"""
Benchmark of every file format that the Redshift bulk loaders can stage to S3 (CSV, JSON, Avro and Parquet),
each with its default number of rows per file.

NOT part of the regular pytest suite (the file name does not match ``test*.py``).
Run from ``packages/bi_etl``::

    uv run python -m tests.performance.bench_redshift_file_writers
    uv run python -m tests.performance.bench_redshift_file_writers --rows 500000 --repeats 5
    uv run python -m tests.performance.bench_redshift_file_writers --writers avro parquet
    uv run python -m tests.performance.bench_redshift_file_writers --upload-mbps 100 --upload-latency 0.1

This builds on :mod:`tests.performance.bench_parquet_rows_per_file`, which has the details of the simulation.
The real loader classes :class:`~bi_etl.bulk_loaders.redshift_s3_csv_loader.RedShiftS3CSVBulk`,
:class:`~bi_etl.bulk_loaders.redshift_s3_json_loader.RedShiftS3JSONBulk`,
:class:`~bi_etl.bulk_loaders.redshift_s3_avro_loader.RedShiftS3AvroBulk` and
:class:`~bi_etl.bulk_loaders.redshift_s3_parquet_loader.RedShiftS3ParquetBulk` write real files, fed through a real
:class:`~bi_etl.bulk_loaders.bulk_worker.BulkWorker` the same way :class:`~bi_etl.components.table.Table` feeds them.
Only the S3 upload and the Redshift ``COPY`` are replaced: a real
:class:`~bi_etl.bulk_loaders.file_uploader.FileUploader` thread uploads each finished file one at a time, and each
upload takes ``file size / --upload-mbps`` plus ``--upload-latency``. The uploads overlap with the writing of the
following files, exactly as they do for the real loaders.

Each loader uses its own default rows per file (``s3_file_max_rows`` is left unset in the config):
CSV and JSON 25,000, Avro 50,000 and Parquet 500,000. The values used are read from the loaders.
The formats differ in file size (CSV and JSON are gzipped text, Avro and Parquet are snappy compressed binary)
as well as in file count, so both the writing time and the upload time differ between them.

The time measured is from the first row being sent to the loader until the last file has arrived in S3.

The rows are generated before the clock starts and are shared by all runs. The table and rows come from
:mod:`tests.performance.bench_data`. They are real :class:`~bi_etl.components.row.row.Row` objects,
so lower ``--rows`` on a small machine.

Example output:

writer   rows/file  files  MB/file  total MB  elapsed s  stdev s  writing s  tail s  rows/s  vs best
-------  ---------  -----  -------  --------  ---------  -------  ---------  ------  ------  -------
csv         25,000     40      1.8      71.3      37.06     2.49      37.00    0.06  26,983  +208.4%
json        25,000     40      2.0      80.5      34.52     0.42      34.46    0.06  28,969  +187.3%
avro        25,000     40      2.2      86.5      15.93     0.41      15.88    0.06  62,763   +32.6%
parquet     25,000     40      2.0      79.1      12.02     0.51      11.96    0.06  83,213    +0.0%

Fastest: parquet (12.02s, 83,213 rows/s)
"""

import argparse
import functools
import gc
import logging
import statistics
import tempfile
import time
from dataclasses import dataclass
from types import SimpleNamespace
from unittest import mock

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.bulk_worker import BulkWorker
from bi_etl.bulk_loaders.file_uploader import FileUploader
from bi_etl.bulk_loaders.redshift_s3_avro_loader import RedShiftS3AvroBulk
from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.redshift_s3_csv_loader import RedShiftS3CSVBulk
from bi_etl.bulk_loaders.redshift_s3_json_loader import RedShiftS3JSONBulk
from bi_etl.bulk_loaders.redshift_s3_parquet_loader import RedShiftS3ParquetBulk
from bi_etl.components.row.row import Row
from tests.performance.bench_data import BenchTable, build_table, make_rows
from tests.performance.bench_parquet_rows_per_file import (
    MB,
    Result,
    SimulatedS3Link,
    print_table,
)

