import csv
import logging
import pickle
from io import StringIO
from pathlib import Path

import pytest

from bi_etl.components import csv_writer as csv_writer_module
from bi_etl.components.csv_writer import CSVWriter, QUOTE_NONE


COLUMNS = ['id', 'name']


def make_writer(target, **kwargs) -> CSVWriter:
    kwargs.setdefault('column_names', COLUMNS)
    return CSVWriter(None, target, **kwargs)


def insert(writer: CSVWriter, **values):
    return writer.insert(writer.Row(data=values))


def test_writes_header_and_rows_to_filename(tmp_path):
    path = tmp_path / 'out.csv'
    with make_writer(str(path)) as writer:
        insert(writer, id=1, name='a')
        insert(writer, id=2, name='b')
    assert path.read_text() == 'id,name\n1,a\n2,b\n'


def test_accepts_path_object(tmp_path):
    path = tmp_path / 'out.csv'
    with make_writer(path) as writer:
        insert(writer, id=1, name='a')
    assert path.read_text() == 'id,name\n1,a\n'


def test_no_header(tmp_path):
    path = tmp_path / 'out.csv'
    with make_writer(path, include_header=False) as writer:
        insert(writer, id=1, name='a')
    assert path.read_text() == '1,a\n'


def test_overwrites_existing_file_by_default(tmp_path):
    path = tmp_path / 'out.csv'
    path.write_text('old content\n')
    with make_writer(path) as writer:
        insert(writer, id=1, name='a')
    assert path.read_text() == 'id,name\n1,a\n'


def test_append_to_existing_file_skips_header(tmp_path):
    path = tmp_path / 'out.csv'
    path.write_text('id,name\n1,a\n')
    with make_writer(path, append=True) as writer:
        insert(writer, id=2, name='b')
    assert path.read_text() == 'id,name\n1,a\n2,b\n'


def test_append_to_missing_file_writes_header(tmp_path):
    path = tmp_path / 'out.csv'
    with make_writer(path, append=True) as writer:
        insert(writer, id=1, name='a')
    assert path.read_text() == 'id,name\n1,a\n'


def test_file_object_is_not_closed_by_writer():
    target = StringIO()
    writer = make_writer(target)
    insert(writer, id=1, name='a')
    writer.close()
    assert not target.closed
    assert target.getvalue() == 'id,name\n1,a\n'


def test_non_io_file_like_object_is_accepted(caplog):
    class Sink:
        def __init__(self):
            self.chunks = []

        def write(self, text):
            self.chunks.append(text)

    sink = Sink()
    with caplog.at_level(logging.INFO):
        writer = make_writer(sink, include_header=False)
    insert(writer, id=1, name='a')
    assert ''.join(sink.chunks) == '1,a\n'
    assert any('Treating input as file object' in r.getMessage() for r in caplog.records)
    writer.close()


def test_close_is_idempotent_and_closes_owned_file(tmp_path):
    writer = make_writer(tmp_path / 'out.csv')
    assert not writer.is_closed
    writer.close()
    assert writer.is_closed
    assert writer.file.closed
    writer.close()
    assert writer.is_closed


def test_logical_name_defaults_to_file_basename(tmp_path):
    with make_writer(tmp_path / 'out.csv') as writer:
        assert writer.logical_name == 'out.csv'


def test_logical_name_for_file_object_without_name_uses_str():
    target = StringIO()
    writer = make_writer(target)
    assert writer.logical_name == str(target)
    writer.close()


def test_explicit_logical_name():
    writer = make_writer(StringIO(), logical_name='my_output')
    assert writer.logical_name == 'my_output'
    writer.close()


def test_repr(tmp_path):
    with make_writer(tmp_path / 'out.csv') as writer:
        text = repr(writer)
    assert text.startswith('CSVWriter(task=None,logical_name=out.csv, ')
    assert "column_names=['id', 'name']" in text


def test_get_writer_is_cached():
    writer = make_writer(StringIO())
    assert writer.get_writer() is writer.get_writer()
    writer.close()


def test_kwargs_set_attributes():
    writer = make_writer(StringIO(), delimiter='|', quotechar="'", null='NULL')
    assert writer.delimiter == '|'
    assert writer.quotechar == "'"
    assert writer.null == 'NULL'
    writer.close()


def test_delimiter_and_lineterminator():
    target = StringIO()
    writer = make_writer(target, delimiter='|', lineterminator='\r\n')
    insert(writer, id=1, name='a')
    assert target.getvalue() == 'id|name\r\n1|a\r\n'
    writer.close()


def test_values_with_delimiter_are_quoted():
    target = StringIO()
    writer = make_writer(target, include_header=False)
    insert(writer, id=1, name='a,b "c"')
    assert target.getvalue() == '1,"a,b ""c"""\n'
    writer.close()


def test_quote_none_with_escapechar():
    target = StringIO()
    writer = make_writer(target, include_header=False, quoting=QUOTE_NONE, escapechar='\\')
    insert(writer, id=1, name='a,b')
    assert target.getvalue() == '1,a\\,b\n'
    writer.close()


def test_none_written_as_empty_by_default():
    target = StringIO()
    writer = make_writer(target, include_header=False)
    insert(writer, id=1, name=None)
    assert target.getvalue() == '1,\n'
    writer.close()


