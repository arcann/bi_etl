"""
Created on Nov 17, 2014

@author: Derek Wood
"""
import string
from datetime import date, timedelta, timezone
from datetime import datetime
from datetime import time
from decimal import Decimal, DecimalException
from typing import Union, Iterable, MutableMapping, Optional


def strip(s: str):
    """
    Python str.strip() except that it handles None values.
    """
    if s is None:
        return None
    else:
        return s.strip()


def str2int(s: str):
    """
    String to integer
    """
    if s is None or s == '':
        return None
    else:
        return int(s.replace(',', ''))


def int2base(n, base):
    valid_digits = string.digits + string.ascii_uppercase
    if base > len(valid_digits):
        raise ValueError(
            f"int2base requires base <= {len(valid_digits)}. {base} will not work"
        )
    if n < 0:
        sign = -1
        n = abs(n)
    elif n == 0:
        return valid_digits[0]
    else:
        sign = 1

    digits = []
    while n:
        digits.append(valid_digits[n % base])
        n = n // base

    if sign < 0:
        digits.append('-')

    digits.reverse()

    return ''.join(digits)


def str2float(s: str):
    """
    String to floating point
    """
    if s is None or s == '':
        return None
    else:
        try:    
            return float(s.replace(',', ''))
        except ValueError as e:
            if s[-1] in ['-', '+']:
                s2 = s[-1] + s[:-1].replace(',', '')
                return float(s2)
            else:
                raise e


def str2float_end_sign(s: str):
    """
    String to integer
    This version is almost 4 times faster than str2float 
    in handling signs at the end of the string.
    """
    if s is None or s == '':
        return None
    else:
        try:    
            if s[-1] in ['-', '+']:
                s2 = s[-1] + s[:-1].replace(',', '')
                return float(s2)
            else:
                return float(s.replace(',', ''))
        except ValueError:
            return float(s.replace(',', ''))


def str2decimal(s: str):
    """
    String to decimal (AKA numeric)
    """
    if s is None or s == '':
        return None
    else:
        try:  
            s = s.replace(',', '')
            return Decimal(s)
        except DecimalException as e:
            if s[-1] in ['-', '+']:
                s2 = s[-1] + s[:-1].replace(',', '')
                try:
                    return Decimal(s2)
                except DecimalException as e:
                    raise ValueError(f"Value {repr(s)} could not be converted to Decimal. {repr(e)}")
            else:
                raise ValueError(f"Value {repr(s)} could not be converted to Decimal. {repr(e)}")


def str2decimal_end_sign(s: str):
    """
    String to decimal (AKA numeric).
    This version is almost 4 times faster than str2decimal
    in handling signs at the end of the string.
    """
    if s is None or s == '':
        return None
    else:
        if s[-1] in ['-', '+']:
            s2 = s[-1] + s[:-1].replace(',', '')
            return Decimal(s2)
        else:
            s = s.replace(',', '')
            return Decimal(s)


def str2date(
        s: str,
        dt_format: str = '%m/%d/%Y',
        ):
    """
    Parse a date (no time) value stored in a string. 
    
    Parameters
    ----------
    s: str
        String value to convert
    dt_format: str
        For format options please see https://docs.python.org/3.5/library/datetime.html#strftime-strptime-behavior
    """
    dt = str2datetime(s, dt_format)
    if dt is not None:
        return date(dt.year, dt.month, dt.day)
    else:
        return None


def str2time(
        s: str,
        dt_format: str = '%H:%M:%S',
        ):
    """
    Parse a time of day value stored in a string. 
    
    Parameters
    ----------
    s: str
        String value to convert
    dt_format: str
        For format options please see
        https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
    """
    tm = str2datetime(s, dt_format)
    if tm is not None:
        return time(
            tm.hour,
            tm.minute,
            tm.second,
            tm.microsecond,
            tm.tzinfo
            )
    else:
        return None


