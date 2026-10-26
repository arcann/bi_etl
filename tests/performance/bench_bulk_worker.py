"""
Overhead benchmark for the :class:`bi_etl.components.table.Table` ``insert_row`` bulk worker.

NOT part of the regular pytest suite (the file name does not match ``test*.py``).
Run from ``packages/bi_etl``::

    uv run python -m tests.performance.bench_bulk_worker
    uv run python -m tests.performance.bench_bulk_worker --duration 10
    uv run python -m tests.performance.bench_bulk_worker --repeats 3
    uv run python -m tests.performance.bench_bulk_worker --chunk-sizes 1 16 128 512

A real ``Table`` (on a throw-away sqlite file) is fed rows through ``insert_row`` for
``--duration`` seconds. The bulk loader is a mock that counts rows and discards them, so the measured
time is Table + worker overhead only. Three things are reported:

* ``insert_row`` time per row while producing, compared to the cost of just creating the row (``baseline``).
* The time ``bulk_load_from_cache`` then needs to drain the queue and stop the worker.
* The raw worker hand-off cost, without Table (``worker only``), to separate worker overhead from Table overhead.

Keep in mind that the queue is unbounded: if the worker consumes more slowly than ``insert_row`` produces,
the ``max queue`` column grows (and so does memory use).
"""
import argparse
import gc
import logging
import os
import statistics
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import sqlalchemy
from sqlalchemy import Column, Integer, TEXT

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.bulk_worker import BulkWorker
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.table import Table
from bi_etl.database import DatabaseMetadata
from bi_etl.scheduler.etl_task import ETLTask
from tests.config_for_tests import build_config

TABLE_NAME = 'bulk_worker_perf'
CLOCK_CHECK_INTERVAL = 256


class AvroWriteOnlyBulkLoader(AvroBulkLoaderMixin, BulkLoader):
    """Mock bulk loader that consumes the rows it is given and throws them away."""

    def __init__(self):
        super().__init__()

        @dataclass
        class MockConfig:
            temp_file_path = None

        self.config = MockConfig()
        self._init_avro(chunk_size=50000)
        self._avro_file_count = 0
        self._avro_total_bytes = 0

    @property
    def avro_file_count(self) -> int:
        """Number of Avro files written so far."""
        return self._avro_file_count

    @property
    def avro_total_bytes(self) -> int:
        """Total size in bytes of the Avro files written so far."""
        return self._avro_total_bytes

    def load_from_files(
            self,
            local_files: list,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str | None = None,
    ) -> int:
        # The files are in a temp directory that is removed once the load returns, so measure them here
        self._avro_file_count += len(local_files)
        self._avro_total_bytes += sum(os.path.getsize(file_path) for file_path in local_files)
        # Skip loading to any DB
        return self.rows_seen



@dataclass
class Result:
    chunk_size: int
    rows: int
    produce_seconds: float
    drain_seconds: float
    max_queue: int
    avro_files: int
    avro_bytes: int
    baseline_us_per_row: float

    @property
    def us_per_row(self) -> float:
        return self.produce_seconds / self.rows * 1e6

    @property
    def overhead_us_per_row(self) -> float:
        return self.us_per_row - self.baseline_us_per_row

    @property
    def end_to_end_rows_per_second(self) -> float:
        return self.rows / (self.produce_seconds + self.drain_seconds)


def _make_row(tbl: Table, i: int, iteration_header: RowIterationHeader):
    row = tbl.Row(iteration_header=iteration_header)
    row['col1'] = i
    row['col2'] = 'some text value'
    return row


class TableFixture:
    """A real Table on a fresh sqlite file, configured with the mock loader."""

    def __init__(self, tmp_dir: Path, chunk_size: int = BulkWorker.DEFAULT_CHUNK_SIZE):
        self.engine = sqlalchemy.create_engine(f"sqlite:///{tmp_dir / 'perf.db'}")
        self.database = DatabaseMetadata(bind=self.engine, quote_schema=False, database_name=__name__)
        inventory = self.database.table_inventory()
        if TABLE_NAME not in inventory:
            sqlalchemy.schema.Table(
                TABLE_NAME,
                self.database,
                Column('col1', Integer, primary_key=True),
                Column('col2', TEXT),
            ).create(bind=self.engine)
        task = ETLTask(config=build_config(tmp=str(tmp_dir)))
        self.loader = AvroWriteOnlyBulkLoader()
        self.table = Table(
            task,
            self.database,
            table_name=TABLE_NAME,
            bulk_worker_chunk_size=chunk_size,
        )
        self.table.set_bulk_loader(self.loader)

    def dispose(self):
        self.table.close(error=True)
        self.database.dispose()
        self.engine.dispose()


def measure_baseline(tmp_dir: Path, duration: float) -> float:
    """Microseconds per row to build a Row without inserting it (the floor for the worker)."""
    fixture = TableFixture(tmp_dir)
    try:
        header = RowIterationHeader()
        tbl = fixture.table
        count = 0
        start = time.perf_counter()
        deadline = start + duration
        while True:
            for _ in range(CLOCK_CHECK_INTERVAL):
                _make_row(tbl, count, header)
                count += 1
            now = time.perf_counter()
            if now >= deadline:
                break
        return (now - start) / count * 1e6
    finally:
        fixture.dispose()