def test_custom_null_value():
    target = StringIO()
    writer = make_writer(target, include_header=False, null='\\N')
    new_row = insert(writer, id=1, name=None)
    assert target.getvalue() == '1,\\N\n'
    assert new_row['name'] == '\\N'
    writer.close()


def test_blank_string_becomes_space_by_default():
    target = StringIO()
    writer = make_writer(target, include_header=False, quoting=QUOTE_NONE, escapechar='\\')
    insert(writer, id=1, name='')
    assert target.getvalue() == '1, \n'
    writer.close()


def test_blank_string_kept_when_fix_blank_strings_disabled():
    target = StringIO()
    writer = make_writer(target, include_header=False, fix_blank_strings=False)
    insert(writer, id=1, name='')
    assert target.getvalue() == '1,\n'
    writer.close()


def test_additional_insert_values_add_and_override():
    target = StringIO()
    writer = make_writer(target, include_header=False)
    new_row = writer.insert(
        writer.Row(data={'id': 1, 'name': 'a'}),
        additional_insert_values={'name': 'override'},
    )
    assert target.getvalue() == '1,override\n'
    assert new_row['name'] == 'override'
    writer.close()


def test_extra_source_columns_are_dropped():
    target = StringIO()
    writer = make_writer(target, include_header=False)
    new_row = insert(writer, id=1, name='a', extra='ignored')
    assert target.getvalue() == '1,a\n'
    assert 'extra' not in new_row
    writer.close()


def test_missing_columns_written_blank():
    target = StringIO()
    writer = make_writer(target, include_header=False)
    insert(writer, id=1)
    assert target.getvalue() == '1,\n'
    writer.close()


def test_empty_source_row_asserts():
    writer = make_writer(StringIO())
    with pytest.raises(AssertionError, match='Empty row passed'):
        writer.insert_row(writer.Row())
    writer.close()


def test_row_without_any_output_columns_asserts():
    writer = make_writer(StringIO())
    with pytest.raises(AssertionError, match='Empty row generated'):
        insert(writer, unrelated=1)
    writer.close()


def test_write_header_manual_then_insert_does_not_duplicate_header():
    target = StringIO()
    writer = make_writer(target)
    writer.write_header()
    insert(writer, id=1, name='a')
    assert target.getvalue() == 'id,name\n1,a\n'
    writer.close()


def test_write_header_without_include_header_writes_nothing():
    target = StringIO()
    writer = make_writer(target, include_header=False)
    writer.write_header()
    assert target.getvalue() == ''
    writer.close()


def test_insert_single_row_returns_new_row():
    writer = make_writer(StringIO())
    new_row = insert(writer, id=1, name='a')
    assert new_row['id'] == 1
    assert new_row['name'] == 'a'
    writer.close()


def test_insert_list_returns_none():
    writer = make_writer(StringIO())
    assert writer.insert([writer.Row(data={'id': 1, 'name': 'a'})]) is None
    writer.close()


def test_insert_list_writes_all_rows():
    target = StringIO()
    writer = make_writer(target, include_header=False)
    writer.insert([
        writer.Row(data={'id': 1, 'name': 'a'}),
        writer.Row(data={'id': 2, 'name': 'b'}),
    ])
    assert target.getvalue() == '1,a\n2,b\n'
    writer.close()


def test_trace_data_logs_raw_row(caplog):
    writer = make_writer(StringIO(), trace_data=True)
    with caplog.at_level(logging.DEBUG, logger=writer.log.name):
        insert(writer, id=1, name='a')
    assert any('Raw row being inserted' in r.getMessage() for r in caplog.records)
    writer.close()


def test_large_field_support_raises_csv_field_size_limit(monkeypatch):
    calls = []
    monkeypatch.setattr(csv_writer_module.csv, 'field_size_limit', lambda *args: calls.append(args))
    writer = make_writer(StringIO(), large_field_support=True)
    writer.get_writer()
    assert calls == [(2147483647,)]
    writer.close()


def test_large_field_support_off_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(csv_writer_module.csv, 'field_size_limit', lambda *args: calls.append(args))
    writer = make_writer(StringIO())
    writer.get_writer()
    assert calls == []
    writer.close()


def test_commit_is_noop():
    writer = make_writer(StringIO())
    assert writer.commit() is None
    writer.close()


def test_pickle_round_trip_reopens_file(tmp_path):
    path = tmp_path / 'out.csv'
    writer = make_writer(path, include_header=False, logical_name='custom')
    clone = pickle.loads(pickle.dumps(writer))
    try:
        assert isinstance(clone, CSVWriter)
        assert clone.column_names == COLUMNS
        assert clone.include_header is False
        assert clone.logical_name == 'custom'
        assert Path(clone.file.name) == path
    finally:
        clone.close()
        writer.close()


def test_writer_output_readable_by_csv_module(tmp_path):
    path = tmp_path / 'out.csv'
    with make_writer(path) as writer:
        insert(writer, id=1, name='x,y')
        insert(writer, id=2, name='multi\nline')
    with open(path, newline='') as f:
        rows = list(csv.DictReader(f))
    assert rows == [{'id': '1', 'name': 'x,y'}, {'id': '2', 'name': 'multi\nline'}]
