from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pyarrow
import pyarrow.parquet as pq
import pytest
from sqlalchemy import DateTime, Integer, Numeric, String

from bi_etl.components.parquet_writer import ParquetWriter, build_parquet_schema
from bi_etl.components.pyarrow_dataset_reader import PyArrowDatasetReader
from bi_etl.scheduler.etl_task import ETLTask
from tests.config_for_tests import build_config
from tests.test_bulk_loaders.bulk_loader_test_helpers import KwTable

SCHEMA = pyarrow.schema(
    [
        pyarrow.field('id', pyarrow.int64()),
        pyarrow.field('name', pyarrow.string()),
        pyarrow.field('score', pyarrow.float64()),
    ]
)


@pytest.fixture
def task() -> ETLTask:
    return ETLTask(config=build_config())


@pytest.fixture
def parquet_path(tmp_path: Path) -> Path:
    return tmp_path / 'out.parquet'


def test_build_parquet_schema():
    table = KwTable('tbl', id=Integer(), name=String(), amount=Numeric(10, 2), created=DateTime(timezone=True))
    schema = build_parquet_schema(table)
    assert schema.names == ['id', 'name', 'amount', 'created']
    assert str(schema.field('amount').type) == 'decimal128(10, 2)'
    assert str(schema.field('created').type) == 'timestamp[us, tz=UTC]'
    assert all(field.nullable for field in schema)


def test_column_names_from_schema(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA) as dst:
        assert dst.column_names == ['id', 'name', 'score']


def test_insert_row_round_trip(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA) as dst:
        dst.insert_row({'id': 1, 'name': 'Alice', 'score': 1.5})
        dst.insert_row({'id': 2, 'name': 'Bob'})
        assert dst.rows_written == 2

    assert pq.read_table(parquet_path).to_pylist() == [
        {'id': 1, 'name': 'Alice', 'score': 1.5},
        {'id': 2, 'name': 'Bob', 'score': None},
    ]


def test_insert_list(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA) as dst:
        dst.insert([{'id': i, 'name': str(i)} for i in range(3)])

    assert pq.read_table(parquet_path).column('id').to_pylist() == [0, 1, 2]


def test_additional_insert_values(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA) as dst:
        dst.insert_row({'id': 1, 'name': 'a'}, additional_insert_values={'name': 'override', 'score': 2.0})

    assert pq.read_table(parquet_path).to_pylist() == [{'id': 1, 'name': 'override', 'score': 2.0}]


def test_extra_columns_ignored(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA) as dst:
        dst.insert_row({'id': 1, 'name': 'a', 'not_in_schema': 5})

    assert pq.read_table(parquet_path).column_names == ['id', 'name', 'score']


def test_row_groups_follow_row_group_size(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA, row_group_size=10) as dst:
        for i in range(25):
            dst.insert_row({'id': i, 'name': str(i)})

    parquet_file = pq.ParquetFile(parquet_path)
    assert [parquet_file.metadata.row_group(i).num_rows for i in range(parquet_file.num_row_groups)] == [10, 10, 5]
    assert parquet_file.read().column('id').to_pylist() == list(range(25))


def test_commit_writes_buffered_rows(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA) as dst:
        dst.insert_row({'id': 1, 'name': 'a'})
        dst.commit()
        dst.insert_row({'id': 2, 'name': 'b'})

    assert pq.ParquetFile(parquet_path).num_row_groups == 2


def test_default_compression_is_snappy(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA) as dst:
        dst.insert_row({'id': 1, 'name': 'a'})

    assert pq.ParquetFile(parquet_path).metadata.row_group(0).column(0).compression == 'SNAPPY'


def test_explicit_compression(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA, compression='GZIP') as dst:
        dst.insert_row({'id': 1, 'name': 'a'})

    assert pq.ParquetFile(parquet_path).metadata.row_group(0).column(0).compression == 'GZIP'


def test_empty_file_is_readable(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA):
        pass

    table = pq.read_table(parquet_path)
    assert table.num_rows == 0
    assert table.schema.names == ['id', 'name', 'score']


def test_from_table_with_datetime_and_decimal(task, parquet_path):
    table = KwTable('tbl', created=DateTime(), amount=Numeric(10, 2))
    created = datetime(2020, 1, 2, 3, 4, 5, 678901)
    with ParquetWriter.from_table(task, parquet_path, table) as dst:
        dst.insert_row({'created': created, 'amount': Decimal('1.25')})

    assert pq.read_table(parquet_path).to_pylist() == [{'created': created, 'amount': Decimal('1.25')}]


def test_str_path_and_file_path(task, parquet_path):
    with ParquetWriter(task, str(parquet_path), SCHEMA) as dst:
        assert dst.file_path == str(parquet_path)
        assert dst.logical_name == 'out.parquet'
    with ParquetWriter(task, parquet_path, SCHEMA, logical_name='mine') as dst:
        assert dst.logical_name == 'mine'


def test_file_object(task, parquet_path):
    with open(parquet_path, 'wb') as f:
        with ParquetWriter(task, f, SCHEMA) as dst:
            dst.insert_row({'id': 1, 'name': 'a'})

    assert pq.read_table(parquet_path).num_rows == 1


def test_close_with_error_discards_buffer(task, parquet_path):
    dst = ParquetWriter(task, parquet_path, SCHEMA)
    dst.insert_row({'id': 1, 'name': 'a'})
    dst.close(error=True)

    assert pq.read_table(parquet_path).num_rows == 0


def test_round_trip_with_dataset_reader(task, parquet_path):
    with ParquetWriter(task, parquet_path, SCHEMA) as dst:
        dst.insert([{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}])

    with PyArrowDatasetReader(task, parquet_path, pyarrow_format='parquet') as src:
        assert [(r['id'], r['name']) for r in src] == [(1, 'a'), (2, 'b')]
