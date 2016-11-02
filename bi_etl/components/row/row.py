# -*- coding: utf-8 -*-
"""
Created on Sep 17, 2014

@author: woodd
"""
import warnings
from decimal import Decimal
from typing import Union, List, Iterable

from bi_etl.components.row.column_difference import ColumnDifference
from bi_etl.components.row.row_status import RowStatus
from bi_etl.utility import dict_to_str
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from sqlalchemy.sql.schema import Column


class Row(object):
    """
    Replacement for core SQL Alchemy, CSV or other dictionary based rows.
    Handles column names that are SQL Alchemy column objects.
    Keeps order of the columns (see columns_in_order)
    """
    NUMERIC_TYPES = [int, float, Decimal]
    # For performance with the Column to str conversion we keep a cache of converted values
    __name_map_db = dict()

    def __init__(self,
                 iteration_header: RowIterationHeader,
                 data=None,
                 status: RowStatus = None,
                 allocate_space=True):
        # Whatever we store here we need to either store on disk for a lookup,
        # or have a way of retrieving in __setstate__
        super().__init__()
        # We need to accept None for iteration_header for shelve to be efficient
        self._data_values = list()
        if isinstance(iteration_header, int):
            self.iteration_header = RowIterationHeader.get_by_id(iteration_header)
        else:
            assert isinstance(iteration_header, RowIterationHeader), \
                "First argument to Row needs to be RowIterationHeader type, got {}".format(type(iteration_header))
            self.iteration_header = iteration_header
        self.iteration_header.add_row(self)
        if allocate_space:
            self._extend_to_size(len(self.iteration_header.columns_in_order))
        self.status = status

        # Populate our data
        if data is not None:
            self.update(data)

    @staticmethod
    def _get_name(input_name) -> str:
        if input_name in Row.__name_map_db:
            return Row.__name_map_db[input_name]
        else:
            # If the input_name is an SA Column use it's name.
            # In Python 2.7 to 3.4, isinstance is a lot faster than try-except or hasattr (which does a try)
            if isinstance(input_name, Column):
                name_str = input_name.name
            else:
                if not isinstance(input_name, str):
                    raise ValueError("Row column name must be str, unicode, or Column. Got {}".format(type(input_name)))
                name_str = input_name
                Row.__name_map_db[input_name] = name_str
            return name_str

    def __reduce__(self):
        # TODO: Experiment with different formats for performance and compactness
        # 91 bytes using pickle.HIGHEST_PROTOCOL, 86 bytes in test using default protocol
        status_value = None
        if self.status is not None:
            if isinstance(self.status, RowStatus):
                status_value = self.status.value
            else:
                status_value = self.status
        return (self.__class__,
                # A tuple of arguments for the callable object.
                (self.iteration_header.iteration_id,
                 self._data_values,
                 status_value
                 ),
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

    # pylint: disable=attribute-defined-outside-init
    def __setstate_v1__(self, incoming_dict):
        self.__dict__ = incoming_dict
        if incoming_dict['s'] is not None:
            self.status = RowStatus(incoming_dict['s'])
        else:
            self.status = None
        # Restore column values
        self._data_values = incoming_dict['v']

    def update_from_dict(self, source_dict):
        for column_specifier, value in source_dict.items():
            column_name = self._get_name(column_specifier)
            self._raw_setitem(column_name, value)

    def update_from_row_proxy(self, source_row):
        for column_specifier, value in source_row.items():
            column_name = self._get_name(column_specifier)
            self._raw_setitem(column_name, value)

    def update_from_tuples(self, tuples_list):
        for column_specifier, value in tuples_list:
            column_name = self._get_name(column_specifier)
            self._raw_setitem(column_name, value)

    def update_from_values(self, values_list):
        if len(self.columns_in_order) >= len(values_list):
            self._data_values = values_list.copy()
        else:
            raise ValueError("Insufficient columns to store list of values in row.")

    def update(self, *args, **key_word_arguments):
        if len(key_word_arguments) > 0:
            self.update_from_dict(key_word_arguments)

        for source_data in args:
            try:
                source_data[None]
                # Is a dict with None it it! That's odd, but...
                self.update_from_dict(source_data)
            except KeyError:
                # Is a dict
                self.update_from_dict(source_data)
            except AttributeError:
                self.update_from_row_proxy(source_data)
            except TypeError as e:
                # Not a dict
                if hasattr(source_data, '__iter__') and not isinstance(source_data, str):
                    try:
                        source_data = list(source_data)
                        # List of tuples (column_name, value) or list of values (only if we have column names already)
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
                            raise ValueError("Row couldn't get set with {args}."
                                             " First Error {e1}."
                                             "Error when assuming SQLAlchemy ORM row object {e2})"
                                             .format(e1=e1, e2=e2, args=source_data)
                                             )
                else:
                    raise ValueError("Row couldn't get set with {atype} {args}."
                                     " Error {e}."
                                     .format(e=e, args=source_data, atype=type(args))
                                     )

    def get_column_position(self, column_specifier):
        column_name = self._get_name(column_specifier)
        return self.iteration_header.get_column_position(column_name)

    def get_column_name(self, column_specifier, raise_on_not_exist= True):
        if column_specifier is None:
            return None
        column_name = self._get_name(column_specifier)
        if raise_on_not_exist and not self.iteration_header.has_column(column_name):
            raise KeyError("{cls} {name} has no item {column_name} it does have {cols}"
                           .format(cls=self.__class__.__name__,
                                   name=self.name,
                                   column_name=column_name,
                                   cols=self.columns_in_order
                                   )
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
        return '{cls}(name={name},status={status},primary_key={pk},\n{content}'.format(
            cls= self.__class__.__name__,
            name=self.name,
            status=self.status,
            pk = self.primary_key,
            content=self.str_formatted()
        )

    def __str__(self):
        if self.primary_key is not None:
            key_values = [(col, self.get(col, '<N/A>')) for col in self.primary_key]
            return "{name} key_values={keys} status={s}".format(name=self.name,
                                                                keys=key_values,
                                                                s=self.status
                                                                )
        else:
            cv = [ self[k] for k in self.columns_in_order[:5] ]
            return "{name} cols[:5]={cv} status={s}".format(name=self.name,
                                                            cv=cv,
                                                            s=self.status
                                                            )

    def values(self):
        return self._data_values

    def __contains__(self, column_specifier):
        column_name = self._get_name(column_specifier)
        return self.iteration_header.has_column(column_name)

    def __getitem__(self, column_specifier):
        column_name = self._get_name(column_specifier)
        position = self.iteration_header.get_column_position(column_name)
        if position < len(self._data_values):
            return self._data_values[position]
        else:
            return None

    def get(self, column_specifier, default_value=None):
        column_name = self._get_name(column_specifier)
        try:
            position = self.iteration_header.get_column_position(column_name)
            if position < len(self._data_values):
                return self._data_values[position]
        except KeyError:
            pass
        return default_value

    @property
    def as_dict(self) -> dict:
        return dict(zip(self.columns_in_order, self._data_values))

    def items(self):
        for column_name, column_value in zip(self.columns_in_order, self._data_values):
            yield column_name, column_value

    def __len__(self):
        return len(self.columns_in_order)

    def __iter__(self):
        for column_name in self.columns_in_order:
            yield column_name

    def __copy__(self):
        return self.clone()

    def keys(self):
        return self.columns_in_order

    def _extend_to_size(self, desired_size):
        current_length = len(self._data_values)
        if current_length < desired_size:
            self._data_values.extend([None for _ in range(desired_size - current_length)])

    def _raw_setitem(self, column_name, value):
        self.iteration_header = self.iteration_header.row_set_item(column_name, value, self)

    def __setitem__(self, key, value):
        key_name = self._get_name(key)
        self._raw_setitem(key_name, value)

    def get_name_by_position(self, position):
        """
        Get the column name in a given position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        assert 0 < position <= self.iteration_header.column_count(), IndexError(
            "Position {} is invalid. Expected 1 to {}".format(position, self.iteration_header.column_count())
        )

        # -1 because positions are 1 based not 0 based
        return self.iteration_header._columns_in_order[position - 1]

    def get_by_position(self, position):
        """
        Get the column value by position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        assert 0 < position <= self.iteration_header.column_count(), IndexError(
            "Position {} is invalid. Expected 1 to {}".format(position, self.iteration_header.column_count())
        )
        if position <= len(self._data_values):
            # -1 because positions are 1 based not 0 based
            return self._data_values[position - 1]
        else:
            return None

    def set_by_zposition(self, zposition, value):
        """
        Set the column value by zposition (zero based)
        Note: The first column position is 0 for this method
        """
        if 0 <= zposition < self.iteration_header.column_count():
            if len(self._data_values) <= zposition:
                self._extend_to_size(zposition + 1)
            self._data_values[zposition] = value
        else:
            raise IndexError(
                "Position {} is invalid. Expected 0 to {}".format(zposition, self.iteration_header.column_count())
            )

    def set_by_position(self, position, value):
        """
        Set the column value by position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        self.set_by_zposition(position-1, value)

    def rename_column(self, old_name, new_name, ignore_missing = False):
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
        old_name = self._get_name(old_name)
        new_name = self._get_name(new_name)
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
        column_name = self._get_name(column_specifier)
        self.iteration_header = self.iteration_header.row_remove_column(column_name, self)

    def remove_columns(self,
                       remove_list,
                       ignore_missing = False):
        """
        Remove columns from this row instance.

        Parameters
        ----------
        remove_list:
            A list of column names to remove

        ignore_missing:
            Ignore (don't raise error) if we don't have a column with a given name
            Defaults to False
        """
        for column_specifier in remove_list:
            column_name = self._get_name(column_specifier)
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

    def subset(self,
               exclude: Iterable = None,
               rename_map: Union[dict, List[tuple]] = None,
               keep_only: Iterable = None,
               )-> 'Row':
        """
        Return a new row instance with a subset of the columns. Original row is not modified
        Excludes are done first, then renames and finally keep_only.

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
            keep_only = set([self._get_name(c) for c in keep_only])
            doing_clone = False

        if exclude is None:
            exclude = []
        else:
            exclude = set([self._get_name(c) for c in exclude])
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
    def columns(self):
        """
        A list of the columns of this row (order not guaranteed in child instances).
        """
        return self.iteration_header._columns_in_order

    @property
    def column_set(self):
        """
        An ImmutableSet of the the columns of this row.
        Used to store different row configurations in a dictionary or set.

        WARNING: The resulting set is not ordered. Do not use if the column order affects the operation.
        See positioned_column_set instead.
        """
        return self.iteration_header.column_set

    @property
    def column_count(self):
        return self.iteration_header.column_count()

    @property
    def positioned_column_set(self):
        """
        An ImmutableSet of the the tuples (column, position) for this row.
        Used to store different row configurations in a dictionary or set.

        Note: column_set would not always work here because the set is not ordered even though the columns are.

        """
        return self.iteration_header.positioned_column_set

    def column_position(self, column_name):
        """
        Get the column position given a column name.

        Parameters
        ----------
        column_name: str
            The column name to find the position of
        """
        normalized_name = self._get_name(column_name)
        return self.columns_in_order.index(normalized_name) + 1  # index is 0 based, positions are 1 based

    @property
    def columns_in_order(self):
        """
        A list of the columns of this row in the order they were defined.

        Note: If the Row was created using a dict or dict like source, there was no order for the Row to work with.
        """
        return self.iteration_header.columns_in_order

    def values_in_order(self):
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
            msg = '{row} data type mismatch on compare of {col_name} {type1} vs {type2}'.format(
                row=self.name,
                col_name=col_name,
                type1=type(val1),
                type2=type(val2),
            )
            warnings.warn(msg)
            return str(val1) == str(val2)

    def compare_to(self,
                   other_row: 'Row',
                   exclude: list = None,
                   compare_only: list = None,
                   coerce_types: bool = True) -> list:
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
                        differences_list.append(ColumnDifference(column_name= other_col_name,
                                                                 old_value= existing_column_value,
                                                                 new_value= other_col_value,
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
                  column_specifier,
                  transform_function,
                  raise_on_not_exist :bool =True,
                  *args,
                  **kwargs):
        """
        Apply a transformation to a column.
        The transformation function must take the value to be transformed as it's first argument.

        Parameters
        ----------
        column_specifier: str
            The column name in the row to be transformed
        transform_function: func
            The transformation function to use. It must take the value to be transformed as it's first argument.
        raise_on_not_exist:
            Should this function raise an error if the column_specifier doesn't match an existing column.
            Defaults to True
        args: list
            Positional arguments to pass to transform_function
        kwargs: dict
            Keyword arguments to pass to transform_function
        """
        try:
            column_name = self._get_name(column_specifier)
            position = self.iteration_header.get_column_position(column_name)
            value = self._data_values[position]
        except KeyError as e:
            # If we get here, everything failed
            if raise_on_not_exist:
                raise e
            return self
        new_value = transform_function(value, *args, **kwargs)
        self._data_values[position] = new_value
        return self

if __name__ == "__main__":
    from _datetime import datetime
    import pickle
    from timeit import timeit
    iteration_header = RowIterationHeader()
    row = Row(iteration_header,
              data={'col1': 54321,
                    'col2': 'Two',
                    'col3': datetime(2012, 1, 3, 12, 25, 33),
                    'col4': 'All good pickles',
                    'col5': 123.23,
                    })
    s = pickle.dumps(row, pickle.HIGHEST_PROTOCOL)
    print(len(s))
    print(s)
    row2 = pickle.loads(s)
    print(row == row2)
    print(row.compare_to(row2))
    r = timeit("pickle.loads(pickle.dumps(row, pickle.HIGHEST_PROTOCOL))",
"""
import pickle;
from bi_etl.components.row.row import Row;
from bi_etl.components.row.row_iteration_header import RowIterationHeader;
from _datetime import datetime
iteration_header = RowIterationHeader()
row = Row(iteration_header,
          data={'col1': 54321,
                'col2': 'Two',
                'col3': datetime(2012, 1, 3, 12, 25, 33),
                'col4': 'All good pickles',
                'col5': 123.23,
                })
"""
)
    print(r)

    print("V1--------")
    Row.__reduce__ = Row.__reduce_v1__
    Row.__setstate__ = Row.__setstate_v1__
    s = pickle.dumps(row, pickle.HIGHEST_PROTOCOL)
    print(len(s))
    print(s)
    row2 = pickle.loads(s)
    print(row == row2)
    #print(row.compare_to(row2))

    r = timeit("pickle.loads(pickle.dumps(row, pickle.HIGHEST_PROTOCOL))",
"""
import pickle;
from bi_etl.components.row.row import Row;
from bi_etl.components.row.row_iteration_header import RowIterationHeader;
from _datetime import datetime
iteration_header = RowIterationHeader()
row = Row(iteration_header,
          data={'col1': 54321,
                'col2': 'Two',
                'col3': datetime(2012, 1, 3, 12, 25, 33),
                'col4': 'All good pickles',
                'col5': 123.23,
                })
"""
)
    print(r)
