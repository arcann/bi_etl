from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest import mock

import fastavro
import pytest
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Interval, JSON, Numeric, String

from bi_etl.components.avro_reader import AvroReader
from bi_etl.components.avro_writer import AvroWriter, _find_tagged_branches, build_avro_schema, default_avro_codec
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


def test_default_codec_can_write_a_file(task, avro_path):
    with AvroWriter(task, avro_path, SCHEMA) as dst:
        dst.write_record({'id': 1, 'name': 'a'})

    with open(avro_path, 'rb') as f:
        assert fastavro.reader(f).codec == default_avro_codec()
    assert len(read_back(avro_path)) == 1


def test_default_codec_falls_back_to_deflate_without_snappy_library():
    default_avro_codec.cache_clear()
    try:
        with mock.patch('fastavro.write.Writer', side_effect=ValueError('snappy codec is supported but ...')):
            assert default_avro_codec() == 'deflate'
    finally:
        default_avro_codec.cache_clear()


def test_tagged_branches_found_for_nullable_primitives_only():
    schema = fastavro.parse_schema(
        {
            'type': 'record',
            'name': 'tagging',
            'fields': [
                {'name': 'plain', 'type': 'long'},
                {'name': 'nullable_long', 'type': ['null', 'long'], 'default': None},
                {'name': 'nullable_decimal', 'type': ['null', {'type': 'bytes', 'logicalType': 'decimal', 'precision': 10, 'scale': 2}]},
                {'name': 'nullable_date', 'type': ['null', {'type': 'int', 'logicalType': 'date'}]},
                {'name': 'two_types', 'type': ['null', 'long', 'string']},
                {'name': 'enum', 'type': ['null', {'type': 'enum', 'name': 'colors', 'symbols': ['RED', 'BLUE']}]},
            ],
        }
    )
    assert _find_tagged_branches(schema) == [
        ('nullable_long', 'long'),
        ('nullable_decimal', 'bytes'),
        ('nullable_date', 'int'),
    ]


def test_all_types_with_nulls_round_trip(task, avro_path):
    table = KwTable(
        'tbl',
        id=Integer(),
        name=String(),
        score=Float(),
        amount=Numeric(12, 2),
        created=DateTime(),
        day=Date(),
        flag=Boolean(),
        duration=Interval(),
    )
    created = datetime(2020, 1, 2, 3, 4, 5)
    with AvroWriter.from_table(task, avro_path, table) as dst:
        dst.insert_row(
            KwRow(id=1, name='a,"b"', score=1.5, amount=Decimal('-12.34'), created=created, day=date(2020, 1, 2),
                  flag=True, duration=timedelta(seconds=90))
        )
        dst.insert_row(
            KwRow(id=2, name=None, score=None, amount=None, created=None, day=None, flag=None, duration=None)
        )

    rows = read_back(avro_path)
    assert rows[0]['name'] == 'a,"b"'
    assert rows[0]['score'] == 1.5
    assert rows[0]['amount'] == Decimal('-12.34')
    assert rows[0]['day'] == date(2020, 1, 2)
    assert rows[0]['flag'] is True
    assert rows[0]['duration'] == 90
    # Naive datetimes are read as local time by fastavro on some platforms, so only the type is checked
    assert isinstance(rows[0]['created'], datetime)
    assert all(rows[1][name] is None for name in ('name', 'score', 'amount', 'created', 'day', 'flag', 'duration'))
    assert rows[1]['id'] == 2


def test_insert_row_file_is_same_as_write_record(task, tmp_path):
    table = KwTable('tbl', id=Integer(), name=String(), amount=Numeric(10, 2))
    schema, _ = build_avro_schema(table, 'tbl')
    values = [(1, 'a', Decimal('1.10')), (2, None, None), (3, 'c', Decimal('3.30'))]
    with AvroWriter(task, tmp_path / 'record.avro', schema, codec='null') as dst:
        for i, name, amount in values:
            dst.write_record({'id': i, 'name': name, 'amount': amount})
    with AvroWriter(task, tmp_path / 'row.avro', schema, codec='null') as dst:
        for i, name, amount in values:
            dst.insert_row(KwRow(id=i, name=name, amount=amount))

    assert read_back(tmp_path / 'row.avro') == read_back(tmp_path / 'record.avro')


def test_insert_row_stats_counted_per_stat_name_and_parent(task, avro_path):
    table = KwTable('tbl', id=Integer())
    with AvroWriter.from_table(task, avro_path, table) as dst:
        dst.insert_row(KwRow(id=1))
        dst.insert_row(KwRow(id=2))
        dst.insert_row(KwRow(id=3), stat_name='other')
        dst.insert_row(KwRow(id=4))
        assert dst.statistics['insert']['inserts'] == 3
        assert dst.statistics['other']['inserts'] == 1