def str2datetime(
        s: str,
        dt_format: Union[str, Iterable[str]] = ('%m/%d/%Y %H:%M:%S', '%m/%d/%Y'),
        ):
    """ 
    Parse a date + time value stored in a string. 
    
    Parameters
    ----------
    s: str
        String value to convert
    dt_format: str
        For format options please see
        https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
    """
    if isinstance(dt_format, str):
        dt_formats = [dt_format]
    else:
        dt_formats = dt_format

    for dt_format in dt_formats:
        try:
            if s is None or s == '':
                return None
            elif '.%f' in dt_format:
                # Fractional seconds are included in format
                # Try as is and then without in case source drops the Fractional seconds when zero
                try:
                    return datetime.strptime(s, dt_format)
                except ValueError as e:
                    msg = str(e)
                    if 'unconverted data remains' in msg:
                        # We might have more digits in the fractional seconds than Python can convert
                        msg, remains = msg.split(':')
                        remains = remains.strip()
                        try:
                            # Make sure what remains is just digits (note this won't work if we have a timezone)
                            int(remains)
                            return datetime.strptime(s[:-1 * len(remains)], dt_format)
                        except ValueError:
                            raise e
                    else:
                        try:
                            return datetime.strptime(s, dt_format.replace('.%f', ''))
                        except ValueError:
                            raise e
            # No fractional seconds included in format
            else:
                return datetime.strptime(s, dt_format)
        except ValueError:
            pass
    raise ValueError(f"{s} does not match any provided formats {dt_formats}")


def round_datetime_ms(
        source_datetime: Optional[datetime],
        digits_to_keep: int,
        ):
    """
    Round a datetime value microseconds to a given number of significant digits.
    """
    if source_datetime is None:
        return None
    new_microseconds = round(source_datetime.microsecond, digits_to_keep-6)
    if new_microseconds == 1000000:
        source_datetime = source_datetime.replace(microsecond=0)
        source_datetime += timedelta(seconds=1)
    else:
        source_datetime = source_datetime.replace(microsecond=new_microseconds)
    return source_datetime


def change_tz(
        source_datetime: Optional[datetime],
        from_tzone,
        to_tzone
        ):
    """
    Change time-zones in dates that have no time-zone info, or incorrect time-zone info
    
    Example from_tzone or to_tzone values: ::
        import pytz

        pytz.utc
        pytz.timezone('US/Eastern')
    
    """
    if source_datetime is not None:
        # Apply our source time zone
        result_datetime = source_datetime.replace(tzinfo=from_tzone)
        # Convert to target time zone
        result_datetime = result_datetime.astimezone(to_tzone)
        # Now we strip off the time zone info so it will match what comes out of Oracle
        result_datetime = result_datetime.replace(tzinfo=None)
        return result_datetime    


