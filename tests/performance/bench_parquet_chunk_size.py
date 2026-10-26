"""
Benchmark to find the best Parquet bulk loader ``chunk_size`` (rows per Parquet file).

NOT part of the regular pytest suite (the file name does not match ``test*.py``).
Run from ``packages/bi_etl``::

    uv run python -m tests.performance.bench_parquet_chunk_size
    uv run python -m tests.performance.bench_parquet_chunk_size --rows 2000000 --repeats 5
    uv run python -m tests.performance.bench_parquet_chunk_size --chunk-sizes 25000 100000 500000
    uv run python -m tests.performance.bench_parquet_chunk_size --upload-latency 0.05

The table has one integer column and nine string columns of 3 to 15 random characters each.
The real :class:`~bi_etl.bulk_loaders.parquet_bulk_loader_mixin.ParquetBulkLoaderMixin` writes real
snappy compressed Parquet files, fed through a real :class:`~bi_etl.bulk_loaders.bulk_worker.BulkWorker`
the same way :class:`~bi_etl.components.table.Table` feeds it. Only the S3 upload is simulated: a real
:class:`~bi_etl.bulk_loaders.file_uploader.FileUploader` thread uploads each finished file one at a time,
and each upload takes ``file size / --upload-mbps`` (plus ``--upload-latency``). The uploads overlap with the
writing of the following files, exactly as they do for the real loader.

The time measured is from the first row being sent to the loader until the last file has arrived in S3.
Because uploads are overlapped with writing, that time is

    time to write all files + time to upload the last file (the "tail") + any upload backlog.

Smaller files shrink the tail but add per-file overhead (open / close / footer, smaller row groups).
Larger files do the opposite. This benchmark finds where those cross over for the writer on this machine.

The rows are generated before the clock starts and are shared by all runs.
They are plain dicts rather than :class:`~bi_etl.components.row.row.Row` objects to keep memory use down
(about 1 KB per row), so lower ``--rows`` on a small machine.
"""
import argparse
import functools
import gc
import logging
import os
import random
import statistics
import string
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq
from sqlalchemy import Integer, String
from sqlalchemy.types import TypeEngine

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.bulk_worker import BulkWorker
from bi_etl.bulk_loaders.file_uploader import FileUploader
from bi_etl.bulk_loaders.parquet_bulk_loader_mixin import ParquetBulkLoaderMixin

STRING_COLUMN_COUNT = 9
MIN_STRING_LENGTH = 3
MAX_STRING_LENGTH = 15
MB = 1_000_000


@dataclass
class BenchColumn:
    """The parts of a column that :func:`~bi_etl.components.parquet_writer.build_parquet_schema` reads."""
    name: str
    type: TypeEngine


@dataclass
class BenchTable:
    """The parts of a table that :class:`SimulatedS3ParquetLoader` reads."""
    qualified_table_name: str
    columns: list[BenchColumn]


def build_table() -> BenchTable:
    """Return a table-like object with one integer column followed by nine string columns."""
    columns = [BenchColumn('id', Integer())]
    columns.extend(BenchColumn(f'str_{i}', String()) for i in range(1, STRING_COLUMN_COUNT + 1))
    return BenchTable('bench_schema.parquet_chunk_size', columns)


def make_rows(count: int, seed: int = 1234) -> list[dict]:
    """
    Generate rows for :func:`build_table`.

    Parameters
    ----------
    count
        Number of rows.
    seed
        Seed for the random generator, so that every run sees the same data.

    Returns
    -------
    list of dict
        Each row has an ``id`` and ``str_1`` to ``str_9``. The strings are random ASCII letters and digits
        with a random length of 3 to 15 characters.
    """
    rng = random.Random(seed)
    alphabet = string.ascii_letters + string.digits
    string_columns = [f'str_{i}' for i in range(1, STRING_COLUMN_COUNT + 1)]
    rows = []
    for i in range(count):
        row = {'id': i}
        for column in string_columns:
            row[column] = ''.join(rng.choices(alphabet, k=rng.randint(MIN_STRING_LENGTH, MAX_STRING_LENGTH)))
        rows.append(row)
    return rows


