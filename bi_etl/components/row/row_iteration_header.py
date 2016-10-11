"""
Created on May 26, 2015

@author: woodd
"""
import functools
from operator import attrgetter
from typing import Union, List, Iterable

from bi_etl.components.row.cached_frozenset import get_cached_frozen_set
from sqlalchemy.sql.schema import Column


class RowIterationHeader(object):
    """
    Stores the headers of a set of rows for a given iteration
    """
    next_iteration_id = 0
    instance_dict = dict()

    @staticmethod
    def get_by_id(iteration_id):
        return RowIterationHeader.instance_dict[iteration_id]

    def __init__(self,
                 all_rows_same_columns: bool,
                 logical_name: str = None,
                 primary_key: list = None,
                 parent: 'bi_etl.components.etlcomponent.ETLComponent' = None,
                 ):
        # Note this is not thread safe. However, we aren't threading yet.
        RowIterationHeader.next_iteration_id += 1
        self.iteration_id = RowIterationHeader.next_iteration_id
        RowIterationHeader.instance_dict[self.iteration_id] = self
        if all_rows_same_columns is None:
            self.all_rows_same_columns = False
        else:
            self.all_rows_same_columns = all_rows_same_columns
        self.column_definition_locked = False
        self.row_count = 0
        self.logical_name = logical_name or id(self)
        self._primary_key = None
        self.primary_key = primary_key
        self.parent = parent
        self._actions_to_next_headers = dict()
        self.columns_in_order = list()
        self._columns_positions = dict()
        self.columns_frozen = False
        self._cached_column_set = None
        self._cached_positioned_column_set = None

    def get_next_header(self, action: str) -> 'RowIterationHeader':
        """
        Get the next header after performing a manipulation on the set of columns.

        Parameters
        ----------
        action

        Returns
        -------

        """
        if action not in self._actions_to_next_headers:
            new_header = RowIterationHeader(all_rows_same_columns=self.all_rows_same_columns,
                                            logical_name= (self.logical_name + '.' + action),
                                            primary_key=self.primary_key,
                                            parent=None
                                            )
            new_header.columns_in_order = self.columns_in_order
            new_header._columns_positions = self._columns_positions

            self._actions_to_next_headers[action] = new_header
        return self._actions_to_next_headers[action]

    @property
    def primary_key(self):
        try:
            if self._primary_key is not None and len(self._primary_key) > 0:
                # Check if primary_key is list of Column objects and needs to be turned into a list of str name values
                # We do this here and not on setter since program might never call getter
                if isinstance(self._primary_key[0], Column):
                    self._primary_key = list(map(attrgetter('name'), self._primary_key))
                return self._primary_key
            else:
                return None
        except AttributeError:
            return None

    @primary_key.setter
    def primary_key(self, value):
        if value is not None:
            if isinstance(value, str):
                value = [value]
            assert hasattr(value, '__iter__'), "primary_key must be iterable or string"
            self._primary_key = value
        else:
            self._primary_key = None

    @property
    def column_set(self):
        """
        An ImmutableSet of the the columns of this row.
        Used to store different row configurations in a dictionary or set.

        WARNING: The resulting set is not ordered. Do not use if the column order affects the operation.
        See positioned_column_set instead.
        """
        if self._cached_column_set is None:
            self._cached_column_set = frozenset(self.columns_in_order)
        return self._cached_column_set

    @property
    def positioned_column_set(self):
        """
        An ImmutableSet of the the tuples (column, position) for this row.
        Used to store different row configurations in a dictionary or set.

        Note: column_set would not always work here because the set is not ordered even though the columns are.

        """
        if self._cached_positioned_column_set is None:
            tpl_lst = list()
            for key, position in enumerate(self.columns_in_order):
                tpl = (key, position)
                tpl_lst.append(tpl)
            self._cached_positioned_column_set = get_cached_frozen_set(tpl_lst)
        return self._cached_positioned_column_set

    def add_row(self, row):
        self.row_count += 1

    def remove_row(self, row):
        self.row_count -= 1

    def column_count(self) -> int:
        return len(self.columns_in_order)

    def has_column(self, column_name):
        return column_name in self._columns_positions

    def _key_error(self, column_name):
        return KeyError("{name} has no item {column_name} it does have {cols}"
                        .format(name=self.logical_name,
                                column_name=column_name,
                                cols=self.columns_in_order
                                )
                        )

    def get_column_position(self, column_name, allow_create=False):
        try:
            position = self._columns_positions[column_name]
        except KeyError:
            if self.columns_frozen or not allow_create:
                raise self._key_error(column_name)
            else:
                new_pos = len(self.columns_in_order)
                self.columns_in_order.append(column_name)
                self._columns_positions[column_name] = new_pos
                self._cached_column_set = None
                self._cached_positioned_column_set = None
                position = new_pos
        return position

    @functools.lru_cache()
    def header_rename_column(self, old_name, new_name, ignore_missing = False) -> int:
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
        assert new_name not in self._columns_positions, "Target column name {} already exists".format(new_name)
        try:
            position = self._columns_positions[old_name]
            self.columns_in_order[position] = new_name
            del self._columns_positions[old_name]
            self._columns_positions[new_name] = position
            if self.primary_key is not None:
                try:
                    pk_position = self.primary_key.index(old_name)
                    self.primary_key[pk_position] = new_name
                except ValueError:
                    pass

            return position

        except (KeyError, ValueError) as e:
            if ignore_missing:
                return None
            else:
                raise e

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
        # Note: subset with rename_map is currently slightly faster
        if isinstance(rename_map, dict):
            for k in rename_map.keys():
                self.rename_column(k, rename_map[k], ignore_missing)
        elif rename_map is not None:  # assume it's a list of tuples
            for (old, new) in rename_map:
                self.rename_column(old, new, ignore_missing)

    def remove_column(self, column_name, ignore_missing = False) -> int:
        try:
            position = self._columns_positions[column_name]
            del self.columns_in_order[position]
            for following_col in self.columns_in_order[position:]:
                self._columns_positions[following_col] -= 1
            return position
        except KeyError as e:
            if ignore_missing:
                return None
            else:
                raise e

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
        for column_name in remove_list:
            self.remove_column(column_name, ignore_missing=ignore_missing)

    def subset(self,
               exclude: Iterable = None,
               rename_map: Union[dict, List[tuple]] = None,
               keep_only: Iterable = None,
              ) -> list:
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

        Returns
        -------
        a list with the position mapping of new to old items.
        So:
            The first item in the list will be the index of that item in the old list.
            The second item in the list will be the index of that item in the old list.
            etc
        """
        position_mapping_list = list()
        old_names = self.columns_in_order.copy()
        #old_name_positions = self._columns_positions.copy()
        self.rename_columns(rename_map)
        for parent_position, old_column_name in enumerate(old_names):
            remove_column = True
            new_column_name = self.columns_in_order[parent_position]
            if old_column_name not in exclude:
                if keep_only is None or new_column_name in keep_only:
                    position_mapping_list.append(parent_position)
                    remove_column = False
            if remove_column:
                self.remove_column(new_column_name)
        return position_mapping_list

