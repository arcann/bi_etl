import asyncio
import time
from typing import Callable, Optional

import pytest
import sqlalchemy
from sqlalchemy import Column, Integer, TEXT

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.bulk_worker import BulkWorker, BulkWorkerAborted
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.table import Table
from bi_etl.database import DatabaseMetadata
from bi_etl.scheduler.etl_task import ETLTask
from tests.config_for_tests import build_config

TABLE_NAME = 'bulk_worker_test'


class RecordingBulkLoader(BulkLoader):
    """
    Fake bulk loader that consumes the iterable it is given and records what it saw.

    Parameters
    ----------
    fail_on_row:
        Raise ``error`` when this (0-based) row is received.
    fail_at_end:
        Raise ``error`` after the iterable is exhausted.
    stop_after:
        Return without consuming any further rows after this many rows.
    """

    def __init__(
            self,
            *,
            fail_on_row: Optional[int] = None,
            fail_at_end: bool = False,
            stop_after: Optional[int] = None,
    ):
        super().__init__()
        self.error = KeyError("loader failed")
        self.fail_on_row = fail_on_row
        self.fail_at_end = fail_at_end
        self.stop_after = stop_after
        self.calls = []
        self.received = []
        self.finished = False
        self.aborted = False

    def load_from_iterable(
            self,
            iterable,
            table_object,
            table_to_load=None,
            perform_rename=False,
            progress_frequency=10,
            analyze_compression=None,
            parent_task=None,
    ) -> int:
        self.calls.append({'table_object': table_object, 'progress_frequency': progress_frequency})
        try:
            for row in iterable:
                if self.fail_on_row is not None and len(self.received) == self.fail_on_row:
                    raise self.error
                self.received.append(row['col1'])
                if self.stop_after is not None and len(self.received) >= self.stop_after:
                    return len(self.received)
        except BulkWorkerAborted:
            self.aborted = True
            raise
        if self.fail_at_end:
            raise self.error
        self.finished = True
        return len(self.received)


def _run_sync(fn: Callable):
    return fn()


def _run_in_asyncio(fn: Callable):
    async def main():
        return fn()

    return asyncio.run(main())


@pytest.fixture(params=[_run_sync, _run_in_asyncio], ids=['sync', 'asyncio'])
def run(request) -> Callable[[Callable], object]:
    """Call a function from sync code, or from inside a running asyncio event loop."""
    return request.param


@pytest.fixture(params=[1, 7, BulkWorker.DEFAULT_CHUNK_SIZE], ids=lambda n: f'chunk{n}')
def chunk_size(request) -> int:
    """The Table.bulk_worker_chunk_size to test with (1 = hand over every row, 7 = odd size that never divides evenly)."""
    return request.param


@pytest.fixture
def open_table(tmp_path, chunk_size):
    """Factory returning a bulk-mode Table on a fresh sqlite DB. Tables are closed after the test."""
    engine = sqlalchemy.create_engine(f"sqlite:///{tmp_path / 'bulk_worker.db'}")
    database = DatabaseMetadata(bind=engine, quote_schema=False, database_name=__name__)
    sqlalchemy.schema.Table(
        TABLE_NAME,
        database,
        Column('col1', Integer, primary_key=True),
        Column('col2', TEXT),
    ).create(bind=engine)
    task = ETLTask(config=build_config(tmp=str(tmp_path)))
    tables = []

    def factory(bulk_loader: BulkLoader) -> Table:
        tbl = Table(
            task,
            database,
            table_name=TABLE_NAME,
            bulk_worker_chunk_size=chunk_size,
        )
        tbl.set_bulk_loader(bulk_loader)
        tables.append(tbl)
        return tbl

    yield factory

    for tbl in tables:
        # error=True so close() doesn't try to finish a bulk load that a test left failed
        tbl.close(error=True)
    database.dispose()
    engine.dispose()


def _make_row(tbl: Table, i: int, iteration_header: RowIterationHeader):
    row = tbl.Row(iteration_header=iteration_header)
    row['col1'] = i
    row['col2'] = f'row {i}'
    return row


def _insert_rows(tbl: Table, count: int, start: int = 0):
    header = RowIterationHeader()
    for i in range(start, start + count):
        tbl.insert_row(_make_row(tbl, i, header))