class SimulatedS3Link:
    """
    A single S3 connection of fixed speed. :meth:`upload` blocks for as long as the real upload would take.

    Only called from the one :class:`~bi_etl.bulk_loaders.file_uploader.FileUploader` thread, so it needs no lock.

    Parameters
    ----------
    megabytes_per_second
        Upload speed.
    latency_seconds
        Fixed time added to every file (request set-up and S3 commit time).

    Attributes
    ----------
    busy_until
        ``time.perf_counter`` value at which the most recently started upload completes.
        This is the arrival time of the last file once the uploads are finished. It is tracked as a deadline
        instead of being read after the sleep, so that sleep overshoot does not accumulate.
    """

    def __init__(self, megabytes_per_second: float, latency_seconds: float = 0.0):
        self._bytes_per_second = megabytes_per_second * MB
        self._latency_seconds = latency_seconds
        self.busy_until = 0.0
        self.files = 0
        self.bytes = 0

    def upload(self, local_file: str) -> None:
        """
        Simulate uploading *local_file*, returning when it would have arrived in S3.

        Parameters
        ----------
        local_file
            Path of a finished file. Only its size is used.
        """
        size = os.path.getsize(local_file)
        start = max(time.perf_counter(), self.busy_until)
        self.busy_until = start + self._latency_seconds + size / self._bytes_per_second
        remaining = self.busy_until - time.perf_counter()
        if remaining > 0:
            time.sleep(remaining)
        self.files += 1
        self.bytes += size


class SimulatedS3ParquetLoader(ParquetBulkLoaderMixin, BulkLoader):
    """
    The real Parquet file writing of :class:`~bi_etl.bulk_loaders.parquet_bulk_loader_mixin.ParquetBulkLoaderMixin`
    with the S3 upload (and the database ``COPY``) replaced by a :class:`SimulatedS3Link`.

    Parameters
    ----------
    chunk_size
        Rows per Parquet file.
    link
        The simulated S3 connection the files are uploaded over.
    temp_file_path
        Directory the Parquet files are written under.
    """

    def __init__(self, chunk_size: int, link: SimulatedS3Link, temp_file_path: str):
        super().__init__()

        class MockConfig:
            pass

        self.config = MockConfig()
        self.config.temp_file_path = temp_file_path
        self._init_parquet(chunk_size=chunk_size)
        self._link = link
        self._file_uploader: FileUploader | None = None
        self.writing_done_at: float | None = None

    def _begin_file_uploads(self, table_object) -> None:
        """Start the upload thread."""
        self._abort_file_uploads()
        self._file_uploader = FileUploader(self._link.upload, name='bench upload')

    def _queue_file_for_upload(self, local_file) -> None:
        """Queue a finished file for the upload thread."""
        if self._file_uploader is not None:
            self._file_uploader.submit(local_file)

    def _abort_file_uploads(self) -> None:
        """Stop the upload thread if it is still running."""
        uploader = self._file_uploader
        self._file_uploader = None
        if uploader is not None:
            uploader.abort()

    def load_from_files(self, local_files: list, table_object, *args, **kwargs) -> int:
        """
        Wait for the queued uploads and return the number of rows in the files.

        Parameters
        ----------
        local_files
            Every file that was written.
        table_object
            Not used.

        Returns
        -------
        int
            Total number of rows in *local_files*.
        """
        self.writing_done_at = time.perf_counter()
        uploader, self._file_uploader = self._file_uploader, None
        uploaded = uploader.finish()
        if uploaded != [str(f) for f in local_files]:
            raise AssertionError('Not every file was uploaded, in order')
        return sum(pq.ParquetFile(f).metadata.num_rows for f in local_files)


@dataclass
class Result:
    """Timings of one run for one ``chunk_size``. All times are in seconds."""
    chunk_size: int
    rows: int
    files: int
    total_bytes: int
    elapsed: float
    writing: float

    @property
    def tail(self) -> float:
        """Time from the last file being written until it arrived in S3."""
        return self.elapsed - self.writing

    @property
    def mb_per_file(self) -> float:
        """Average file size in MB."""
        return self.total_bytes / self.files / MB

    @property
    def rows_per_second(self) -> float:
        """Rows per second from first row sent to last file in S3."""
        return self.rows / self.elapsed