LOADER_CLASSES: dict[str, type[RedShiftS3Base]] = {
    'csv': RedShiftS3CSVBulk,
    'json': RedShiftS3JSONBulk,
    'avro': RedShiftS3AvroBulk,
    'parquet': RedShiftS3ParquetBulk,
}


class SimulatedS3Upload:
    """
    Mixin that replaces the S3 upload and the Redshift ``COPY`` of a
    :class:`~bi_etl.bulk_loaders.redshift_s3_base.RedShiftS3Base` loader with a :class:`SimulatedS3Link`.

    Everything else (the file writing, and the file upload hooks being called as each file is finished) is the real
    loader code. List it before the loader class in the bases, so that it overrides the S3 hooks of
    :class:`~bi_etl.bulk_loaders.s3_bulk_loader_mixin.S3BulkLoaderMixin`.

    Parameters
    ----------
    link
        The simulated S3 connection the files are uploaded over.
    temp_file_path
        Directory the files are written under.
    expected_rows
        Number of rows that :meth:`load_from_files` reports as loaded, in place of the ``COPY`` row count.
        The count of rows written is checked by :func:`run_once` instead.

    Attributes
    ----------
    writing_done_at
        ``time.perf_counter`` value at which the loader finished writing and started to wait for the uploads.
    """

    def __init__(self, link: SimulatedS3Link, temp_file_path: str, expected_rows: int):
        config = SimpleNamespace(
            temp_file_path=temp_file_path,
            user_id=None,
            region_name=None,
            s3_file_max_rows=None,
            analyze_compression=None,
            redshift_copy_iam_role=None,
        )
        super().__init__(config=config)
        self._link = link
        self._expected_rows = expected_rows
        self.writing_done_at: float | None = None

    def _init_s3(self, config) -> None:
        """Use a mock AWS session in place of the real S3 connection."""
        self.session = mock.MagicMock()
        self._file_uploader: FileUploader | None = None

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

    def _handle_load_failure(self) -> None:
        """There is no S3 folder to clean up."""

    def load_from_files(self, local_files: list, table_object, *args, **kwargs) -> int:
        """
        Wait for the queued uploads.

        Parameters
        ----------
        local_files
            Every file that was written.
        table_object
            Not used.

        Returns
        -------
        int
            The ``expected_rows`` given to the constructor.

        Raises
        ------
        AssertionError
            If the files were not all uploaded, in order.
        """
        self.writing_done_at = time.perf_counter()
        uploader, self._file_uploader = self._file_uploader, None
        uploaded = uploader.finish()
        if uploaded != [str(f) for f in local_files]:
            raise AssertionError('Not every file was uploaded, in order')
        return self._expected_rows


def simulated_loader_class(loader_class: type[RedShiftS3Base]) -> type[BulkLoader]:
    """
    Return a subclass of *loader_class* that uses :class:`SimulatedS3Upload`.

    Parameters
    ----------
    loader_class
        One of the :data:`LOADER_CLASSES`.
    """
    return type(f'Simulated{loader_class.__name__}', (SimulatedS3Upload, loader_class), {})


@dataclass
class WriterResult(Result):
    """
    Timings of one run for one file format. All times are in seconds.

    ``chunk_size`` is the default rows per file of the loader.
    """
    writer: str = ''


