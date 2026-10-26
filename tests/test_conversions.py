import codecs
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, DecimalException

import pytest

from bi_etl import conversions


class TestStrip:
    def test_none(self):
        assert conversions.strip(None) is None

    @pytest.mark.parametrize('value, expected', [('  a b \t', 'a b'), ('', ''), ('x', 'x')])
    def test_strips_whitespace(self, value, expected):
        assert conversions.strip(value) == expected


class TestStr2Int:
    @pytest.mark.parametrize('value, expected', [
        ('123', 123), ('1,234,567', 1234567), ('-5', -5), ('0', 0),
    ])
    def test_valid(self, value, expected):
        assert conversions.str2int(value) == expected

    @pytest.mark.parametrize('value', [None, ''])
    def test_null_like(self, value):
        assert conversions.str2int(value) is None

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            conversions.str2int('abc')


class TestInt2Base:
    @pytest.mark.parametrize('n, base, expected', [
        (0, 2, '0'),
        (5, 2, '101'),
        (255, 16, 'FF'),
        (35, 36, 'Z'),
        (36, 36, '10'),
        (-5, 2, '-101'),
        (10, 10, '10'),
    ])
    def test_conversion(self, n, base, expected):
        assert conversions.int2base(n, base) == expected

    def test_base_too_large_raises(self):
        with pytest.raises(ValueError, match='int2base requires base'):
            conversions.int2base(10, 37)


class TestStr2Float:
    @pytest.mark.parametrize('func', [conversions.str2float, conversions.str2float_end_sign])
    @pytest.mark.parametrize('value, expected', [
        ('1.5', 1.5),
        ('1,234.5', 1234.5),
        ('-2.25', -2.25),
        ('5-', -5.0),
        ('5+', 5.0),
        ('1,234.5-', -1234.5),
    ])
    def test_valid(self, func, value, expected):
        assert func(value) == expected

    @pytest.mark.parametrize('func', [conversions.str2float, conversions.str2float_end_sign])
    @pytest.mark.parametrize('value', [None, ''])
    def test_null_like(self, func, value):
        assert func(value) is None

    @pytest.mark.parametrize('func', [conversions.str2float, conversions.str2float_end_sign])
    @pytest.mark.parametrize('value', ['abc', 'abc-'])
    def test_invalid_raises(self, func, value):
        with pytest.raises(ValueError):
            func(value)


class TestStr2Decimal:
    @pytest.mark.parametrize('func', [conversions.str2decimal, conversions.str2decimal_end_sign])
    @pytest.mark.parametrize('value, expected', [
        ('1.50', Decimal('1.50')),
        ('1,234.50', Decimal('1234.50')),
        ('-7', Decimal('-7')),
        ('5-', Decimal('-5')),
        ('5+', Decimal('5')),
        ('1,234.5-', Decimal('-1234.5')),
    ])
    def test_valid(self, func, value, expected):
        result = func(value)
        assert result == expected
        assert result.as_tuple() == expected.as_tuple()

    @pytest.mark.parametrize('func', [conversions.str2decimal, conversions.str2decimal_end_sign])
    @pytest.mark.parametrize('value', [None, ''])
    def test_null_like(self, func, value):
        assert func(value) is None

    @pytest.mark.parametrize('value', ['abc', 'abc-'])
    def test_str2decimal_invalid_raises_value_error(self, value):
        with pytest.raises(ValueError, match='could not be converted to Decimal'):
            conversions.str2decimal(value)

    @pytest.mark.parametrize('value', ['abc', 'abc-'])
    def test_str2decimal_end_sign_invalid_raises(self, value):
        with pytest.raises(DecimalException):
            conversions.str2decimal_end_sign(value)


