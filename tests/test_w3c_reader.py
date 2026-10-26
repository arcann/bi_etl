import logging
from io import StringIO

import pytest

from bi_etl.components.w3c_reader import W3CReader

HEADER = '#Software: Microsoft Internet Information Services\n' \
         '#Version: 1.0\n' \
         '#Fields: date time cs-method sc-status\n'


def make_reader(source, **kwargs) -> W3CReader:
    return W3CReader(None, source, **kwargs)


def read_all(reader: W3CReader) -> list:
    return [row.as_dict for row in reader]


def test_reads_rows_from_file_object():
    text = HEADER + '2020-01-01 10:00:00 GET 200\n2020-01-01 10:00:01 POST 404\n'
    with make_reader(StringIO(text)) as reader:
        assert read_all(reader) == [
            {'date': '2020-01-01', 'time': '10:00:00', 'cs-method': 'GET', 'sc-status': '200'},
            {'date': '2020-01-01', 'time': '10:00:01', 'cs-method': 'POST', 'sc-status': '404'},
        ]


def test_reads_rows_from_filename(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_text(HEADER + '2020-01-01 10:00:00 GET 200\n')
    with make_reader(str(path)) as reader:
        assert read_all(reader) == [
            {'date': '2020-01-01', 'time': '10:00:00', 'cs-method': 'GET', 'sc-status': '200'},
        ]


def test_column_names_from_fields_directive():
    with make_reader(StringIO(HEADER)) as reader:
        assert reader.column_names == ['date', 'time', 'cs-method', 'sc-status']


def test_comment_lines_between_rows_are_skipped():
    text = HEADER + 'a b c d\n#Date: 2020-01-01\ne f g h\n'
    with make_reader(StringIO(text)) as reader:
        assert [list(r.values()) for r in reader] == [['a', 'b', 'c', 'd'], ['e', 'f', 'g', 'h']]


def test_header_only_returns_no_rows():
    with make_reader(StringIO(HEADER)) as reader:
        assert read_all(reader) == []


def test_lines_are_stripped():
    text = HEADER + '  a b c d  \r\n'
    with make_reader(StringIO(text)) as reader:
        assert [list(r.values()) for r in reader] == [['a', 'b', 'c', 'd']]


def test_eof_before_column_names_raises():
    with make_reader(StringIO('#Software: x\n#Version: 1.0\n')) as reader:
        with pytest.raises(ValueError, match='EOF found before column names'):
            _ = reader.column_names


def test_empty_file_raises_on_column_names():
    with make_reader(StringIO('')) as reader:
        with pytest.raises(ValueError, match='EOF found before column names'):
            _ = reader.column_names


def test_data_before_column_names_raises():
    with make_reader(StringIO('a b c d\n' + HEADER)) as reader:
        with pytest.raises(ValueError, match='Data lines started before column names'):
            _ = reader.column_names


def test_row_with_extra_columns_raises():
    text = HEADER + 'a b c d e\n'
    with make_reader(StringIO(text)) as reader:
        with pytest.raises(ValueError, match='has extra columns'):
            read_all(reader)


def test_short_row_is_padded_with_none_and_warns(caplog):
    text = HEADER + 'a b\n'
    with make_reader(StringIO(text)) as reader:
        with caplog.at_level(logging.WARNING):
            rows = read_all(reader)
    assert rows == [{'date': 'a', 'time': 'b', 'cs-method': None, 'sc-status': None}]
    assert any('is missing columns' in r.getMessage() for r in caplog.records)


def test_short_row_warnings_respect_limit(caplog):
    text = HEADER + 'a b\n' * 5
    with make_reader(StringIO(text)) as reader:
        reader.warnings_limit = 2
        with caplog.at_level(logging.WARNING):
            read_all(reader)
    assert sum('is missing columns' in r.getMessage() for r in caplog.records) == 2


def test_blank_lines_are_skipped():
    text = HEADER + 'a b c d\n\ne f g h\n'
    with make_reader(StringIO(text)) as reader:
        assert [list(r.values()) for r in reader] == [['a', 'b', 'c', 'd'], ['e', 'f', 'g', 'h']]


def test_trailing_blank_line_is_ignored():
    text = HEADER + 'a b c d\n\n'
    with make_reader(StringIO(text)) as reader:
        assert [list(r.values()) for r in reader] == [['a', 'b', 'c', 'd']]


def test_read_all_false_reads_line_by_line():
    text = HEADER + 'a b c d\ne f g h\n'
    with make_reader(StringIO(text), read_all=False) as reader:
        assert [list(r.values()) for r in reader] == [['a', 'b', 'c', 'd'], ['e', 'f', 'g', 'h']]


def test_line_num_tracks_lines_read():
    text = HEADER + 'a b c d\ne f g h\n'
    with make_reader(StringIO(text), read_all=False) as reader:
        read_all(reader)
        assert reader.line_num == 5


def test_line_num_tracks_lines_read_with_read_all():
    text = HEADER + 'a b c d\ne f g h\n'
    with make_reader(StringIO(text)) as reader:
        read_all(reader)
        assert reader.line_num == 5


def test_logical_name_from_file_basename(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_text(HEADER)
    with make_reader(str(path)) as reader:
        assert reader.logical_name == 'log.txt'


def test_logical_name_for_file_object_without_name_uses_str():
    source = StringIO(HEADER)
    with make_reader(source) as reader:
        assert reader.logical_name == str(source)


def test_explicit_logical_name():
    with make_reader(StringIO(HEADER), logical_name='web_log') as reader:
        assert reader.logical_name == 'web_log'


def test_kwargs_set_attributes():
    with make_reader(StringIO(HEADER), read_all=False) as reader:
        assert reader.read_all is False


def test_encoding_used_when_opening_filename(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_bytes((HEADER + 'é b c d\n').encode('utf-16'))
    with make_reader(str(path), encoding='utf-16') as reader:
        assert read_all(reader)[0]['date'] == 'é'


def test_errors_argument_used_when_opening_filename(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_bytes(HEADER.encode() + b'\xff b c d\n')
    with make_reader(str(path), encoding='utf-8', errors='replace') as reader:
        assert read_all(reader)[0]['date'] == '�'


def test_invalid_bytes_raise_with_strict_errors(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_bytes(HEADER.encode() + b'\xff b c d\n')
    with make_reader(str(path), encoding='utf-8') as reader:
        with pytest.raises(UnicodeDecodeError):
            read_all(reader)


def test_close_closes_file_it_opened(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_text(HEADER)
    reader = make_reader(str(path))
    assert not reader.is_closed
    reader.close()
    assert reader.is_closed
    assert reader.file.closed


def test_close_does_not_close_supplied_file_object():
    source = StringIO(HEADER)
    reader = make_reader(source)
    reader.close()
    assert reader.is_closed
    assert not source.closed


def test_close_is_idempotent(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_text(HEADER)
    reader = make_reader(str(path))
    reader.close()
    reader.close()
    assert reader.is_closed


def test_context_manager_closes(tmp_path):
    path = tmp_path / 'log.txt'
    path.write_text(HEADER)
    with make_reader(str(path)) as reader:
        pass
    assert reader.is_closed
    assert reader.file.closed


def test_repr_includes_logical_name_and_columns():
    with make_reader(StringIO(HEADER), logical_name='web_log') as reader:
        text = repr(reader)
    assert text.startswith('W3CReader(task=None,logical_name=web_log,')
    assert "column_names=['date', 'time', 'cs-method', 'sc-status']" in text


def test_where_criteria_dict_filters_rows():
    text = HEADER + 'a b GET 200\nc d POST 404\ne f GET 500\n'
    with make_reader(StringIO(text)) as reader:
        rows = [row.as_dict for row in reader.where(criteria_dict={'cs-method': 'GET'})]
    assert [r['date'] for r in rows] == ['a', 'e']
