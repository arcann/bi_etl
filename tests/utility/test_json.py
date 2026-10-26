import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest
from pydantic import BaseModel

from bi_etl.utility.json import OurJSONEncoder, json_default, json_dumps


class Color(Enum):
    RED = 'r'
    ONE = 1


class Point(BaseModel):
    x: int
    y: int


class TestJsonDefault:
    def test_decimal(self):
        assert json_default(Decimal('1.230')) == '1.230'

    def test_path(self):
        p = Path('some') / 'file.txt'
        assert json_default(p) == str(p)

    @pytest.mark.parametrize('pure_path', [PurePosixPath('/a/b'), PureWindowsPath('C:/a/b')])
    def test_pure_path(self, pure_path):
        assert json_default(pure_path) == str(pure_path)

    def test_datetime(self):
        assert json_default(datetime(2024, 1, 2, 3, 4, 5)) == '2024-01-02T03:04:05'

    def test_datetime_with_microseconds(self):
        assert json_default(datetime(2024, 1, 2, 3, 4, 5, 6)) == '2024-01-02T03:04:05.000006'

    def test_type(self):
        assert json_default(int) == str(int)

    def test_pydantic_model_returns_json_string(self):
        assert json_default(Point(x=1, y=2)) == '{"x":1,"y":2}'

    @pytest.mark.parametrize('member, expected', [(Color.RED, 'r'), (Color.ONE, 1)])
    def test_enum_returns_value(self, member, expected):
        assert json_default(member) == expected

    @pytest.mark.parametrize('obj', [object(), {1, 2}, date(2024, 1, 1)])
    def test_unsupported_type_raises(self, obj, capsys):
        with pytest.raises(TypeError, match='No handling for'):
            json_default(obj)
        assert 'No handling for' in capsys.readouterr().out


class TestOurJSONEncoder:
    def test_dumps_with_encoder(self):
        data = {'d': Decimal('1.5'), 'when': datetime(2024, 1, 2), 'color': Color.RED}
        result = json.loads(json.dumps(data, cls=OurJSONEncoder))
        assert result == {'d': '1.5', 'when': '2024-01-02T00:00:00', 'color': 'r'}

    def test_native_types_unchanged(self):
        data = {'a': 1, 'b': [1.5, None, True], 'c': 'text'}
        assert json.loads(json.dumps(data, cls=OurJSONEncoder)) == data

    def test_unsupported_type_raises(self):
        with pytest.raises(TypeError):
            json.dumps({'x': object()}, cls=OurJSONEncoder)


class TestJsonDumps:
    def test_none_returns_none(self):
        assert json_dumps(None) is None

    def test_simple_dict(self):
        assert json_dumps({'a': 1}) == '{"a": 1}'

    def test_special_types(self):
        result = json.loads(json_dumps([Decimal('2.50'), Path('x'), Color.ONE]))
        assert result == ['2.50', str(Path('x')), 1]

    def test_nested_pydantic_model_is_embedded_as_string(self):
        result = json.loads(json_dumps({'p': Point(x=3, y=4)}))
        assert result == {'p': '{"x":3,"y":4}'}

    def test_kwargs_passed_through(self):
        assert json_dumps({'b': 1, 'a': 2}, sort_keys=True, separators=(',', ':')) == '{"a":2,"b":1}'

    def test_falsy_values_are_serialized(self):
        assert json_dumps(0) == '0'
        assert json_dumps([]) == '[]'
        assert json_dumps('') == '""'

    def test_unsupported_type_raises(self):
        with pytest.raises(TypeError):
            json_dumps({'x': object()})