def _insert_until_error(tbl: Table, max_rows: int = 1000):
    """Insert rows until the worker's failure surfaces (the caller expects it to raise)."""
    header = RowIterationHeader()
    for i in range(max_rows):
        tbl.insert_row(_make_row(tbl, i, header))
        # Give a worker that runs concurrently (rather than at insert_row's yield point) time to fail
        time.sleep(0.001)


class TestBulkWorkerLifecycle:
    def test_worker_not_started_until_first_insert(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            assert loader.calls == []
            _insert_rows(tbl, 1)
            tbl.bulk_load_from_cache()

        run(body)
        assert len(loader.calls) == 1

    def test_loader_called_once_with_table_and_no_progress_logging(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 5)
            tbl.bulk_load_from_cache()
            return tbl

        tbl = run(body)
        assert len(loader.calls) == 1
        assert loader.calls[0]['table_object'] is tbl
        assert loader.calls[0]['progress_frequency'] is None

    def test_all_rows_delivered_in_order(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 25)
            tbl.bulk_load_from_cache()

        run(body)
        assert loader.received == list(range(25))
        assert loader.finished

    def test_rows_loaded_stat_is_loader_return_value(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 7)
            tbl.bulk_load_from_cache(stat_name='my_bulk_load')
            return tbl

        tbl = run(body)
        stats = tbl.statistics['my_bulk_load']
        assert stats['rows_loaded'] == 7
        assert stats['max_insert_queue'] >= 0
        assert stats['ending_insert_queue'] == 0

    def test_bulk_load_without_inserts_does_not_call_loader(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            tbl.bulk_load_from_cache(stat_name='nothing')
            return tbl

        tbl = run(body)
        assert loader.calls == []
        assert tbl.statistics['nothing']['rows_loaded'] is None

    def test_new_worker_started_for_next_load_after_completion(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 3)
            tbl.bulk_load_from_cache()
            _insert_rows(tbl, 2, start=100)
            tbl.bulk_load_from_cache()

        run(body)
        assert len(loader.calls) == 2
        assert loader.received == [0, 1, 2, 100, 101]

    def test_close_completes_pending_bulk_load(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 4)
            tbl.close()

        run(body)
        assert loader.received == [0, 1, 2, 3]
        assert loader.finished

    def test_close_with_error_aborts_pending_worker(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 3)
            tbl.close(error=True)

        run(body)
        deadline = time.monotonic() + 5
        while not loader.aborted and time.monotonic() < deadline:
            time.sleep(0.01)
        assert loader.aborted
        assert not loader.finished

    def test_rollback_aborts_pending_worker(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 3)
            tbl.rollback()

        run(body)
        deadline = time.monotonic() + 5
        while not loader.aborted and time.monotonic() < deadline:
            time.sleep(0.01)
        assert loader.aborted
        assert not loader.finished

class TestBulkWorkerFailure:
    def test_failure_surfaces_on_later_insert_before_end_of_load(self, run, open_table):
        loader = RecordingBulkLoader(fail_on_row=0)

        def body():
            tbl = open_table(loader)
            with pytest.raises(KeyError, match="loader failed"):
                _insert_until_error(tbl)

        run(body)
        assert not loader.finished

    def test_failure_after_some_rows_surfaces_on_later_insert(self, run, open_table):
        loader = RecordingBulkLoader(fail_on_row=3)

        def body():
            tbl = open_table(loader)
            with pytest.raises(KeyError, match="loader failed"):
                _insert_until_error(tbl)

        run(body)
        assert loader.received == [0, 1, 2]

    def test_loader_returning_early_raises_runtime_error(self, run, open_table):
        loader = RecordingBulkLoader(stop_after=2)

        def body():
            tbl = open_table(loader)
            with pytest.raises(RuntimeError, match="stopped before all rows were provided"):
                _insert_until_error(tbl)

        run(body)
        assert loader.received == [0, 1]

    def test_failure_when_input_ends_is_raised_by_bulk_load(self, run, open_table):
        loader = RecordingBulkLoader(fail_at_end=True)

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 3)
            with pytest.raises(KeyError, match="loader failed"):
                tbl.bulk_load_from_cache()

        run(body)
        assert loader.received == [0, 1, 2]

    def test_upsert_mode_rejected_once_insert_row_started_worker(self, run, open_table):
        loader = RecordingBulkLoader()

        def body():
            tbl = open_table(loader)
            _insert_rows(tbl, 1)
            with pytest.raises(ValueError, match="Upsert called on a table that is using insert_row"):
                tbl._set_upsert_mode()

        run(body)