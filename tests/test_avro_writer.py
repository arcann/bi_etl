from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import fastavro
import pytest
from sqlalchemy import Integer, Interval, JSON, Numeric, String

from bi_etl.components.avro_reader import AvroReader
from bi_etl.components.avro_writer import AvroWriter, build_avro_schema, default_avro_codec
from bi_etl.scheduler.etl_task import ETLTask
from tests.config_for_tests import build_config
from tests.test_bulk_loaders.bulk_loader_test_helpers import KwRow, KwTable

SCHEMA = {
    'type': 'record',
    'name': 'sample',
    'fields': [
        {'name': 'id', 'type': 'long'},
        {'name': 'name', 'type': 'string'},
        {'name': 'score', 'type': ['null', 'double'], 'default': None},
    ],
}


@pytest.fixture
def task() -> ETLTask:
    return ETLTask(config=build_config())


@pytest.fixture
def avro_path(tmp_path: Path) -> Path:
    return tmp_path / 'out.avro'


def read_back(path) -> list:
    with open(path, 'rb') as f:
        return list(fastavro.reader(f))


def test_default_codec_is_known():
    assert default_avro_codec() in {'snappy', 'deflate'}


def test_column_names_from_schema(task, avro_path):
    with AvroWriter(task, avro_path, SCHEMA) as dst:
        assert dst.column_names == ['id', 'name', 'score']


def test_write_record_round_trip(task, avro_path):
    with AvroWriter(task, avro_path, SCHEMA) as dst:
        dst.write_record({'id': 1, 'name': 'Alice', 'score': 1.5})
        dst.write_record({'id': 2, 'name': 'Bob'})
        assert dst.rows_written == 2

    assert read_back(avro_path) == [
        {'id': 1, 'name': 'Alice', 'score': 1.5},
        {'id': 2, 'name': 'Bob', 'score': None},
    ]


def test_insert_row_and_list(task, avro_path):
    table = KwTable('tbl', id=Integer(), name=String())
    with AvroWriter.from_table(task, avro_path, table) as dst:
        dst.insert_row(KwRow(id=1, name='a'))
        dst.insert([KwRow(id=2, name='b'), KwRow(id=3, name='c')])
        assert dst.rows_written == 3

    assert [r['id'] for r in read_back(avro_path)] == [1, 2, 3]


def test_additional_insert_values(task, avro_path):
    table = KwTable('tbl', id=Integer(), name=String())
    with AvroWriter.from_table(task, avro_path, table) as dst:
        dst.insert_row(KwRow(id=1, name='a'), additional_insert_values={'name': 'override'})

    assert read_back(avro_path) == [{'id': 1, 'name': 'override'}]


def test_values_translated_but_none_is_not(task, avro_path):
    table = KwTable('tbl', id=Integer(), duration=Interval(), attributes=JSON())
    with AvroWriter.from_table(task, avro_path, table) as dst:
        dst.insert_row(KwRow(id=1, duration=timedelta(minutes=2), attributes={'a': 1}))
        dst.insert_row(KwRow(id=2, duration=None, attributes=None))

    assert read_back(avro_path) == [
        {'id': 1, 'duration': 120, 'attributes': '{"a": 1}'},
        {'id': 2, 'duration': None, 'attributes': None},
    ]


def test_logical_types_round_trip(task, avro_path):
    table = KwTable('tbl', amount=Numeric(10, 2))
    schema, translate = build_avro_schema(table, 'tbl')
    assert translate == {}
    with AvroWriter(task, avro_path, schema) as dst:
        dst.write_record({'amount': Decimal('12.34')})

    assert read_back(avro_path) == [{'amount': Decimal('12.34')}]


def test_build_avro_schema_names_and_translations():
    table = KwTable('tbl', id=Integer(), duration=Interval())
    schema, translate = build_avro_schema(table, 'my_schema')
    assert schema['name'] == 'my_schema'
    assert [f['name'] for f in schema['fields']] == ['id', 'duration']
    assert set(translate) == {'duration'}


def test_from_table_schema_name_default(task, avro_path):
    table = KwTable('tbl', id=Integer())
    with AvroWriter.from_table(task, avro_path, table) as dst:
        assert dst.parsed_schema['name'].endswith(table.qualified_table_name)


def test_explicit_codec(task, avro_path):
    with AvroWriter(task, avro_path, SCHEMA, codec='deflate') as dst:
        dst.write_record({'id': 1, 'name': 'a'})
    with open(avro_path, 'rb') as f:
        assert fastavro.reader(f).codec == 'deflate'


def test_empty_file_is_readable(task, avro_path):
    with AvroWriter(task, avro_path, SCHEMA):
        pass

    assert read_back(avro_path) == []


def test_many_rows(task, avro_path):
    with AvroWriter(task, avro_path, SCHEMA) as dst:
        for i in range(2500):
            dst.write_record({'id': i, 'name': str(i)})
        assert dst.rows_written == 2500

    assert [r['id'] for r in read_back(avro_path)] == list(range(2500))


def test_str_path_closed_on_close(task, avro_path):
    dst = AvroWriter(task, str(avro_path), SCHEMA)
    assert not dst.file.closed
    assert dst.file_path == str(avro_path)
    dst.close()
    assert dst.file.closed


def test_file_object_not_closed(task, avro_path):
    with open(avro_path, 'wb') as f:
        with AvroWriter(task, f, SCHEMA) as dst:
            dst.write_record({'id': 1, 'name': 'a'})
        assert not f.closed

    assert len(read_back(avro_path)) == 1


def test_logical_name(task, avro_path):
    with AvroWriter(task, avro_path, SCHEMA) as dst:
        assert dst.logical_name == 'out.avro'
    with AvroWriter(task, avro_path, SCHEMA, logical_name='mine') as dst:
        assert dst.logical_name == 'mine'


def test_commit_flushes(task, avro_path):
    with AvroWriter(task, avro_path, SCHEMA) as dst:
        dst.write_record({'id': 1, 'name': 'a'})
        dst.commit()
        dst.file.flush()
        assert len(read_back(avro_path)) == 1


def test_bad_schema_raises_and_closes_file(task, avro_path):
    with pytest.raises(Exception):
        AvroWriter(task, avro_path, {'type': 'record', 'name': 'bad', 'fields': [{'name': 'x', 'type': 'nope'}]})
    # File handle was released so it can be removed (Windows would refuse otherwise)
    avro_path.unlink()


def test_round_trip_with_avro_reader(task, avro_path):
    table = KwTable('tbl', id=Integer(), name=String())
    with AvroWriter.from_table(task, avro_path, table) as dst:
        dst.insert([KwRow(id=1, name='a'), KwRow(id=2, name='b')])

    with AvroReader(task, avro_path) as src:
        assert src.column_names == ['id', 'name']
        assert [(r['id'], r['name']) for r in src] == [(1, 'a'), (2, 'b')]
