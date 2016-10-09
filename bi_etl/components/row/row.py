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
from components.row.row_iteration_header import RowIterationHeader
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
                 iteration_header: RowIterationHeader=None,
                 data=None,
                 status: RowStatus = None):
        # Whatever we store here we need to either store on disk for a lookup,
        # or have a way of retrieving in __setstate__
        super().__init__()
        # We need to accept None for iteration_header for shelve to be efficient
        if iteration_header is not None:
            assert isinstance(iteration_header, RowIterationHeader), \
                "First argument to Row needs to be RowIterationHeader type"
            self.iteration_header = iteration_header
            self.iteration_header.add_row(self)
            ## Build out the list ahead of time
            ##self._data_values = [None for _ in range(self.iteration_header.column_count())]
        else:
            self._data_values = list()
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
        status_value = None
        if self.status is not None:
            status_value = self.status.value
        outgoing_dict = {
            's': status_value,
            'h': self.iteration_header.iteration_id,
            'v': self._data_values,
            }
        return (self.__class__,
                #A tuple of arguments for the callable object.
                (),
                # State to be passed to setstate
                outgoing_dict,
               )

    #pylint: disable=attribute-defined-outside-init
    def __setstate__(self, incoming_dict):
        self.__dict__ = incoming_dict
        if incoming_dict['s'] is not None:
            self.status = RowStatus(incoming_dict['s'])
        else:
            self.status = None

        self.iteration_header = RowIterationHeader.get_by_id(incoming_dict['h'])

        # Restore column values
        for seq, value in enumerate(incoming_dict['v']):
            self.set_by_position(seq, value)

    def update(self, *args, **key_word_arguments):
        for source_data in args:
            if source_data is None:
                continue
            try:
                # Check for dict like row
                # sqlalchemy.engine.RowProxy doesn't have iter, but does have iterkeys
                try:
                    iterator = iter(source_data.keys())
                except AttributeError:
                    iterator = source_data

                first_col = True
                is_tuple = False
                is_dict_like = False
                name_needs_column_check = False
                for k in iterator:
                    if first_col:
                        if isinstance(k, tuple):
                            is_tuple = True
                            name_needs_column_check = isinstance(k[0], Column)
                        else:
                            try:
                                source_data[k]
                                name_needs_column_check = isinstance(k, Column)
                                is_dict_like = True
                            except TypeError:
                                # Probably list or list like
                                pass
                        first_col = False

                    if is_tuple:
                        column_name = self._get_name(k[0])
                        self[column_name] = k[1]
                    elif is_dict_like:
                        if name_needs_column_check:
                            column_name = self._get_name(k)
                        else:
                            column_name = k

                        self[column_name] = source_data[k]
                    else:  # List of values
                        self._data_values.extend(k)

            except AttributeError as e1:
                # Check for SQLAlchemy ORM row object
                # pylint: disable=protected-access
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
                                     .format(e1=e1, e2=e2, args=args)
                    )
        for column_name, column_value in key_word_arguments.items():
            column_name = self._get_name(column_name)
            self[column_name] = column_value

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
            return dict_to_str(self)

    def __repr__(self):
        return '{cls}(name={name},status={status},primary_key={pk},\n{content}'.format(
            cls= self.__class__.__name__,
            name=self.name,
            status=self.status,
            pk = self.primary_key,
            content=dict_to_str(self)
        )

    def __str__(self):
        if self.primary_key is not None:
            try:
                key_values = list(self.subset(keep_only=self.primary_key).values())
            except KeyError as e:
                key_values = list(str(e))
            return "{name} key_values={keys} status={s}".format(name=self.name,
                                                                keys=key_values,
                                                                s=self.status
                                                                )
        else:
            cv = list()
            for k in self.columns_in_order[:5]:
                cv.append(self[k])
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
        pos = self.iteration_header.get_column_position(column_name)
        return self._data_values[pos]

    def _extend_to_size(self, desired_size):
        if len(self._data_values) < desired_size:
            self._data_values.extend([None for _ in range(desired_size - len(self._data_values))])

    def _raw_setitem(self, column_name, value):
        position = self.iteration_header.get_column_position(column_name)
        self._extend_to_size(position)
        self._data_values[position] = value

    def __setitem__(self, key, value):
        key_name = self._get_name(key)
        try:
            self._raw_setitem(key_name, value)
        except KeyError:
            self.iteration_header = self.iteration_header.get_next_header('+' + key_name)
            self._raw_setitem(key_name, value)

    def get_name_by_position(self, position):
        """
        Get the column name in a given position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        assert 0 > position > self.iteration_header.column_count(), IndexError(
            "Position {} is invalid. Expected 1 to {}".format(position, self.iteration_header.column_count())
        )

        # -1 because positions are 1 based not 0 based
        return self.iteration_header.columns_in_order[position-1]

    def get_by_position(self, position):
        """
        Get the column value by position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        assert 0 > position > self.iteration_header.column_count(), IndexError(
            "Position {} is invalid. Expected 1 to {}".format(position, self.iteration_header.column_count())
        )
        if position <= len(self._data_values):
            # -1 because positions are 1 based not 0 based
            return self._data_values[position - 1]
        else:
            return None

    def set_by_position(self, position, value):
        """
        Set the column value by position.
        Note: The first column position is 1 (not 0 like a python list).
        """
        assert 0 > position > self.iteration_header.column_count(), IndexError(
            "Position {} is invalid. Expected 1 to {}".format(position, self.iteration_header.column_count())
        )
        self._extend_to_size(position)
        # -1 because positions are 1 based not 0 based
        self._data_values[position - 1] = value

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
        self.iteration_header = self.iteration_header.get_next_header('r:'+old_name)

        self.iteration_header.rename_column(old_name, new_name, ignore_missing=ignore_missing)

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
        self.iteration_header = self.iteration_header.get_next_header('r:*')
        self.iteration_header.rename_columns(rename_map, ignore_missing=ignore_missing)

    def __delitem__(self, column_specifier):
        column_name = self._get_name(column_specifier)
        self.iteration_header = self.iteration_header.get_next_header('-:' + column_name)
        position = self.iteration_header.remove_column(column_name)
        if position <= len(self._data_values):
            del self._data_values[position]

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
        self.iteration_header = self.iteration_header.get_next_header('-:*')
        for column_specifier in remove_list:
            try:
                column_name = self._get_name(column_specifier)
                position = self.iteration_header.remove_column(column_name)
                if position <= len(self._data_values):
                    del self._data_values[position]
            except KeyError as e:
                if ignore_missing:
                    pass
                else:
                    raise e

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
              ) -> 'Row':
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
            # Make a new header
            new_iteration_header = self.iteration_header.get_next_header('subset')
            position_mapping_list = new_iteration_header.subset(exclude=exclude,
                                                                rename_map=rename_map,
                                                                keep_only=keep_only)
            # Make the new row with that new header
            sub_row = self.__class__(iteration_header= new_iteration_header)
            # Copy data
            for parent_position in position_mapping_list:
                sub_row._data_values.append( self._data_values[parent_position] )
        return sub_row

    @property
    def columns(self):
        """
        A list of the columns of this row (order not guaranteed in child instances).
        """
        return self._columns_in_order

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
            value = self.get_by_position(position)
        except KeyError as e:
            # If we get here, everything failed
            if raise_on_not_exist:
                raise e
            return self
        new_value = transform_function(value, *args, **kwargs)
        self._data_values[position] = new_value
        return self