def run_once(
        writer: str,
        rows: list[Row],
        table: BenchTable,
        temp_dir: str,
        upload_mbps: float = 300.0,
        upload_latency: float = 0.05,
        worker_chunk_size: int = BulkWorker.DEFAULT_CHUNK_SIZE,
) -> WriterResult:
    """
    Load *rows* once with the default rows per file of *writer*, timed from the first row sent to the last file in S3.

    Parameters
    ----------
    writer
        Key of :data:`LOADER_CLASSES`.
    rows
        Rows to load.
    table
        Table the rows belong to, see :func:`~tests.performance.bench_data.build_table`.
    temp_dir
        Directory to write the files under.
    upload_mbps
        Simulated upload speed in MB (10**6 bytes) per second.
    upload_latency
        Simulated fixed time per file upload, in seconds.
    worker_chunk_size
        Rows per hand-off to the loader thread, as in ``Table.bulk_worker_chunk_size``.

    Returns
    -------
    WriterResult

    Raises
    ------
    AssertionError
        If the loader did not write every row.
    """
    link = SimulatedS3Link(upload_mbps, upload_latency)
    loader = simulated_loader_class(LOADER_CLASSES[writer])(link, temp_dir, len(rows))
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
        raise AssertionError(f'{writer} loader wrote {worker.value} rows, sent {len(rows)}')
    return WriterResult(
        writer=writer,
        rows_per_file=loader.rows_per_file,
        rows=len(rows),
        files=link.files,
        total_bytes=link.bytes,
        elapsed=link.busy_until - start,
        writing=loader.writing_done_at - start,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--rows', type=int, default=1_000_000,
        help='Rows to load per run (default 1,000,000)'
    )
    parser.add_argument(
        '--writers', nargs='+', choices=list(LOADER_CLASSES), default=list(LOADER_CLASSES),
        help='File formats to test (default all)',
    )
    parser.add_argument(
        '--repeats', type=int, default=5,
        help='Runs per file format; the median run is reported'
    )
    parser.add_argument(
        '--upload-mbps', type=float, default=300.0,
        help='Simulated S3 upload speed in MB/s (default 300)'
    )
    parser.add_argument(
        '--upload-latency', type=float, default=0.05,
        help='Simulated fixed seconds per file upload (default 0.05). Real S3 PUTs are about 0.02 to 0.1',
    )
    parser.add_argument(
        '--worker-chunk-size', type=int, default=BulkWorker.DEFAULT_CHUNK_SIZE,
        help='Rows per hand-off from the producer to the loader thread',
    )
    parser.add_argument(
        '--column-multiplier', type=int, default=1,
        help='Number of times the columns (other than the key) are repeated, to make the table wider (default 1)',
    )
    args = parser.parse_args()

    logging.disable(logging.CRITICAL)
    table = build_table(column_multiplier=args.column_multiplier)
    print(f'Generating {args.rows:,} rows...')
    rows = make_rows(args.rows, column_multiplier=args.column_multiplier)
    print(
        f'{args.rows:,} rows of {len(table.columns)} columns, {args.repeats} run(s) per file format, '
        f'upload {args.upload_mbps:g} MB/s + {args.upload_latency:g}s per file\n'
    )

    medians = []
    with tempfile.TemporaryDirectory() as tmp:
        for writer in args.writers:
            print(f'Testing {writer} with {args.repeats} repeats...')
            try:
                runs = [
                    run_once(
                        writer, rows, table, tmp,
                        upload_mbps=args.upload_mbps,
                        upload_latency=args.upload_latency,
                        worker_chunk_size=args.worker_chunk_size,
                    )
                    for _ in range(args.repeats)
                ]
            except TypeError as e:
                # bi_etl.utility.json.json_default deliberately has no handling for date values
                if writer != 'json' or 'No handling for' not in str(e):
                    raise
                print(f'  {writer}: SKIPPED, the loader cannot write this data: {e}', flush=True)
                continue
            median = sorted(runs, key=lambda r: r.elapsed)[len(runs) // 2]
            stdev = statistics.stdev([r.elapsed for r in runs]) if len(runs) > 1 else 0.0
            medians.append((median, stdev))
            print(f'  {writer}: {median.elapsed:.2f}s', flush=True)

    best = min(medians, key=lambda m: m[0].elapsed)[0]
    print()
    print_table(
        ['writer', 'rows/file', 'files', 'MB/file', 'total MB', 'elapsed s', 'stdev s', 'writing s', 'tail s',
         'rows/s', 'vs best'],
        [
            [
                r.writer, f'{r.rows_per_file:,}', f'{r.files:,}', f'{r.mb_per_file:.1f}', f'{r.total_bytes / MB:.1f}',
                f'{r.elapsed:.2f}', f'{stdev:.2f}', f'{r.writing:.2f}', f'{r.tail:.2f}',
                f'{r.rows_per_second:,.0f}', f'{r.elapsed / best.elapsed - 1:+.1%}',
            ]
            for r, stdev in medians
        ],
    )
    print(f'\nFastest: {best.writer} ({best.elapsed:.2f}s, {best.rows_per_second:,.0f} rows/s)')


if __name__ == '__main__':
    main()