def get_date_local(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        local_timezone = datetime.now(timezone.utc).astimezone().tzinfo
        dt = dt.astimezone(local_timezone)
    return dt


def get_date_midnight(dt: datetime) -> datetime:
    dt = get_date_local(dt)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def ensure_datetime(dt: Union[datetime, date]) -> datetime:
    """
    Takes a date or a datetime as input, outputs a datetime
    """
    if isinstance(dt, datetime):
        return dt
    elif isinstance(dt, date):
        return datetime(dt.year, dt.month, dt.day)
    else:
        raise ValueError(f'expected datetime, got {dt}')


def ensure_datetime_dict(
        d: Union[dict, MutableMapping],
        key: str,
        ):
    """
    Takes a dict containing a date or a datetime as input.
    Changes the dict entry to be a datetime
    """
    dt = d[key]
    if isinstance(dt, datetime):
        return
    elif isinstance(dt, date):
        d[key] = datetime(dt.year, dt.month, dt.day)
    else:
        raise ValueError(f'expected datetime for {key}, got {dt}')


def nvl(value, default):
    """
    Pass value through unchanged unless it is NULL (None).
    If it is NULL (None), then return provided default value.
    """
    if (value is None) or (value == ''):
        return default
    else:
        return value


def coalesce(*values):
    for candidate_value in values:
        if candidate_value is not None:
            return candidate_value
    return None


def nullif(v, value_to_null):
    """
    Pass value through unchanged unless it is equal to provided `value_to_null` value. 
    If `v` ==`value_to_null` value then return NULL (None)
    """
    if v == value_to_null:
        return None
    else:
        return v


def default_to_missing(v: str) -> str:
    """
    Same as nvl(v, 'Missing')
    """
    return nvl(v, 'Missing')    


def default_to_invalid(v: str) -> str:
    """
    Same as nvl(v, 'Invalid')
    """
    return nvl(v, 'Invalid')


def default_to_question_mark(v: str) -> str:
    """
    Same as nvl(v, '?')
    """
    return nvl(v, '?')


def default_nines(v: int) -> int:
    """
    Same as nvl(v, -9999)
    """
    return nvl(v, -9999)


def str2bytes_size(str_size: str) -> str:
    """
    Parses a string containing a size in bytes including KB, MB, GB, TB codes
    into an integer with the actual number of bytes (using 1 KB = 1024). 
    """    
    if isinstance(str_size, str):
        str_size = str_size.upper().strip()
        # Trip final B so we can except 10MB or 10M equally
        if str_size[-1] == 'B':
            str_size = str_size[:-1]
            
        # Check for KB
        if str_size[-1] == 'K':
            result = int(str_size[:-1]) * pow(2, 10)
        # Check for MB
        elif str_size[-1] == 'M':
            result = int(str_size[:-1]) * pow(2, 20)
        # Check for GB
        elif str_size[-1] == 'G':
            result = int(str_size[:-1]) * pow(2, 30)
        # Check for TB
        elif str_size[-1] == 'T':
            result = int(str_size[:-1]) * pow(2, 30)
        else:
            result = int(str_size)
    elif str_size is None:
        result = None
    else:
        # return what we were given, just making sure it was an int
        result = int(str_size)
    return result


"""
http://code.activestate.com/recipes/578019/
Bytes-to-human / human-to-bytes converter.
Based on: http://goo.gl/kTQMs
Working with Python 2.x and 3.x.

Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
License: MIT
"""

# see: http://goo.gl/kTQMs
SYMBOLS = {
    'customary'     : ['B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'],
    'customary_ext' : ['byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'],
    'iec'           : ['Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'],
    'iec_ext'       : ['byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'],
}


def bytes2human(
        n: int,
        format_str: str = '%(value).1f %(symbol)s',
        symbols: str = 'customary'
        ) -> str:
    """
    Convert n bytes into a human-readable string based on format_str.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs

      >>> bytes2human(0)
      '0.0 B'
      >>> bytes2human(1)
      '1.0 B'
      >>> bytes2human(1024)
      '1.0 K'
      >>> bytes2human(1048576)
      '1.0 M'
      >>> bytes2human(1099511627776127398123789121)
      '909.5 Y'

      >>> bytes2human(9856, symbols="customary")
      '9.6 K'
      >>> bytes2human(9856, symbols="customary_ext")
      '9.6 kilo'
      >>> bytes2human(9856, symbols="iec")
      '9.6 Ki'
      >>> bytes2human(9856, symbols="iec_ext")
      '9.6 kibi'

      >>> bytes2human(10000, "%(value).1f %(symbol)s/sec")
      '9.8 K/sec'

      >>> # precision can be adjusted by playing with %f operator
      >>> bytes2human(10000, format_str="%(value).5f %(symbol)s")
      '9.76562 K'
    """
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = SYMBOLS[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format_str % dict(symbol=symbol, value=value)
    return format_str % dict(symbol=symbols[0], value=n)


def human2bytes(s: str) -> int:
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.

      >>> human2bytes('0 B')
      0
      >>> human2bytes('1 K')
      1024
      >>> human2bytes('1 M')
      1048576
      >>> human2bytes('1 Gi')
      1073741824
      >>> human2bytes('1 tera')
      1099511627776

      >>> human2bytes('0.5kilo')
      512
      >>> human2bytes('0.1  byte')
      0
      >>> human2bytes('1 k')  # k is an alias for K
      1024
      >>> human2bytes('12 foo')
      Traceback (most recent call last):
          ...
      ValueError: can't interpret '12 foo'
    """
    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for _, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]: 1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])


def replace_tilda(e):
    """
    Used for unicode error to replace invalid ascii with ~

    Apply this with this code

    .. code-block:: python

        codecs.register_error('replace_tilda', replace_tilda)
        ...
        bytes_value = str_value.encode('ascii', errors='replace_tilda')

    See https://docs.python.org/3/library/codecs.html#codecs.register_error
    """
    return u'~', e.start + 1
