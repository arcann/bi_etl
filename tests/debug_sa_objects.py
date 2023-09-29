"""
Created on Mar 27, 2015

@author: Derek Wood
"""
import operator

import sqlalchemy
from sqlalchemy.exc import InvalidRequestError


def rowproxy_reconstructor(cls, state):
    obj = cls.__new__(cls)
    obj.__setstate__(state)
    return obj


class BaseRowProxy(object):
    __slots__ = ('_parent', '_row', '_processors', '_keymap')

    def __init__(self, parent, row, processors, keymap):
        """RowProxy objects are constructed by ResultProxy objects."""

        self._parent = parent
        self._row = row
        self._processors = processors
        self._keymap = keymap

    def __reduce__(self):
        return (rowproxy_reconstructor,
                (self.__class__, self.__getstate__()))

    def values(self):
        """Return the values represented by this RowProxy as a list."""
        return list(self)

    def __iter__(self):
        for processor, value in zip(self._processors, self._row):
            if processor is None:
                yield value
            else:
                yield processor(value)

    def __len__(self):
        return len(self._row)

    def __getitem__(self, key):
        try:
            processor, _, index = self._keymap[key]
        except KeyError:
            processor, _, index = self._parent._key_fallback(key)
        except TypeError:
            if isinstance(key, slice):
                val_list = []
                for processor, value in zip(self._processors[key],
                                            self._row[key]):
                    if processor is None:
                        val_list.append(value)
                    else:
                        val_list.append(processor(value))
                return tuple(val_list)
            else:
                raise
        if index is None:
            raise sqlalchemy.exc.InvalidRequestError(
                "Ambiguous column name '%s' in result set! "
                "try 'use_labels' option on select statement." % key)
        if processor is not None:
            return processor(self._row[index])
        else:
            return self._row[index]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e.args[0])


# noinspection PyProtectedMember
class RowProxy(BaseRowProxy):
    """Proxy values from a single cursor row.

    Mostly follows "ordered dictionary" behavior, mapping result
    values to the string-based column name, the integer position of
    the result in the row, as well as Column instances which can be
    mapped to the original Columns that produced this result set (for
    results that correspond to constructed SQL expressions).
    """
    __slots__ = ()

    def __contains__(self, key):
        return self._parent._has_key(self._row, key)

    def __getstate__(self):
        return {
            '_parent': self._parent,
            '_row': tuple(self)
        }

    def __setstate__(self, state):
        self._parent = parent = state['_parent']
        self._row = state['_row']
        self._processors = parent._processors
        self._keymap = parent._keymap

    __hash__ = None

    def _op(self, other, op):
        return op(tuple(self), tuple(other)) \
            if isinstance(other, RowProxy) \
            else op(tuple(self), other)

    def __lt__(self, other):
        return self._op(other, operator.lt)

    def __le__(self, other):
        return self._op(other, operator.le)

    def __ge__(self, other):
        return self._op(other, operator.ge)

    def __gt__(self, other):
        return self._op(other, operator.gt)

    def __eq__(self, other):
        return self._op(other, operator.eq)

    def __ne__(self, other):
        return self._op(other, operator.ne)

    def __repr__(self):
        return repr(tuple(self))

    def has_key(self, key):
        """Return True if this RowProxy contains the given key."""

        return self._parent._has_key(self._row, key)

    def items(self):
        """Return a list of tuples, each tuple containing a key/value pair."""
        # TODO: no coverage here
        return [(key, self[key]) for key in list(self.keys())]

    def keys(self):
        """Return the list of keys as strings represented by this RowProxy."""

        return self._parent.keys


def mock_engine():
    buffer = []
    
    def executor(sql, *a, **kw):
        buffer.append(sql)
    engine = sqlalchemy.create_engine('ORACLE://', strategy='mock', executor=executor)
    assert not hasattr(engine, 'mock')
    engine.mock = buffer
    return engine