class TestStr2Datetime:
    def test_default_formats_with_time(self):
        assert conversions.str2datetime('01/02/2024 03:04:05') == datetime(2024, 1, 2, 3, 4, 5)

    def test_default_formats_fall_back_to_date_only(self):
        assert conversions.str2datetime('01/02/2024') == datetime(2024, 1, 2)

    def test_single_format_string(self):
        assert conversions.str2datetime('2024-01-02', '%Y-%m-%d') == datetime(2024, 1, 2)

    def test_list_of_formats(self):
        formats = ['%Y-%m-%d', '%d.%m.%Y']
        assert conversions.str2datetime('02.01.2024', formats) == datetime(2024, 1, 2)

    @pytest.mark.parametrize('value', [None, ''])
    def test_null_like(self, value):
        assert conversions.str2datetime(value) is None

    def test_no_matching_format_raises(self):
        with pytest.raises(ValueError, match='does not match any provided formats'):
            conversions.str2datetime('not a date')

    FRACTIONAL = '%Y-%m-%d %H:%M:%S.%f'

    def test_fractional_seconds(self):
        result = conversions.str2datetime('2024-01-02 03:04:05.123456', self.FRACTIONAL)
        assert result == datetime(2024, 1, 2, 3, 4, 5, 123456)

    def test_fractional_seconds_missing_when_zero(self):
        result = conversions.str2datetime('2024-01-02 03:04:05', self.FRACTIONAL)
        assert result == datetime(2024, 1, 2, 3, 4, 5)

    @pytest.mark.parametrize('value', [
        '2024-01-02 03:04:05.1234567',
        '2024-01-02 03:04:05.123456789',
    ])
    def test_excess_fractional_digits_truncated(self, value):
        result = conversions.str2datetime(value, self.FRACTIONAL)
        assert result == datetime(2024, 1, 2, 3, 4, 5, 123456)

    def test_fractional_with_trailing_non_digits_raises(self):
        with pytest.raises(ValueError):
            conversions.str2datetime('2024-01-02 03:04:05.123456Z', self.FRACTIONAL)

    def test_fractional_format_garbage_raises(self):
        with pytest.raises(ValueError, match='does not match any provided formats'):
            conversions.str2datetime('garbage', self.FRACTIONAL)


class TestStr2Date:
    def test_default_format(self):
        result = conversions.str2date('01/02/2024')
        assert result == date(2024, 1, 2)
        assert type(result) is date

    def test_custom_format(self):
        assert conversions.str2date('2024-03-04', '%Y-%m-%d') == date(2024, 3, 4)

    @pytest.mark.parametrize('value', [None, ''])
    def test_null_like(self, value):
        assert conversions.str2date(value) is None

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            conversions.str2date('2024-03-04')


class TestStr2Time:
    def test_default_format(self):
        assert conversions.str2time('13:45:10') == time(13, 45, 10)

    def test_custom_format(self):
        assert conversions.str2time('01:02 PM', '%I:%M %p') == time(13, 2)

    @pytest.mark.parametrize('value', [None, ''])
    def test_null_like(self, value):
        assert conversions.str2time(value) is None

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            conversions.str2time('25:00:00')


class TestRoundDatetimeMs:
    def test_none(self):
        assert conversions.round_datetime_ms(None, 3) is None

    def test_round_down_to_milliseconds(self):
        dt = datetime(2024, 1, 2, 3, 4, 5, 123456)
        assert conversions.round_datetime_ms(dt, 3) == datetime(2024, 1, 2, 3, 4, 5, 123000)

    def test_round_up_to_milliseconds(self):
        dt = datetime(2024, 1, 2, 3, 4, 5, 123600)
        assert conversions.round_datetime_ms(dt, 3) == datetime(2024, 1, 2, 3, 4, 5, 124000)

    def test_six_digits_unchanged(self):
        dt = datetime(2024, 1, 2, 3, 4, 5, 123456)
        assert conversions.round_datetime_ms(dt, 6) == dt

    def test_rollover_carries_into_seconds(self):
        dt = datetime(2024, 1, 2, 3, 4, 5, 999600)
        assert conversions.round_datetime_ms(dt, 3) == datetime(2024, 1, 2, 3, 4, 6)

    def test_rollover_carries_across_day(self):
        dt = datetime(2024, 1, 1, 23, 59, 59, 999600)
        assert conversions.round_datetime_ms(dt, 3) == datetime(2024, 1, 2, 0, 0, 0)

    def test_zero_digits_rounds_to_seconds(self):
        dt = datetime(2024, 1, 2, 3, 4, 5, 600000)
        assert conversions.round_datetime_ms(dt, 0) == datetime(2024, 1, 2, 3, 4, 6)