def measure_table(tmp_dir: Path, chunk_size: int, duration: float, baseline_us: float) -> Result:
    fixture = TableFixture(tmp_dir, chunk_size)
    try:
        tbl = fixture.table
        header = RowIterationHeader()
        gc.collect()
        count = 0
        start = time.perf_counter()
        deadline = start + duration
        while True:
            for _ in range(CLOCK_CHECK_INTERVAL):
                tbl.insert_row(_make_row(tbl, count, header))
                count += 1
            produce_end = time.perf_counter()
            if produce_end >= deadline:
                break
        tbl.bulk_load_from_cache(stat_name='perf_load')
        drain_end = time.perf_counter()
        if fixture.loader.rows_seen != count:
            raise AssertionError(f'loader saw {fixture.loader.rows_seen} rows, sent {count}')
        return Result(
            chunk_size=chunk_size,
            rows=count,
            produce_seconds=produce_end - start,
            drain_seconds=drain_end - produce_end,
            max_queue=tbl.statistics['perf_load']['max_insert_queue'],
            avro_files=fixture.loader.avro_file_count,
            avro_bytes=fixture.loader.avro_total_bytes,
            baseline_us_per_row=baseline_us,
        )
    finally:
        fixture.dispose()


def measure_worker_only(chunk_size: int, duration: float) -> tuple[int, float, float]:
    """Raw hand-off cost of the worker with trivial items. Returns (items, produce seconds, drain seconds)."""

    def consume(rows: Iterable) -> int:
        count = 0
        for _ in rows:
            count += 1
        return count

    worker = BulkWorker(consume, chunk_size=chunk_size)
    worker.start()
    gc.collect()
    count = 0
    item = object()
    start = time.perf_counter()
    deadline = start + duration
    while True:
        for _ in range(CLOCK_CHECK_INTERVAL):
            worker.put(item)
            count += 1
        produce_end = time.perf_counter()
        if produce_end >= deadline:
            break
    worker.close_input()
    worker.join()
    drain_end = time.perf_counter()
    if worker.value != count:
        raise AssertionError(f'worker saw {worker.value} items, sent {count}')
    return count, produce_end - start, drain_end - produce_end


def _median_result(results: list[Result]) -> Result:
    return sorted(results, key=lambda r: r.us_per_row)[len(results) // 2]


def _stdev(values: list[float]) -> float:
    """Sample standard deviation, or 0 when there are too few values to have one."""
    return statistics.stdev(values) if len(values) > 1 else 0.0


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print('  '.join(h.ljust(widths[i]) if i == 0 else h.rjust(widths[i]) for i, h in enumerate(headers)))
    print('  '.join('-' * w for w in widths))
    for r in rows:
        print('  '.join(c.ljust(widths[i]) if i == 0 else c.rjust(widths[i]) for i, c in enumerate(r)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--duration', type=float, default=5.0,
        help='Seconds to feed rows per measurement (default 5)'
    )
    parser.add_argument(
        '--chunk-sizes', nargs='+', type=int,
        default=sorted([1, 128, 256]),
        help='Rows per hand-off to the worker thread (default: 1, the per-row hand-off, and the default chunk size)',
    )
    parser.add_argument(
        '--repeats', type=int, default=3,
        help='Runs per measurement; the median run is reported'
    )
    parser.add_argument(
        '--skip-worker-only', action='store_true',
        help='Skip the Table-less worker measurement'
    )
    args = parser.parse_args()

    logging.disable(logging.CRITICAL)
    print(f'Measuring {args.duration:g}s per run, {args.repeats} run(s) per measurement\n')

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        baseline_us = statistics.median(
            measure_baseline(tmp_dir, min(args.duration, 2.0)) for _ in range(max(args.repeats, 1))
        )
        print(f'Baseline (create Row only, no insert): {baseline_us:.2f} us/row\n')

        table_rows = []
        for chunk_size in args.chunk_sizes:
            runs = [
                measure_table(tmp_dir, chunk_size, args.duration, baseline_us)
                for _ in range(args.repeats)
            ]
            r = _median_result(runs)
            table_rows.append(
                [
                    str(chunk_size), f'{r.rows:,}', f'{r.us_per_row:.2f}',
                    f'{_stdev([run.us_per_row for run in runs]):.2f}',
                    f'{r.overhead_us_per_row:+.2f}', f'{r.drain_seconds * 1000:.1f}', f'{r.max_queue:,}',
                    f'{r.avro_files:,}', f'{r.avro_bytes / 1024 ** 1:,.0f}',
                    f'{r.end_to_end_rows_per_second:,.0f}',
                ]
            )
        print('Table.insert_row with mock bulk loader')
        print_table(
            [
                'chunk', 'rows', 'us/row', 'stdev us', 'overhead us', 'drain ms', 'max queue',
                'avro files', 'avro KiB', 'rows/s end-to-end',
            ],
            table_rows,
        )

        if not args.skip_worker_only:
            worker_rows = []
            for chunk_size in args.chunk_sizes:
                runs = [measure_worker_only(chunk_size, args.duration) for _ in range(args.repeats)]
                items, produce, drain = sorted(runs, key=lambda x: x[1] / x[0])[len(runs) // 2]
                worker_rows.append(
                    [
                        str(chunk_size), f'{items:,}', f'{produce / items * 1e6:.3f}',
                        f'{_stdev([run[1] / run[0] * 1e6 for run in runs]):.3f}',
                        f'{drain * 1000:.1f}', f'{items / (produce + drain):,.0f}',
                    ]
                )
            print('\nWorker only (put() of a trivial item, no Table)')
            print_table(
                ['chunk', 'items', 'us/put', 'stdev us', 'drain ms', 'items/s end-to-end'],
                worker_rows,
            )


if __name__ == '__main__':
    main()
