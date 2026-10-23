from collections.abc import MutableSet


class CaseInsensitiveSet(MutableSet):
    def __init__(self, iterable=None):
        # Dictionary maps case-folded strings to their original casings
        self._data: dict[str, str] = dict()
        if iterable:
            for item in iterable:
                self._add(item)

    def __contains__(self, value):
        if not isinstance(value, str):
            return False
        return value.casefold() in self._data

    def __iter__(self):
        return iter(self._data.values())

    def __len__(self):
        return len(self._data)

    def _add(self, value):
        """
        Internal method to add a value to the set.

        :param value:
        :return:
        """
        folded = value.casefold()
        if folded not in self._data:
            self._data[folded] = value

    def add(self, value):
        self._add(value)

    def discard(self, value):
        self._data.pop(value.casefold(), None)

    def __repr__(self):
        return f"{self.__class__.__name__}({list(self._data.values())})"


class CaseInsensitiveFrozenSet(CaseInsensitiveSet, frozenset):
    def __init__(self, iterable=None):
        super().__init__(iterable)
        self._frozenset = frozenset(self._data.keys())

    def add(self, value):
        raise NotImplementedError

    def discard(self, value):
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, CaseInsensitiveFrozenSet):
            return self._frozenset == other._frozenset
        return False

    def __hash__(self):
        return hash(self._frozenset)
