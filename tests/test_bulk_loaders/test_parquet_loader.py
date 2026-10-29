"""
Tests for the Parquet bulk loader mixin and the Redshift and Databricks Parquet loaders:
schema generation, file writing, value handling and S3 upload.
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pyarrow.parquet as pq
import pytest
from sqlalchemy import DateTime, Integer, Interval, JSON, LargeBinary, Time

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.databricks_s3_parquet_loader import DatabricksS3ParquetBulkLoader
from bi_etl.bulk_loaders.parquet_bulk_loader_mixin import ParquetBulkLoaderMixin
from bi_etl.bulk_loaders.redshift_s3_parquet_loader import RedShiftS3ParquetBulk
from tests.test_bulk_loaders.bulk_loader_test_helpers import (
    AVRO_ROWS, CHUNK_SIZE, ROW_COUNT, SA_COLUMNS, FakeTable, KwTable, ParquetLoaderForTests, patch_copy,
    s3_config, upload_threads_alive,
)


class StubParquetLoader(ParquetBulkLoaderMixin, BulkLoader):
    def __init__(self):
        super().__init__()
        self.config = SimpleNamespace(temp_file_path=None)
        self._init_parquet(chunk_size=10)
        self.loaded_table = None
        self.file_names: list[str] = []
        self.rows_per_file: list[int] = []
        self.loaded_ids: list[int] = []

    def load_from_files(self, local_files, table_object, **kwargs) -> int:
        self.file_names = [os.path.basename(local_file) for local_file in local_files]
        tables = [pq.read_table(local_file) for local_file in local_files]
        self.rows_per_file = [table.num_rows for table in tables]
        self.loaded_table = tables[0]
        self.loaded_ids = [i for table in tables for i in table.column('id').to_pylist()]
        return sum(self.rows_per_file)


@pytest.fixture
def parquet_loader():
    return ParquetLoaderForTests(chunk_size=10)


class TestParquetSchemaGeneration:
    """Verify _get_parquet_schema maps SQLAlchemy column types to the expected Arrow types."""

    def test_field_names_match_columns(self, mock_table):
        schema = ParquetBulkLoaderMixin._get_parquet_schema(mock_table)

        assert schema.names == [c.name for c in SA_COLUMNS]

    def test_all_fields_are_nullable(self, mock_table):
        schema = ParquetBulkLoaderMixin._get_parquet_schema(mock_table)

        assert all(field.nullable for field in schema)

    @pytest.mark.parametrize(
        'column_name, expected_type',
        [
            ('id', 'int64'),
            ('name', 'string'),
            ('score', 'double'),
            ('active', 'bool'),
            ('birthday', 'date32[day]'),
            ('created_at', 'timestamp[us]'),
            ('amount', 'decimal128(10, 2)'),
        ],
    )
    def test_column_type(self, mock_table, column_name, expected_type):
        schema = ParquetBulkLoaderMixin._get_parquet_schema(mock_table)

        assert str(schema.field(column_name).type) == expected_type

    @pytest.mark.parametrize(
        'sa_type, expected_type',
        [
            (Time(), 'time64[us]'),
            (LargeBinary(), 'large_binary'),
            (Interval(), 'month_day_nano_interval'),
            (JSON(), 'string'),
        ],
    )
    def test_other_python_types(self, sa_type, expected_type):
        table = KwTable('tbl', value=sa_type)

        schema = ParquetBulkLoaderMixin._get_parquet_schema(table)

        assert str(schema.field('value').type) == expected_type


class TestParquetWriteAndRead:
    """Verify a finished chunk is a file that pyarrow reads back with the same values."""

    @staticmethod
    def _write(loader, table, directory, rows, file_number=1):
        files = []
        writer = loader._start_parquet_file(
            temp_dir=str(directory),
            file_number=file_number,
            schema=ParquetBulkLoaderMixin._get_parquet_schema(table),
            local_files_list=files,
        )
        for row in rows:
            writer.insert_row(row)
        loader._finish_parquet_file(writer, file_number)
        return files

    def test_chunk_produces_readable_parquet_file(self, parquet_loader, mock_table, tmp_path):
        files = self._write(parquet_loader, mock_table, tmp_path, AVRO_ROWS)

        assert [os.path.basename(f) for f in files] == ['data_1.parquet.snappy']
        assert pq.read_table(files[0]).num_rows == len(AVRO_ROWS)

    def test_values_survive_round_trip(self, parquet_loader, mock_table, tmp_path):
        files = self._write(parquet_loader, mock_table, tmp_path, AVRO_ROWS)

        assert pq.read_table(files[0]).to_pylist() == AVRO_ROWS

    def test_null_values_are_preserved(self, parquet_loader, mock_table, tmp_path):
        files = self._write(parquet_loader, mock_table, tmp_path, AVRO_ROWS)

        last_row = pq.read_table(files[0]).to_pylist()[-1]
        assert last_row['id'] is None
        assert last_row['score'] is None
        assert last_row['amount'] is None
        assert last_row['name'] == 'Carol'

    def test_file_is_snappy_compressed(self, parquet_loader, mock_table, tmp_path):
        files = self._write(parquet_loader, mock_table, tmp_path, AVRO_ROWS)

        assert pq.ParquetFile(files[0]).metadata.row_group(0).column(0).compression == 'SNAPPY'

    def test_file_number_is_used_in_the_file_name(self, parquet_loader, mock_table, tmp_path):
        first = self._write(parquet_loader, mock_table, tmp_path, AVRO_ROWS, file_number=1)
        second = self._write(parquet_loader, mock_table, tmp_path, AVRO_ROWS, file_number=2)

        assert first != second
        assert os.path.basename(second[0]) == 'data_2.parquet.snappy'

    def test_finished_file_is_queued_for_upload(self, parquet_loader, mock_table, tmp_path, monkeypatch):
        queued = []
        monkeypatch.setattr(parquet_loader, '_queue_file_for_upload', queued.append)

        files = self._write(parquet_loader, mock_table, tmp_path, AVRO_ROWS)

        assert queued == files


class TestParquetLoadFromIterable:
    """Verify load_from_iterable splits the rows into files of chunk_size rows and loads them."""

    @staticmethod
    def _rows(count):
        return ({'id': i, 'name': f'name {i}'} for i in range(count))

    def test_rows_are_split_into_files_of_chunk_size_rows(self):
        loader = StubParquetLoader()

        assert loader.load_from_iterable(self._rows(ROW_COUNT), FakeTable()) == ROW_COUNT

        assert loader.rows_per_file == [CHUNK_SIZE, CHUNK_SIZE, ROW_COUNT - 2 * CHUNK_SIZE]
        assert loader.file_names == ['data_1.parquet.snappy', 'data_2.parquet.snappy', 'data_3.parquet.snappy']

    def test_exact_multiple_of_chunk_size_does_not_write_an_empty_file(self):
        loader = StubParquetLoader()

        assert loader.load_from_iterable(self._rows(2 * CHUNK_SIZE), FakeTable()) == 2 * CHUNK_SIZE

        assert loader.rows_per_file == [CHUNK_SIZE, CHUNK_SIZE]

    def test_fewer_rows_than_chunk_size_write_one_file(self):
        loader = StubParquetLoader()

        assert loader.load_from_iterable(self._rows(3), FakeTable()) == 3

        assert loader.rows_per_file == [3]

    def test_empty_iterable_loads_nothing(self):
        loader = StubParquetLoader()

        assert loader.load_from_iterable(iter([]), FakeTable()) == 0

        assert loader.loaded_table is None
        assert loader.file_names == []

    def test_all_rows_are_loaded_in_order(self):
        loader = StubParquetLoader()

        loader.load_from_iterable(self._rows(ROW_COUNT), FakeTable())

        assert loader.loaded_ids == list(range(ROW_COUNT))

    def test_default_chunk_size(self):
        assert ParquetLoaderForTests().chunk_size == 500_000



class TestParquetDatetime:
    def test_time_of_day_is_kept(self):
        loader = StubParquetLoader()
        table = KwTable('tbl', id=Integer(), created=DateTime())
        created = datetime(2020, 1, 2, 3, 4, 5, 678901)

        assert loader.load_from_iterable([{'id': 1, 'created': created}], table) == 1

        assert loader.loaded_table.column('created').to_pylist() == [created]

    def test_none_datetime_is_null(self):
        loader = StubParquetLoader()
        table = KwTable('tbl', id=Integer(), created=DateTime())

        loader.load_from_iterable([{'id': 1, 'created': None}], table)

        assert loader.loaded_table.column('created').to_pylist() == [None]

    def test_timezone_aware_column_keeps_the_instant(self):
        loader = StubParquetLoader()
        table = KwTable('tbl', id=Integer(), created=DateTime(timezone=True))
        created = datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=-5)))

        loader.load_from_iterable([{'id': 1, 'created': created}], table)

        column = loader.loaded_table.column('created')
        assert str(column.type) == 'timestamp[us, tz=UTC]'
        assert column.to_pylist() == [created]

    @pytest.mark.parametrize('with_timezone', [False, True])
    def test_schema_type(self, with_timezone):
        table = KwTable('tbl', created=DateTime(timezone=with_timezone))

        schema = ParquetBulkLoaderMixin._get_parquet_schema(table)

        expected = 'timestamp[us, tz=UTC]' if with_timezone else 'timestamp[us]'
        assert str(schema.field('created').type) == expected


class TestRedshiftParquetUpload:
    def test_files_uploaded_before_copy(self, bucket, monkeypatch):
        loader = RedShiftS3ParquetBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        loaded = loader.load_from_iterable(
            ({'id': i, 'name': f'name {i}'} for i in range(ROW_COUNT)),
            FakeTable(),
        )

        assert loaded == ROW_COUNT
        assert bucket.uploaded_names == [
            'data_1.parquet.snappy',
            'data_2.parquet.snappy',
            'data_3.parquet.snappy',
        ]
        assert all(upload.thread is not threading.current_thread() for upload in bucket.uploads)
        assert len(copies) == 1
        assert not upload_threads_alive()

    def test_default_max_rows(self):
        assert RedShiftS3ParquetBulk(s3_config()).s3_file_max_rows == 500_000

    def test_empty_iterable(self, bucket, monkeypatch):
        loader = RedShiftS3ParquetBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        assert loader.load_from_iterable(iter([]), FakeTable()) == 0
        assert not copies
        assert bucket.uploads == []


class TestDatabricksParquetUpload:
    @staticmethod
    def _table_with_cursor():
        table = FakeTable()
        table.database = MagicMock()
        cursor = table.database.bind.raw_connection.return_value.cursor.return_value
        cursor.fetchall.return_value = [(None, ROW_COUNT)]
        return table, cursor

    def test_parquet_files_uploaded_before_insert(self, bucket):
        loader = DatabricksS3ParquetBulkLoader(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        table, cursor = self._table_with_cursor()
        uploads_when_sql_ran = []
        cursor.execute.side_effect = lambda sql: uploads_when_sql_ran.append(bucket.uploaded_names)

        loaded = loader.load_from_iterable(
            ({'id': i, 'name': f'name {i}'} for i in range(ROW_COUNT)),
            table,
        )

        assert loaded == ROW_COUNT
        expected = ['data_1.parquet.snappy', 'data_2.parquet.snappy', 'data_3.parquet.snappy']
        assert bucket.uploaded_names == expected
        assert uploads_when_sql_ran == [expected]
        assert all(upload.thread is not threading.current_thread() for upload in bucket.uploads)
        sql = cursor.execute.call_args[0][0]
        assert "format => 'parquet'" in sql
        assert 'BY NAME' in sql
        assert not upload_threads_alive()

    def test_default_max_rows(self):
        assert DatabricksS3ParquetBulkLoader(s3_config()).s3_file_max_rows == 500_000

    def test_empty_iterable(self, bucket):
        loader = DatabricksS3ParquetBulkLoader(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        table, cursor = self._table_with_cursor()

        assert loader.load_from_iterable(iter([]), table) == 0
        cursor.execute.assert_not_called()
        assert bucket.uploads == []
        assert not upload_threads_alive()

    def test_error_while_writing_aborts_uploads(self, bucket):
        loader = DatabricksS3ParquetBulkLoader(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        table, cursor = self._table_with_cursor()

        def rows():
            for i in range(ROW_COUNT):
                if i == 2 * CHUNK_SIZE + 2:
                    raise KeyError('row source failed')
                yield {'id': i, 'name': f'name {i}'}

        with pytest.raises(KeyError, match='row source failed'):
            loader.load_from_iterable(rows(), table)

        cursor.execute.assert_not_called()
        assert 'data_3.parquet.snappy' not in bucket.uploaded_names
        assert not upload_threads_alive()
