"""
Created on Nov 17, 2014

@author: woodd
"""

from collections import namedtuple
from datetime import date
from datetime import datetime
from datetime import time
from decimal import Decimal, InvalidOperation

Transformation = namedtuple(typename='Transformation', field_names=['column', 'conversion'])


class Conversion(object):
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs


def str2int(s):
    """
    String to integer
    """
    if s == None or s == '':
        return None
    else:
        return int(s.replace(',', ''))


def str2float(s):
    """
    String to floating point
    """
    if s is None or s == '':
        return None
    else:
        try:    
            return float(s.replace(',', ''))
        except ValueError as e:
            if s[-1] in ['-','+']:
                s2 = s[-1]+ s[:-1].replace(',','')
                return float(s2)
            else:
                raise e


def str2float_end_sign(s):
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
                s2 = s[-1] + s[:-1].replace(',','')
                return float(s2)
            else:
                return float(s.replace(',', ''))
        except ValueError:
            return float(s.replace(',', ''))


def str2decimal(s):
    """
    String to decimal (AKA numeric)
    """
    if s is None or s == '':
        return None
    else:
        try:  
            s = s.replace(',', '')
            return Decimal(s)
        except InvalidOperation as e:
            if s[-1] in ['-', '+']:
                s2 = s[-1]+ s[:-1].replace(',', '')
                return Decimal(s2)
            else:
                raise e


def str2decimal_end_sign(s):
    """
    String to decimal (AKA numeric).
    This version is almost 4 times faster than tr2decimal 
    in handling signs at the end of the string.
    """
    if s is None or s == '':
        return None
    else:
        if s[-1] in ['-','+']:
            s2 = s[-1]+ s[:-1].replace(',','')
            return Decimal(s2)
        else:
            s = s.replace(',', '')
            return Decimal(s)


def str2date(s, dt_format='%m/%d/%Y'):
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


def str2time(s, dt_format='%H:%M:%S'):
    """
    Parse a time of day value stored in a string. 
    
    Parameters
    ----------
    s: str
        String value to convert
    dt_format: str
        For format options please see https://docs.python.org/3.5/library/datetime.html#strftime-strptime-behavior
    """
    tm = str2datetime(s, dt_format)
    if tm is not None:
        return time(tm.hour, 
                    tm.minute, 
                    tm.second,
                    tm.microsecond,
                    tm.tzinfo
                    )
    else:
        return None


def str2datetime(s, dt_format='%m/%d/%Y %H:%M:%S'):
    """ 
    Parse a date + time value stored in a string. 
    
    Parameters
    ----------
    s: str
        String value to convert
    dt_format: str
        For format options please see https://docs.python.org/3.5/library/datetime.html#strftime-strptime-behavior
    """
    # TODO: Warn callers of deprecated  00000000 to None conversion. They should use nullif instead
    if s is None or s == '' or s == '00000000':
        return None
    else:
        return datetime.strptime(s, dt_format)


def change_tz(source_datetime, from_tzone, to_tzone):
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


def nvl(value, default):
    """
    Pass value through unchanged unless it is NULL (None).
    If it is NULL (None), then return provided default value.
    """
    if (value is None) or (value == ''):
        return default
    else:
        return value
    

def nullif(v, value_to_null):
    """
    Pass value through unchanged unless it is equal to provided `value_to_null` value. 
    If `v` ==`value_to_null` value then return NULL (None)
    """
    if v == value_to_null:
        return None
    else:
        return v

def defaultMissing(v):
    """
    Same as nvl(v, 'Missing')
    """
    return nvl(v, 'Missing')    


def defaultInvalid(v):
    """
    Same as nvl(v, 'Invalid')
    """
    return nvl(v, 'Invalid')


def defaultQuestionmark(v):
    """
    Same as nvl(v, '?')
    """
    return nvl(v, '?')


def defaultNines(v):
    """
    Same as nvl(v, -9999)
    """
    return nvl(v, -9999)


def str2bytes_size(str_size):
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
            result = int(str_size[:-1]) * pow(2,30)
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
    'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
}


def bytes2human(n, format_str='%(value).1f %(symbol)s', symbols='customary'):
    """
    Convert n bytes into a human readable string based on format_str.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs

      >>> bytes2human(0)
      '0.0 B'
      >>> bytes2human(0.9)
      '0.0 B'
      >>> bytes2human(1)
      '1.0 B'
      >>> bytes2human(1.9)
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
            return format_str% dict(symbol=symbols[0], value=value)
    return format_str % dict(symbol=symbols[0], value=n)


def human2bytes(s):
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
    """
    return u'~', e.start + 1