class TestChangeTz:
    def test_none(self):
        assert conversions.change_tz(None, timezone.utc, timezone.utc) is None

    def test_utc_to_offset_zone(self):
        eastern = timezone(timedelta(hours=-5))
        result = conversions.change_tz(datetime(2024, 1, 1, 12, 0), timezone.utc, eastern)
        assert result == datetime(2024, 1, 1, 7, 0)
        assert result.tzinfo is None

    def test_offset_zone_to_utc_crosses_day(self):
        eastern = timezone(timedelta(hours=-5))
        result = conversions.change_tz(datetime(2024, 1, 1, 22, 0), eastern, timezone.utc)
        assert result == datetime(2024, 1, 2, 3, 0)

    def test_existing_tzinfo_is_replaced_not_converted(self):
        plus_two = timezone(timedelta(hours=2))
        source = datetime(2024, 1, 1, 12, 0, tzinfo=plus_two)
        result = conversions.change_tz(source, timezone.utc, timezone.utc)
        assert result == datetime(2024, 1, 1, 12, 0)


class TestLocalAndMidnight:
    def test_get_date_local_naive_unchanged(self):
        dt = datetime(2024, 1, 2, 3, 4, 5)
        assert conversions.get_date_local(dt) is dt

    def test_get_date_local_aware_is_same_instant(self):
        dt = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
        result = conversions.get_date_local(dt)
        assert result == dt
        assert result.tzinfo is not None

    def test_get_date_midnight_naive(self):
        dt = datetime(2024, 1, 2, 13, 45, 10, 5)
        assert conversions.get_date_midnight(dt) == datetime(2024, 1, 2)

    def test_get_date_midnight_aware_keeps_tzinfo(self):
        dt = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
        result = conversions.get_date_midnight(dt)
        assert result.tzinfo is not None
        assert (result.hour, result.minute, result.second, result.microsecond) == (0, 0, 0, 0)
        assert result == conversions.get_date_local(dt).replace(hour=0, minute=0)


class TestEnsureDatetime:
    def test_datetime_returned_as_is(self):
        dt = datetime(2024, 1, 2, 3, 4, 5)
        assert conversions.ensure_datetime(dt) is dt

    def test_date_converted(self):
        result = conversions.ensure_datetime(date(2024, 1, 2))
        assert result == datetime(2024, 1, 2)
        assert isinstance(result, datetime)

    @pytest.mark.parametrize('value', ['2024-01-02', None, 5])
    def test_other_types_raise(self, value):
        with pytest.raises(ValueError, match='expected datetime'):
            conversions.ensure_datetime(value)


class TestEnsureDatetimeDict:
    def test_date_converted_in_place(self):
        d = {'when': date(2024, 1, 2)}
        assert conversions.ensure_datetime_dict(d, 'when') is None
        assert d['when'] == datetime(2024, 1, 2)
        assert isinstance(d['when'], datetime)

    def test_datetime_left_alone(self):
        dt = datetime(2024, 1, 2, 3, 4, 5)
        d = {'when': dt}
        conversions.ensure_datetime_dict(d, 'when')
        assert d['when'] is dt

    def test_other_values_raise(self):
        with pytest.raises(ValueError, match="expected datetime for when"):
            conversions.ensure_datetime_dict({'when': 'x'}, 'when')

    def test_missing_key_raises(self):
        with pytest.raises(KeyError):
            conversions.ensure_datetime_dict({}, 'when')


class TestNullHandling:
    @pytest.mark.parametrize('value, expected', [
        (None, 'dflt'), ('', 'dflt'), ('x', 'x'), (0, 0), (False, False),
    ])
    def test_nvl(self, value, expected):
        assert conversions.nvl(value, 'dflt') == expected

    @pytest.mark.parametrize('values, expected', [
        ((None, None, 3, 4), 3),
        ((None, 0, 3), 0),
        (('', 'a'), ''),
        ((None, None), None),
        ((), None),
    ])
    def test_coalesce(self, values, expected):
        assert conversions.coalesce(*values) == expected

    @pytest.mark.parametrize('value, to_null, expected', [
        ('x', 'x', None),
        ('y', 'x', 'y'),
        (-9999, -9999, None),
        (0, -9999, 0),
        (None, 'x', None),
    ])
    def test_nullif(self, value, to_null, expected):
        assert conversions.nullif(value, to_null) == expected

    @pytest.mark.parametrize('func, default', [
        (conversions.default_to_missing, 'Missing'),
        (conversions.default_to_invalid, 'Invalid'),
        (conversions.default_to_question_mark, '?'),
        (conversions.default_nines, -9999),
    ])
    def test_default_helpers(self, func, default):
        assert func(None) == default
        assert func('') == default

    @pytest.mark.parametrize('func, value', [
        (conversions.default_to_missing, 'abc'),
        (conversions.default_to_invalid, 'abc'),
        (conversions.default_to_question_mark, 'abc'),
        (conversions.default_nines, 42),
    ])
    def test_default_helpers_pass_through(self, func, value):
        assert func(value) == value


