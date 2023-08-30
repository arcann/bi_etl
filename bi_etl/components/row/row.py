# -*- coding: utf-8 -*-
"""
Created on Sep 17, 2014

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import collections.abc
import dataclasses
import warnings
from collections import namedtuple
from decimal import Decimal
from typing import *
from typing import Union, List, Iterable

from pydantic import BaseModel
from sqlalchemy.sql.schema import Column

from bi_etl.components.row.column_difference import ColumnDifference
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.row.row_status import RowStatus
from bi_etl.utility import dict_to_str


class Row(MutableMapping):
    """
    Replacement for core SQL Alchemy, CSV or other dictionary based rows.
    Handles column names that are SQL Alchemy column objects.
    Keeps order of the columns (see columns_in_order)
    """

    # Using slots to fix the attributes to just these. This allows CPython to create Row objects 10% faster
    __slots__ = [
        '_data_values',
        'iteration_header',
        'status',
    ]
    NUMERIC_TYPES = {int, float, Decimal}
    RAISE_ON_NOT_EXIST_NAME = 'raise_on_not_exist'
    RowIterationHeader_Class = RowIterationHeader
    # For performance with the Column to str conversion we keep a cache of converted values

    def __init__(self,
                 iteration_header: RowIterationHeader,
                 data: Union[MutableMapping, list, namedtuple, None] = None,
                 status: Optional[RowStatus] = None,
                 allocate_space: bool = True):
        """
        Note: If data is passed here, it uses :py:meth:`bi_etl.components.row.row.Row.update` to map the data
        into the columns.  That is nicely automatic, but slower since it has to try various
        ways to read the data object.

        Fastest way would be to not pass any data values, and follow with a call to one of:

        * :py:meth:`bi_etl.components.row.row.Row.update_from_namedtuple`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_dict`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_row_proxy`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_tuples`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_dataclass`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_pydantic`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_values`

        """
        # Whatever we store here we need to either store on disk for a lookup,
        # or have a way of retrieving in __setstate__
        super().__init__()
        # We need to accept None for iteration_header for shelve to be efficient
        self._data_values = list()
        if isinstance(iteration_header, int):
            self.iteration_header = self.RowIterationHeader_Class.get_by_id(iteration_header)
            """
            The :py:class:`bi_etl.components.row.row_iteration_header.RowIterationHeader` instance that
            provides a shared definition of columns across many Row instances.

            NOTE: Changes to the columns, such as adding a new column, will replace the iteration_header
            of this Row.  If two or more Row's get the same change, they will all share the same new
            RowIterationHeader instance as their iteration_header value.
            """

        elif isinstance(iteration_header, tuple):
            self.iteration_header = self.RowIterationHeader_Class.get_by_process_and_id(iteration_header)
        else:
            assert isinstance(iteration_header, self.RowIterationHeader_Class), \
                f"First argument to Row needs to be RowIterationHeader type, got {type(iteration_header)}"
            self.iteration_header = iteration_header
        self.iteration_header.add_row(self)
        if allocate_space:
            self._extend_to_size(len(self.iteration_header.columns_in_order))
        self.status = status

        # Populate our data
        if data is not None:
            self.update(data)

    def __reduce__(self):
        # TODO: Experiment with different formats for performance and compactness
        # 91 bytes using pickle.HIGHEST_PROTOCOL, 86 bytes in test using default protocol
        status_value = None
        if self.status is not None:
            if isinstance(self.status, RowStatus):
                status_value = self.status.value
            else:
                status_value = self.status
        return (
            # A callable object that will be called to create the initial version of the object.
            self.__class__,

            # A tuple of arguments for the callable object.
            # An empty tuple must be given if the callable does not accept any argument
            (
                self.iteration_header.get_cross_process_iteration_header(),
                self._data_values,
                status_value
            ),
            # Optionally, the object’s state, which will be passed to the object’s __setstate__() method
            # as previously described.
            # If the object has no such method then, the value must be a dictionary, and it will be
            # added to the object’s __dict__ attribute.
            None,

            # Optionally, an iterator (and not a sequence) yielding successive items.
            # These items will be appended to the object either using obj.append(item) or,
            # in batch, using obj.extend(list_of_items).

            # Optionally, an iterator (not a sequence) yielding successive key-value pairs.
            # These items will be stored to the object using obj[key] = value

            # PROTOCOL 5+ only
            # Optionally, a callable with a (obj, state) signature.
            # This callable allows the user to programmatically control
            # the state-updating behavior of a specific object,
            # instead of using obj’s static __setstate__() method.
            # If not None, this callable will have priority over obj’s __setstate__().
        )

    def __reduce_v1__(self):
        # TODO: Experiment with different formats for performance and compactness
        # 114 bytes in test
        status_value = None
        if self.status is not None:
            status_value = self.status.value
        outgoing_dict = {
            's': status_value,
            'v': self._data_values,
        }
        return (self.__class__,
                # A tuple of arguments for the callable object.
                (self.iteration_header.iteration_id,),
                # State to be passed to setstate
                outgoing_dict,
                )

    def __setstate_v1__(self, incoming_dict):
        if incoming_dict['s'] is not None:
            self.status = RowStatus(incoming_dict['s'])
        else:
            self.status = None
        # Restore column values
        self._data_values = incoming_dict['v']

    def update_from_namedtuple(self, source_data: namedtuple):
        """
        Update the row values from a ``namedtuple`` instance.
        Adds columns for any new names found.
        """
        # noinspection PyProtectedMember
        for column_specifier, value in zip(source_data._fields, source_data):
            column_name = self.iteration_header.get_column_name(column_specifier)
            self._raw_setitem(column_name, value)

    def update_from_dict(self, source_dict: dict):
        """
        Update the row values from a ``dict`` instance.
        Adds columns for any new names found.
        """
        for column_specifier, value in source_dict.items():
            column_name = self.iteration_header.get_column_name(column_specifier)
            self._raw_setitem(column_name, value)

    def update_from_row_proxy(self, source_row: Row):
        """
        Update the row values from a SQL Alchemy result row instance.
        Adds columns for any new names found.
        """
        for column_specifier, value in source_row.items():
            column_name = self.iteration_header.get_column_name(column_specifier)
            self._raw_setitem(column_name, value)

    def update_from_tuples(self, tuples_list: List[tuple]):
        """
        Update the row values from a ``list`` of ``tuples``.

        Each tuple should have 2 values:
          1. Column name
          2. Column value

        Adds columns for any new names found.
        """
        for column_specifier, value in tuples_list:
            column_name = self.iteration_header.get_column_name(column_specifier)
            self._raw_setitem(column_name, value)

    def update_from_dataclass(self, dataclass_inst):
        """
        Update the row values from a ``dataclass`` instance.
        Adds columns for any new names found.
        """
        self.update_from_dict(dataclass_inst.__dict__)

    def update_from_pydantic(self, pydantic_inst: BaseModel):
        """
        Update the row values from a ``pydantic`` instance of ``BaseModel``.
        Adds columns for any new names found.
        """
        # Internally pydantic __iter__ uses __dict__ but is a bit more complex
        # So going straight to __dict__ is faster
        self.update_from_dict(pydantic_inst.__dict__)

    def update_from_values(self, values_list: list):
        """
        Update the row from a list of values.
        The length of the list should be at least as long as the
        number of columns (un-filled columns will be null).
        Extra values past the number of columns will be discarded.
        """
        header_col_cnt = len(self.columns_in_order)
        self._data_values = values_list[:header_col_cnt]
        dv_col_cnt = len(self._data_values)
        if dv_col_cnt < header_col_cnt:
            self._data_values.extend([None] * (header_col_cnt - dv_col_cnt))

    def update(self, *args, **key_word_arguments):
        """
        Update the row values from a ``dict`` instance.
        Adds columns for any new names found.

        NOTE: This method is easy (nicely automatic) to use but slow
        since it has to try various ways to read the data container object.

        Consider using the appropriate one of the more specific update methods
        based on the source data container.

        * :py:meth:`bi_etl.components.row.row.Row.update_from_namedtuple`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_dict`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_row_proxy`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_tuples`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_dataclass`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_pydantic`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_values`
        """
        if len(key_word_arguments) > 0:
            self.update_from_dict(key_word_arguments)

        for source_data in args:
            try:
                if hasattr(source_data, '_fields'):
                    self.update_from_namedtuple(source_data)
                else:
                    # Is a dict
                    self.update_from_dict(source_data)
            except AttributeError as e:
                # Not a dict or sqlalchemy Row
                if dataclasses.is_dataclass(source_data):
                    self.update_from_dataclass(source_data)
                elif hasattr(source_data, '__iter__') and not isinstance(source_data, str):
                    try:
                        source_data = list(source_data)
                        if len(source_data) > 0:
                            # List of tuples (column_name, value) or list of values
                            # (only if we have column names already)
                            if isinstance(source_data[0], tuple):
                                self.update_from_tuples(source_data)
                            else:
                                self.update_from_values(source_data)
                    except TypeError as e1:
                        try:
                            # noinspection PyProtectedMember
                            # sqlalchemy.util._collections.ImmutableProperties
                            attributes = source_data._sa_instance_state.attrs
                            for a in attributes:  # instance of sqlalchemy.orm.state.AttributeState
                                self._raw_setitem(a.key, getattr(source_data, a.key))
                        except AttributeError as e2:  # Not iterable
                            raise ValueError(
                                f"Row couldn't get set with {source_data}. "
                                f"First Error {e1}. Error when assuming SQLAlchemy ORM row object {e2})"
                                )
                else:
                    args = str(source_data)
                    raise ValueError(
                        f"Row instance couldn't be built with source type {type(args)} value={args}. Error was {e}."
                        )

    def get_column_position(self, column_specifier) -> int:
        """
        Get the ordinal column position based on a column name (str or :py:class:`sqlalchemy.sql.schema.Column`)
        """
        column_name = self.iteration_header.get_column_name(column_specifier)
        return self.iteration_header.get_column_position(column_name)

    def get_column_name(self, column_specifier, raise_on_not_exist=True):
        if column_specifier is None:
            return None
        column_name = self.iteration_header.get_column_name(column_specifier)
        if raise_on_not_exist and not self.iteration_header.has_column(column_name):
            raise KeyError(
                f"{self.__class__.__name__} {self.name} has no item {column_name} "
                f"it does have {self.columns_in_order}"
                )
        return column_name

    @property
    def primary_key(self):
        return self.iteration_header.primary_key

    @primary_key.setter
    def primary_key(self, value):
        self.iteration_header.primary_key = value

    def str_formatted(self):
        return dict_to_str(self)

    @property
    def name(self):
        if self.iteration_header is not None and self.iteration_header.logical_name is not None:
            return self.iteration_header.logical_name
        else:
            return None

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name},status={self.status},primary_key={self.primary_key},\n' \
               f'{self.str_formatted()}'

    def __str__(self):
        if self.primary_key is not None:
            key_values = [(col, self.get(col, '<N/A>')) for col in self.primary_key]
            return f"{self.name} key_values={key_values} status={self.status}"
        else:
            cv = [self[k] for k in self.columns_in_order[:5]]
            return f"{self.name} cols[:5]={cv} status={self.status}"

    def __contains__(self, column_specifier):
        column_name = self.iteration_header.get_column_name(column_specifier)
        return self.iteration_header.has_column(column_name)

    def __getitem__(self, column_specifier):
        column_name = self.iteration_header.get_column_name(column_specifier)
        position = self.iteration_header.get_column_position(column_name)
        try:
            return self._data_values[position]
        except IndexError:
            return None

    def get(self, column_specifier, default_value=None):
        column_name = self.iteration_header.get_column_name(column_specifier)
        try:
            position = self.iteration_header.get_column_position(column_name)
            try:
                return self._data_values[position]
            except IndexError:
                return default_value
        except KeyError:
            return default_value

    @property
    def as_dict(self) -> dict:
        return dict(zip(self.columns_in_order, self._data_values))

    @property
    def as_key_value_list(self) -> list:
        return list(zip(self.columns_in_order, self._data_values))

    def items(self) -> collections.abc.ItemsView:
        return collections.abc.ItemsView(
            self.as_dict
        )

    def __len__(self):
        return len(self.columns_in_order)

    def __iter__(self):
        for column_name in self.columns_in_order:
            yield column_name

    def __copy__(self):
        return self.clone()

    def keys(self) -> collections.abc.KeysView:
        return collections.abc.KeysView(
            {k: None for k in self.iteration_header.columns_in_order}
        )

    def _extend_to_size(self, desired_size):
        current_length = len(self._data_values)
        if current_length < desired_size:
            self._data_values.extend([None for _ in range(desired_size - current_length)])

    def _raw_setitem(self, column_name: Union[str, Column], value):
        self.iteration_header = self.iteration_header.row_set_item(column_name, value, self)

    def __setitem__(self, key, value):
        key_name = self.iteration_header.get_column_name(key)
        self._raw_setitem(key_name, value)

    def set_keeping_parent(self, column_name: Union[str, Column], value):
        """
        Save and restore the iteration header parent in case we are adding
        the key to the header. This saves time in build_row since it can
        know the row is "safe" for quick building

        :param column_name:
        :param value:
        :return: None
        """
        current_parent = self.iteration_header.parent
        self[column_name] = value
        self.iteration_header.parent = current_parent

    def get_name_by_position(self, position):
        """
        Get the column name in a given position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        assert 0 < position <= self.iteration_header.column_count, IndexError(
            f"Position {position} is invalid. Expected 1 to {self.iteration_header.column_count}"
        )

        # -1 because positions are 1 based not 0 based
        # noinspection PyProtectedMember
        return self.iteration_header._columns_in_order[position - 1]

    def get_by_position(self, position):
        """
        Get the column value by position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        assert 0 < position <= self.iteration_header.column_count, IndexError(
            f"Position {position} is invalid. Expected 1 to {self.iteration_header.column_count}"
        )
        if position <= len(self._data_values):
            # -1 because positions are 1 based not 0 based
            return self._data_values[position - 1]
        else:
            return None

    def set_by_zposition_unsafe(self, zposition, value):
        self._data_values[zposition] = value

    def set_by_zposition(self, zposition, value):
        """
        Set the column value by zposition (zero based)
        Note: The first column position is 0 for this method
        """
        if 0 <= zposition < self.iteration_header.column_count:
            if len(self._data_values) <= zposition:
                self._extend_to_size(zposition + 1)
            self._data_values[zposition] = value
        else:
            raise IndexError(
                f"zPosition {zposition} is invalid. Expected 0 to {self.iteration_header.column_count - 1}"
            )

    def set_by_position(self, position, value):
        """
        Set the column value by position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        try:
            self.set_by_zposition(position-1, value)
        except IndexError:
            raise IndexError(
                f"Position {position} is invalid. Expected 1 to {self.iteration_header.column_count}"
            )

    def rename_column(self, old_name, new_name, ignore_missing=False):
        """
        Rename a column

        Parameters
        ----------
        old_name: str
            The name of the column to find and rename.

        new_name: str
            The new name to give the column.

        ignore_missing: boolean
            Ignore (don't raise error) if we don't have a column with the name in old_name.
            Defaults to False
        """
        old_name = self.iteration_header.get_column_name(old_name)
        new_name = self.iteration_header.get_column_name(new_name)
        self.iteration_header = self.iteration_header.rename_column(old_name,
                                                                    new_name,
                                                                    ignore_missing=ignore_missing)

    def rename_columns(self,
                       rename_map: Union[dict, List[tuple]],
                       ignore_missing: bool = False):
        """
        Rename many columns at once.

        Parameters
        ----------
        rename_map
            A dict or list of tuples to use to rename columns.
            Note: a list of tuples is better to use if the renames need to happen in a certain order.

        ignore_missing
            Ignore (don't raise error) if we don't have a column with the name in old_name.
            Defaults to False
        """
        self.iteration_header = self.iteration_header.rename_columns(rename_map, ignore_missing=ignore_missing)

    def __delitem__(self, column_specifier):
        column_name = self.iteration_header.get_column_name(column_specifier)
        self.iteration_header = self.iteration_header.row_remove_column(column_name, self)

    def remove_columns(self,
                       remove_list,
                       ignore_missing=False):
        """
        Remove columns from this row instance (changes to a new RowIterationHeader)

        Parameters
        ----------
        remove_list:
            A list of column names to remove

        ignore_missing:
            Ignore (don't raise error) if we don't have a column with a given name
            Defaults to False
        """
        for column_specifier in remove_list:
            column_name = self.iteration_header.get_column_name(column_specifier)
            self.iteration_header = self.iteration_header.row_remove_column(column_name,
                                                                            row=self,
                                                                            ignore_missing=ignore_missing)

    def clone(self) -> 'Row':
        """
        Create a clone of this row.
        """
        # Make the new row with the same header
        sub_row = self.__class__(iteration_header=self.iteration_header)
        # Copy data
        sub_row._data_values = self._data_values.copy()
        return sub_row

    def subset(
            self,
            exclude: Optional[Iterable] = None,
            rename_map: Optional[Union[dict, List[tuple]]] = None,
            keep_only: Optional[Iterable] = None,
            ) -> 'Row':
        """
        Return a new row instance with a subset of the columns. Original row is not modified
        Excludes are done first, then renames and finally keep_only.
        New instance will have a different RowIterationHeader.

        Parameters
        ----------
        exclude:
            A list of column names (before renames) to exclude from the subset.
            Optional. Defaults to no excludes.

        rename_map:
            A dict to use to rename columns.
            Optional. Defaults to no renames.

        keep_only:
            A list of column names (after renames) of columns to keep.
            Optional. Defaults to keep all.
        """
        # Checks for clone operation
        doing_clone = True

        if keep_only is not None:
            keep_only = set([self.iteration_header.get_column_name(c) for c in keep_only])
            doing_clone = False

        if exclude is None:
            exclude = []
        else:
            exclude = set([self.iteration_header.get_column_name(c) for c in exclude])
            doing_clone = False

        if rename_map is not None:
            doing_clone = False

        if doing_clone:
            sub_row = self.clone()
        else:
            # Make a new row with new header
            sub_row = self.iteration_header.row_subset(row=self,
                                                       exclude=exclude,
                                                       rename_map=rename_map,
                                                       keep_only=keep_only)
        return sub_row

    @property
    def column_set(self) -> frozenset:
        """
        An ImmutableSet of the columns of this row.
        Used to store different row configurations in a dictionary or set.

        WARNING: The resulting set is not ordered. Do not use if the column order affects the operation.
        See positioned_column_set instead.

        Pass through call to iteration_header.column_set.
        """
        return self.iteration_header.column_set

    @property
    def column_count(self) -> int:
        """
        Returns count of how many columns are in this row.

        Pass through call to iteration_header.column_count.
        """
        return self.iteration_header.column_count

    @property
    def positioned_column_set(self) -> Set[tuple]:
        """
        An ImmutableSet of the tuples (column, position) for this row.
        Used to store different row configurations in a dictionary or set.

        Note: column_set would not always work here because the set is not ordered even though the columns are.

        Pass through call to iteration_header.positioned_column_set.
        """
        return self.iteration_header.positioned_column_set

    def column_position(self, column_name):
        """
        Get the column position (1 based) given a column name.

        Parameters
        ----------
        column_name: str
            The column name to find the position of
        """
        normalized_name = self.iteration_header.get_column_name(column_name)
        return self.columns_in_order.index(normalized_name) + 1  # index is 0 based, positions are 1 based

    @property
    def columns_in_order(self) -> Sequence:
        """
        A list of the columns of this row in the order they were defined.

        Note: If the Row was created using a dict or dict like source, there was no order for the Row to work with.
        """
        return self.iteration_header.columns_in_order

    def values(self) -> List:
        """
        Return a list of the row values in the same order as the columns.
        """
        # TODO: Change to return either ValuesView or tuple of values.
        #       tuple tests as a lot faster, but ValuesView is what callers might expect
        #       since MutableMapping returns ValuesView.
        #       In either case, the call will be slower, but safer since the caller
        #       would not be able to break the row by changing the list of values.
        return self._data_values

    def _values_equal_coerce(self, val1, val2, col_name):
        if val1 is None:
            if val2 is None:
                return True
            else:
                return False
        elif val2 is None:
            return False
        elif type(val1) == type(val2):
            return val1 == val2
        elif type(val1) in self.NUMERIC_TYPES and type(val2) in self.NUMERIC_TYPES:
            return Decimal(val1) == Decimal(val2)
        else:
            msg = f'{self.name} data type mismatch on compare of {col_name} {type(val1)} vs {type(val2)}'
            warnings.warn(msg)
            return str(val1) == str(val2)

    def compare_to(self,
                   other_row: 'Row',
                   exclude: Iterable = None,
                   compare_only: Iterable = None,
                   coerce_types: bool = True) -> MutableSequence[ColumnDifference]:
        """
        Compare one RowCaseInsensitive to another. Returns a list of differences.

        Parameters
        ----------
        other_row
        exclude
        compare_only
        coerce_types

        Returns
        -------
        List of differences
        """
        if compare_only is not None:
            compare_only = set([other_row.get_column_name(c, raise_on_not_exist=False) for c in compare_only])

        if exclude is None:
            exclude = []
        else:
            exclude = set([other_row.get_column_name(c, raise_on_not_exist=False) for c in exclude])

        differences_list = list()
        for other_col_name, other_col_value in other_row.items():
            if other_col_name not in exclude:
                if compare_only is None or other_col_name in compare_only:
                    existing_column_value = self[other_col_name]
                    if coerce_types:
                        values_equal = self._values_equal_coerce(existing_column_value, other_col_value, other_col_name)
                    else:
                        values_equal = (existing_column_value == other_col_value)
                    if not values_equal:
                        differences_list.append(ColumnDifference(column_name=other_col_name,
                                                                 old_value=existing_column_value,
                                                                 new_value=other_col_value,
                                                                 )
                                                )
        return differences_list

    def __eq__(self, other):
        try:
            diffs = self.compare_to(other)
        except KeyError:
            return False
        return diffs == []

    def transform(self,
                  column_specifier: str,
                  transform_function: Callable,
                  *args,
                  **kwargs):
        # noinspection PyIncorrectDocstring
        """
        Apply a transformation to a column.
        The transformation function must take the value to be transformed as it's first argument.

        Parameters
        ----------
        column_specifier: str
            The column name in the row to be transformed
        transform_function: func
            The transformation function to use. It must take the value to be transformed as it's first argument.
        args:
            Positional arguments to pass to transform_function
        kwargs:
            Keyword arguments to pass to transform_function

        Keyword Parameters Used Directly
        --------------------------------
        raise_on_not_exist:
            Should this function raise an error if the column_specifier doesn't match an existing column.
            Must be passed as a keyword arg
            Defaults to True

        All other keyword parameters are passed along to the transform_function
        """
        # noinspection PyPep8Naming

        raise_on_not_exist = True
        if Row.RAISE_ON_NOT_EXIST_NAME in kwargs:
            raise_on_not_exist = kwargs[Row.RAISE_ON_NOT_EXIST_NAME]
            del kwargs[Row.RAISE_ON_NOT_EXIST_NAME]

        try:
            column_name = self.iteration_header.get_column_name(column_specifier)
            position = self.iteration_header.get_column_position(column_name)
            value = self._data_values[position]
        except KeyError as e:
            # If we get here, everything failed
            if raise_on_not_exist:
                raise e
            return self
        try:
            new_value = transform_function(value, *args, **kwargs)
            self._data_values[position] = new_value
        except Exception as e:
            raise ValueError(f"{transform_function} on {column_name} with value {value} yielded exception {e}")

        return self
