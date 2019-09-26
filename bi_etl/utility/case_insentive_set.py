from collections.abc import MutableSet


class CaseInsentiveSet(MutableSet):
    """
    Implements a case-insensitive set while still preserving the case of the first instance of each item.
    """
    def __init__(self, values):
        self._values = {}
        for v in values:
            self.add(v)

    def __repr__(self):
        return f'<{type(self).__name__}{tuple(self._values.values())} @ {id(self):x}>'

    def __contains__(self, value: str):
        return value.casefold() in self._values

    def __iter__(self):
        return iter(self._values.values())

    def __len__(self):
        return len(self._values)

    def add(self, value: str):
        value_key = value.casefold()
        if value_key not in self._values:
            self._values[value_key] = value

    def discard(self, value: str):
        try:
            del self._values[value.casefold()]
        except KeyError:
            pass