def run_once(
        rows: list[dict],
        table: BenchTable,
        chunk_size: int,
        temp_dir: str,
        upload_mbps: float = 300.0,
        upload_latency: float = 0.0,
        worker_chunk_size: int = BulkWorker.DEFAULT_CHUNK_SIZE,
) -> Result:
    """
    Load *rows* once with the given ``chunk_size`` and time it from the first row sent to the last file in S3.

    Parameters
    ----------
    rows
        Rows to load.
    table
        Table the rows belong to, see :func:`build_table`.
    chunk_size
        Rows per Parquet file.
    temp_dir
        Directory to write the Parquet files under.
    upload_mbps
        Simulated upload speed in MB (10**6 bytes) per second.
    upload_latency
        Simulated fixed time per file upload, in seconds.
    worker_chunk_size
        Rows per hand-off to the loader thread, as in ``Table.bulk_worker_chunk_size``.

    Returns
    -------
    Result

    Raises
    ------
    AssertionError
        If the loader did not write every row.
    """
    print(f"Starting run with chunk size {chunk_size}")
    link = SimulatedS3Link(upload_mbps, upload_latency)
    loader = SimulatedS3ParquetLoader(chunk_size, link, temp_dir)
    worker = BulkWorker(
        functools.partial(loader.load_from_iterable, table_object=table),
        chunk_size=worker_chunk_size,
    )
    gc.collect()
    worker.start()
    start = time.perf_counter()
    for row in rows:
        worker.put(row)
    worker.close_input()
    worker.join()
    if worker.exception is not None:
        raise worker.exception
    if worker.value != len(rows):
        raise AssertionError(f'loader wrote {worker.value} rows, sent {len(rows)}')
    return Result(
        chunk_size=chunk_size,
        rows=len(rows),
        files=link.files,
        total_bytes=link.bytes,
        elapsed=link.busy_until - start,
        writing=loader.writing_done_at - start,
    )


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print *rows* as a table with right aligned columns, except the first."""
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print('  '.join(h.ljust(widths[i]) if i == 0 else h.rjust(widths[i]) for i, h in enumerate(headers)))
    print('  '.join('-' * w for w in widths))
    for r in rows:
        print('  '.join(c.ljust(widths[i]) if i == 0 else c.rjust(widths[i]) for i, c in enumerate(r)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--rows', type=int, default=1_000_000,
        help='Rows to load per run (default 1,000,000)'
    )
    parser.add_argument(
        '--chunk-sizes', nargs='+', type=int,
        default=[10_000, 25_000, 50_000, 100_000, 250_000, 500_000],
        help='Rows per Parquet file to try (default 10k to 500k)',
    )
    parser.add_argument(
        '--repeats', type=int, default=3,
        help='Runs per chunk size; the median run is reported'
    )
    parser.add_argument(
        '--upload-mbps', type=float, default=300.0,
        help='Simulated S3 upload speed in MB/s'
        )
    parser.add_argument(
        '--upload-latency', type=float, default=0.05,
        help='Simulated fixed seconds per file upload (default 0, the speed alone). Real S3 PUTs are about 0.02 to 0.1',
    )
    parser.add_argument(
        '--worker-chunk-size', type=int, default=BulkWorker.DEFAULT_CHUNK_SIZE,
        help='Rows per hand-off from the producer to the loader thread',
    )
    args = parser.parse_args()

    logging.disable(logging.CRITICAL)
    print(f'Generating {args.rows:,} rows...')
    rows = make_rows(args.rows)
    table = build_table()
    print(
        f'{args.rows:,} rows, {args.repeats} run(s) per chunk size, '
        f'upload {args.upload_mbps:g} MB/s + {args.upload_latency:g}s per file\n'
    )

    medians = []
    with tempfile.TemporaryDirectory() as tmp:
        for chunk_size in args.chunk_sizes:
            print(f"Testing chunk size {chunk_size:>9,} with {args.repeats} repeats...")
            runs = [
                run_once(
                    rows, table, chunk_size, tmp,
                    upload_mbps=args.upload_mbps,
                    upload_latency=args.upload_latency,
                    worker_chunk_size=args.worker_chunk_size,
                )
                for _ in range(args.repeats)
            ]
            median = sorted(runs, key=lambda r: r.elapsed)[len(runs) // 2]
            stdev = statistics.stdev([r.elapsed for r in runs]) if len(runs) > 1 else 0.0
            medians.append((median, stdev))
            print(f'  chunk_size {chunk_size:>9,}: {median.elapsed:.2f}s', flush=True)

    best = min(medians, key=lambda m: m[0].elapsed)[0]
    print()
    print_table(
        ['chunk_size', 'files', 'MB/file', 'total MB', 'elapsed s', 'stdev s', 'writing s', 'tail s', 'rows/s',
         'vs best'],
        [
            [
                f'{r.chunk_size:,}', f'{r.files:,}', f'{r.mb_per_file:.1f}', f'{r.total_bytes / MB:.1f}',
                f'{r.elapsed:.2f}', f'{stdev:.2f}', f'{r.writing:.2f}', f'{r.tail:.2f}',
                f'{r.rows_per_second:,.0f}', f'{r.elapsed / best.elapsed - 1:+.1%}',
            ]
            for r, stdev in medians
        ],
    )
    print(f'\nBest chunk_size: {best.chunk_size:,} rows ({best.mb_per_file:.1f} MB per file, {best.elapsed:.2f}s)')


if __name__ == '__main__':
    main()
