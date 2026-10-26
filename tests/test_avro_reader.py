from pathlib import Path

import fastavro
import pytest

from bi_etl.components.avro_reader import AvroReader
from bi_etl.scheduler.etl_task import ETLTask
from tests.config_for_tests import build_config

SCHEMA = {
    'type': 'record',
    'name': 'sample',
    'fields': [
        {'name': 'id', 'type': 'long'},
        {'name': 'name', 'type': 'string'},
        {'name': 'score', 'type': ['null', 'double'], 'default': None},
    ],
}

RECORDS = [
    {'id': 1, 'name': 'Alice', 'score': 1.5},
    {'id': 2, 'name': 'Bob', 'score': 2.5},
    {'id': 3, 'name': 'Carol', 'score': None},
]


@pytest.fixture
def task() -> ETLTask:
    return ETLTask(config=build_config())


@pytest.fixture
def avro_file(tmp_path: Path) -> Path:
    path = tmp_path / 'sample.avro'
    with open(path, 'wb') as f:
        fastavro.writer(f, fastavro.parse_schema(SCHEMA), RECORDS)
    return path


def test_column_names(task, avro_file):
    with AvroReader(task, avro_file) as src:
        assert src.column_names == ['id', 'name', 'score']


def test_iterate_rows(task, avro_file):
    with AvroReader(task, avro_file) as src:
        rows = list(src)
        assert src.rows_read == 3

    assert [row['id'] for row in rows] == [1, 2, 3]
    assert [row['name'] for row in rows] == ['Alice', 'Bob', 'Carol']
    assert [row['score'] for row in rows] == [1.5, 2.5, None]


def test_column_names_then_iterate(task, avro_file):
    with AvroReader(task, avro_file) as src:
        _ = src.column_names
        assert len(list(src)) == 3


def test_source_as_str(task, avro_file):
    with AvroReader(task, str(avro_file)) as src:
        assert len(list(src)) == 3


def test_source_as_file_object_not_closed(task, avro_file):
    with open(avro_file, 'rb') as f:
        with AvroReader(task, f) as src:
            assert len(list(src)) == 3
        assert not f.closed


def test_path_source_closed_on_close(task, avro_file):
    src = AvroReader(task, avro_file)
    assert not src.file.closed
    src.close()
    assert src.file.closed


def test_logical_name_default_from_file(task, avro_file):
    with AvroReader(task, avro_file) as src:
        assert src.logical_name == 'sample.avro'


def test_logical_name_override(task, avro_file):
    with AvroReader(task, avro_file, logical_name='my_source') as src:
        assert src.logical_name == 'my_source'


def test_reader_schema_projection(task, avro_file):
    reader_schema = {
        'type': 'record',
        'name': 'sample',
        'fields': [
            {'name': 'name', 'type': 'string'},
            {'name': 'extra', 'type': 'string', 'default': 'x'},
        ],
    }
    with AvroReader(task, avro_file, reader_schema=reader_schema) as src:
        assert src.column_names == ['name', 'extra']
        rows = list(src)

    assert [row['name'] for row in rows] == ['Alice', 'Bob', 'Carol']
    assert all(row['extra'] == 'x' for row in rows)


def test_empty_file(task, tmp_path):
    path = tmp_path / 'empty.avro'
    with open(path, 'wb') as f:
        fastavro.writer(f, fastavro.parse_schema(SCHEMA), [])

    with AvroReader(task, path) as src:
        assert src.column_names == ['id', 'name', 'score']
        assert list(src) == []
        assert src.rows_read == 0


def test_multiple_blocks(task, tmp_path):
    path = tmp_path / 'blocks.avro'
    records = [{'id': i, 'name': str(i), 'score': None} for i in range(25)]
    with open(path, 'wb') as f:
        fastavro.writer(f, fastavro.parse_schema(SCHEMA), records, sync_interval=50)

    with AvroReader(task, path) as src:
        rows = list(src)

    assert [row['id'] for row in rows] == list(range(25))


def test_where_criteria_dict(task, avro_file):
    with AvroReader(task, avro_file) as src:
        rows = list(src.where(criteria_dict={'name': 'Bob'}))

    assert len(rows) == 1
    assert rows[0]['id'] == 2


def test_max_rows(task, avro_file):
    with AvroReader(task, avro_file, max_rows=2) as src:
        rows = list(src)

    assert [row['id'] for row in rows] == [1, 2]


def test_kwargs_set_as_attributes(task, avro_file):
    with AvroReader(task, avro_file, log_first_row=False) as src:
        assert src.log_first_row is False


def test_non_record_schema_raises(task, tmp_path):
    path = tmp_path / 'longs.avro'
    with open(path, 'wb') as f:
        fastavro.writer(f, fastavro.parse_schema('long'), [1, 2, 3])

    with AvroReader(task, path) as src:
        with pytest.raises(ValueError):
            _ = src.column_names


def test_missing_file_raises(task, tmp_path):
    with pytest.raises(FileNotFoundError):
        AvroReader(task, tmp_path / 'does_not_exist.avro')