class TestStr2BytesSize:
    @pytest.mark.parametrize('value, expected', [
        ('10', 10),
        ('1K', 1024),
        ('1KB', 1024),
        ('2m', 2 * 2 ** 20),
        ('5MB', 5 * 2 ** 20),
        (' 3 gb ', 3 * 2 ** 30),
        ('1G', 2 ** 30),
        (42, 42),
    ])
    def test_valid(self, value, expected):
        assert conversions.str2bytes_size(value) == expected

    def test_none(self):
        assert conversions.str2bytes_size(None) is None

    def test_terabytes(self):
        assert conversions.str2bytes_size('1T') == 2 ** 40

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            conversions.str2bytes_size('abc')


class TestBytes2Human:
    @pytest.mark.parametrize('n, expected', [
        (0, '0.0 B'),
        (1, '1.0 B'),
        (1023, '1023.0 B'),
        (1024, '1.0 K'),
        (9856, '9.6 K'),
        (1048576, '1.0 M'),
        (1099511627776127398123789121, '909.5 Y'),
    ])
    def test_customary(self, n, expected):
        assert conversions.bytes2human(n) == expected

    @pytest.mark.parametrize('symbols, expected', [
        ('customary', '9.6 K'),
        ('customary_ext', '9.6 kilo'),
        ('iec', '9.6 Ki'),
        ('iec_ext', '9.6 kibi'),
    ])
    def test_symbol_sets(self, symbols, expected):
        assert conversions.bytes2human(9856, symbols=symbols) == expected

    def test_custom_format(self):
        assert conversions.bytes2human(10000, '%(value).1f %(symbol)s/sec') == '9.8 K/sec'
        assert conversions.bytes2human(10000, format_str='%(value).5f %(symbol)s') == '9.76562 K'

    def test_negative_raises(self):
        with pytest.raises(ValueError, match='n < 0'):
            conversions.bytes2human(-1)

    def test_unknown_symbol_set_raises(self):
        with pytest.raises(KeyError):
            conversions.bytes2human(1, symbols='bogus')


class TestHuman2Bytes:
    @pytest.mark.parametrize('value, expected', [
        ('0 B', 0),
        ('1 K', 1024),
        ('1 M', 1048576),
        ('1 Gi', 1073741824),
        ('1 tera', 1099511627776),
        ('0.5kilo', 512),
        ('0.1  byte', 0),
        ('1 k', 1024),
        ('2 Mi', 2 * 2 ** 20),
    ])
    def test_valid(self, value, expected):
        assert conversions.human2bytes(value) == expected

    def test_unrecognized_unit_raises(self):
        with pytest.raises(ValueError, match="can't interpret '12 foo'"):
            conversions.human2bytes('12 foo')

    def test_round_trip_powers_of_two(self):
        for n in (0, 1024, 2 ** 20, 5 * 2 ** 30):
            assert conversions.human2bytes(conversions.bytes2human(n)) == n


class TestReplaceTilda:
    def test_returns_tilde_and_next_position(self):
        error = UnicodeEncodeError('ascii', 'café', 3, 4, 'ordinal not in range(128)')
        assert conversions.replace_tilda(error) == ('~', 4)

    def test_registered_as_codec_error_handler(self):
        codecs.register_error('replace_tilda', conversions.replace_tilda)
        assert 'café'.encode('ascii', errors='replace_tilda') == b'caf~'
        assert 'éü!'.encode('ascii', errors='replace_tilda') == b'~~!'