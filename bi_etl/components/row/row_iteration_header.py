"""
Created on May 26, 2015

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import functools
import typing
from operator import attrgetter
from typing import Union, List

from sqlalchemy.sql.schema import Column

from bi_etl.components.row.cached_frozenset import get_cached_frozen_set

if typing.TYPE_CHECKING:
    import bi_etl.components.row.row.Row
    from bi_etl.components.etlcomponent import ETLComponent


class RowIterationHeader(object):
    """
    Stores the headers of a set of rows for a given iteration
    """
    next_iteration_id = 0
    instance_dict = dict()
    __shared_name_map_db = dict()

    @staticmethod
    def get_by_id(iteration_id):
        return RowIterationHeader.instance_dict[iteration_id]

    def __init__(
            self,
            logical_name: typing.Optional[str] = None,
            primary_key: typing.Optional[typing.Iterable] = None,
            parent: typing.Optional[ETLComponent] = None,
            columns_in_order: typing.Optional[typing.Iterable] = None,
            columns_can_vary_by_row: typing.Optional[bool] = None,
            ):
        # Note this is not thread safe. However, we aren't threading yet.
        RowIterationHeader.next_iteration_id += 1
        self.iteration_id = RowIterationHeader.next_iteration_id
        RowIterationHeader.instance_dict[self.iteration_id] = self
        self.column_definition_locked = False
        if columns_in_order:
            self._column_count = len(columns_in_order)
        else:
            self._column_count = 0
        if columns_can_vary_by_row is not None:
            self.columns_can_vary_by_row = columns_can_vary_by_row
        else:
            if self._column_count == 0:
                # If we got no columns we have to assume varibable rows
                self.columns_can_vary_by_row = True
            else:
                # If we got did get columns we'll assume fixed rows
                # If the source could still be variable (e.g. a CSV file)
                # The caller should pass in columns_can_vary_by_row = True
                self.columns_can_vary_by_row = False
        self.row_count = 0
        self.logical_name = logical_name or id(self)
        self._primary_key = None
        self.primary_key = primary_key
        self.parent = parent
        self._actions_to_next_headers = dict()
        self._columns_positions = dict()
        if columns_in_order is not None:
            self._columns_in_order = None
            self.columns_in_order = columns_in_order
            self.__name_map_db = RowIterationHeader.__shared_name_map_db
            self.__name_map_db.update({col: col for col in columns_in_order})
        else:
            self._columns_in_order = list()
            self.__name_map_db = RowIterationHeader.__shared_name_map_db
        self.columns_frozen = False
        self._cached_column_set = None
        self._cached_positioned_column_set = None
        self._cached_columns_in_order_tuple = None
        self._action_position = None
        self.action_id = None
        self.action_count = 0

    def get_column_name(self, input_name: str) -> str:
        try:
            return self.__name_map_db[input_name]
        except KeyError:
            # If the input_name is an SA Column use it's name.
            # In Python 2.7 to 3.4, isinstance is a lot faster than try-except or hasattr (which does a try)
            if isinstance(input_name, str):
                name_str = input_name
            elif isinstance(input_name, Column):
                name_str = input_name.name
            else:
                raise ValueError("Row column name must be str, unicode, or Column. Got {}".format(type(input_name)))
            self.__name_map_db[input_name] = name_str
            return name_str

    def get_action_header(
            self,
            action: tuple,
            start_empty: bool = False,
            ) -> RowIterationHeader:
        """
        Get the header after performing a manipulation on the set of columns.

        Parameters
        ----------
        action:
            A hashable action ID
        start_empty:
            Should the new header start empty (vs transferring the columns)

        Returns
        -------

        """
        return self._actions_to_next_headers[action]

    def get_next_header(
            self,
            action: tuple,
            start_empty: bool = False,
            ) -> RowIterationHeader:
        """
        Get the next header after performing a manipulation on the set of columns.

        Parameters
        ----------
        action:
            A hashable action ID
        start_empty:
            Should the new header start empty (vs transferring the columns)

        Returns
        -------

        """
        if action not in self._actions_to_next_headers:
            new_header = RowIterationHeader(
                logical_name=self.logical_name,
                primary_key=self.primary_key,
                parent=None
                )
            new_header.action_count = self.action_count + 1
            new_header.action_id = action
            if not start_empty:
                new_header._columns_in_order = self._columns_in_order.copy()
                new_header._columns_positions = self._columns_positions.copy()
                new_header._column_count = self._column_count

            self._actions_to_next_headers[action] = new_header
        return self._actions_to_next_headers[action]

    @functools.lru_cache()
    def __repr__(self):
        return '{cls}(id={id},logical_name={logical_name},primary_key={pk}'.format(
            cls=self.__class__.__name__,
            id=self.iteration_id,
            logical_name=self.logical_name,
            pk=self.primary_key,
        )

    @functools.lru_cache()
    def __str__(self):
        return repr(self)

    @property
    def columns_in_order(self) -> typing.Sequence:
        """
        A list of the columns of this row in the order they were defined.
        """
        if self._cached_columns_in_order_tuple is None:
            self._cached_columns_in_order_tuple = tuple(self._columns_in_order)
        return self._cached_columns_in_order_tuple

    @columns_in_order.setter
    def columns_in_order(self, value: typing.Iterable):
        if self._columns_in_order is not None:
            if self.column_count > 0:
                raise ValueError("Setting columns_in_order is only allowed on an empty RowIterationHeader")
        self._columns_in_order = list(value)
        for position, column_name in enumerate(value):
            self._columns_positions[column_name] = position
        self._clear_caches()

    @property
    def primary_key(self) -> typing.Optional[typing.Iterable]:
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
    def primary_key(self, value: typing.Optional[typing.Union[str, typing.Iterable]]):
        if value is not None:
            if isinstance(value, str):
                value = [value]
            assert hasattr(value, '__iter__'), "primary_key must be iterable or string"
            self._primary_key = value
        else:
            self._primary_key = None

    @property
    def column_set(self) -> frozenset:
        """
        An ImmutableSet of the the columns of this row.
        Used to store different row configurations in a dictionary or set.

        WARNING: The resulting set is not ordered. Do not use if the column order affects the operation.
        See positioned_column_set instead.
        """
        if self._cached_column_set is None:
            self._cached_column_set = frozenset(self._columns_in_order)
        return self._cached_column_set

    @property
    def positioned_column_set(self) -> typing.Set[tuple]:
        """
        An ImmutableSet of the the tuples (column, position) for this row.
        Used to store different row configurations in a dictionary or set.

        Note: column_set would not always work here because the set is not ordered even though the columns are.

        """
        if self._cached_positioned_column_set is None:
            tpl_lst = list()
            for key, position in enumerate(self._columns_in_order):
                tpl = (key, position)
                tpl_lst.append(tpl)
            self._cached_positioned_column_set = get_cached_frozen_set(tpl_lst)
        return self._cached_positioned_column_set

    def add_row(self, row):
        self.row_count += 1

    def remove_row(self, row):
        self.row_count -= 1

    @property
    def column_count(self) -> int:
        return self._column_count

    def has_column(self, column_name) -> bool:
        return column_name in self._columns_positions

    def _key_error(self, column_name) -> KeyError:
        return KeyError("{name} has no item {column_name} it does have {cols}"
                        .format(name=self.logical_name,
                                column_name=column_name,
                                cols=self._columns_in_order
                                )
                        )

    @functools.lru_cache(maxsize=1000)
    def get_column_position(
            self,
            column_name: str,
            allow_create: bool = False,
            ) -> int:
        try:
            position = self._columns_positions[column_name]
        except KeyError:
            if self.columns_frozen or not allow_create:
                raise self._key_error(column_name)
            else:
                position = self._add_column(column_name)
        return position

    # noinspection PyProtectedMember
    def row_set_item(
            self,
            column_name: str,
            value,
            row: bi_etl.components.row.row.Row,
            ) -> RowIterationHeader:
        """
        Set a column in a row and return a new row header (it might have changed if the column was new). 
        
        Parameters:        
            column_name: column to set
            value: new value
            row (bi_etl.components.row.row.Row): row to find column on

        Returns:        
            Modified row header
        """
        if column_name in self._columns_positions:
            position = self._columns_positions[column_name]
            # noinspection PyProtectedMember
            row.set_by_zposition(position, value)
            new_header = self
        else:
            # Modification of columns required
            action_tuple = ('+:', column_name)
            new_header = self.get_next_header(action_tuple)
            new_header.add_row(row)
            if new_header._action_position is None:
                new_header._action_position = new_header._add_column(column_name)
            else:
                pass

            # Protected access is required here since we can't call setitem it calls this method.
            # noinspection PyProtectedMember
            row._data_values.append(value)
        return new_header

    def rename_column(
            self,
            old_name: str,
            new_name: str,
            ignore_missing: bool = False,
            no_new_header: bool = False,
            ) -> RowIterationHeader:
        """
        Rename a column

        Parameters:
            old_name: str
                The name of the column to find and rename.
    
            new_name: str
                The new name to give the column.
    
            ignore_missing: boolean
                Ignore (don't raise error) if we don't have a column with the name in old_name.
                Defaults to False
    
            no_new_header:
                Skip creating a new row header, modify in place.
                
                ** BE CAREFUL USING THIS! **
                
                All new rows created with this header will immediately get the new name,
                in which case you won't want to call this method again.
        """
        # Clear LRU cache of get_column_position
        self.get_column_position.cache_clear()
        try:
            position = self._columns_positions[old_name]
            # Only check if target column name exists if we found the source name
            # This way we can have two renames that both map to the same target as long as
            # 1) Only one of the source column names exists
            # 2) ignore_missing is True
            assert new_name not in self._columns_positions, "Target column name {} already exists".format(new_name)
            # Modification of columns required
            if not no_new_header:
                action_tuple = ('r', old_name, new_name)
                new_header = self.get_next_header(action_tuple)
                new_header.row_count = self.row_count
            else:
                new_header = self
            if old_name in new_header._columns_positions:
                new_header._columns_in_order[position] = new_name
                del new_header._columns_positions[old_name]
                new_header._columns_positions[new_name] = position
                if new_header.primary_key is not None:
                    try:
                        pk_position = new_header.primary_key.index(old_name)
                        new_header.primary_key[pk_position] = new_name
                    except ValueError:
                        pass
        except (KeyError, ValueError) as e:
            if ignore_missing:
                return self
            else:
                raise ValueError(f'{old_name} is not a column. Valid columns are {self._columns_positions.keys()}')
        return new_header

    def rename_columns(
            self,
            rename_map: Union[dict, List[tuple]],
            ignore_missing: bool = False,
            no_new_header: bool = False
            ) -> RowIterationHeader:
        """
        Rename many columns at once.

        Parameters:
            rename_map
                A dict or list of tuples to use to rename columns.
                Note a list of tuples is better to use if the renames need to happen in a certain order.
    
            ignore_missing:
                Ignore (don't raise error) if we don't have a column with the name in old_name.
                Defaults to False
    
            no_new_header:
                Skip creating a new row header, modify in place.
                
                ** BE CAREFUL USING THIS! **
                
                All new rows created with this header will immediately get the new name,
                in which case you won't want to call this method again.
        """
        new_header = self
        # Note: By using id(rename_map) we assume that the calling code will not change
        # the rename map after we first see it. This seems like a reasonable assumption
        # for the performance gained.
        action_tuple = ('rc', id(rename_map))
        try:
            new_header = self._actions_to_next_headers[action_tuple]
        except KeyError:
            # Results of rename not already stored, perform the renames one by one
            if isinstance(rename_map, typing.Mapping):
                for k in rename_map.keys():
                    new_header = new_header.rename_column(k, rename_map[k],
                                                          ignore_missing=ignore_missing,
                                                          no_new_header=no_new_header)
            elif rename_map is not None:  # assume it's a list of tuples
                for (old, new) in rename_map:
                    new_header = new_header.rename_column(old, new,
                                                          ignore_missing=ignore_missing,
                                                          no_new_header=no_new_header)
            # Now store the shortcut
            self._actions_to_next_headers[action_tuple] = new_header

        return new_header

    def row_remove_column(
            self,
            column_name: str,
            row: bi_etl.components.row.row.Row,
            ignore_missing: bool = False,
            ) -> RowIterationHeader:
        if column_name not in self._columns_positions:
            if not ignore_missing:
                raise self._key_error(column_name)
            return self
        else:
            # Modification of columns required
            self.get_column_position.cache_clear()
            action_tuple = ('-:', column_name)
            new_header = self.get_next_header(action_tuple)
            new_header.add_row(row)
            if new_header._action_position is None:
                position = new_header._columns_positions[column_name]
                new_header._action_position = position
                del new_header._columns_in_order[position]
                del new_header._columns_positions[column_name]
                for following_col in new_header._columns_in_order[position:]:
                    new_header._columns_positions[following_col] -= 1
                new_header._column_count = len(new_header._columns_in_order)
                if self.primary_key is not None and column_name in self.primary_key:
                    self.primary_key.remove(column_name)
            # Protected access is required here since we can't call __delitem__, it calls this method.
            # noinspection PyProtectedMember
            del row._data_values[new_header._action_position]
            return new_header

    def row_subset(
            self,
            row: bi_etl.components.row.row.Row,
            exclude: typing.Optional[typing.Iterable] = None,
            rename_map: typing.Optional[typing.Union[dict, List[tuple]]] = None,
            keep_only: typing.Optional[typing.Iterable] = None,
            ) -> bi_etl.components.row.row.Row:
        """
        Return a new row instance with a subset of the columns. Original row is not modified
        Excludes are done first, then renames and finally keep_only.

        Parameters
        ----------
        row:
            The row to subset
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
        action_1 = 's'
        action_2 = frozenset(exclude or {})
        action_3 = frozenset(keep_only or {})
        # Note: By using id(rename_map) we assume that the calling code will not change
        # the rename map after we first see it. This seems like a reasonable assumption
        # for the performance gained.
        action_4 = id(rename_map)

        action_tuple = (action_1, action_2, action_3, action_4)

        new_iteration_header = self.get_next_header(action_tuple)
        sub_row = row.__class__(iteration_header=new_iteration_header, allocate_space=False)

        if new_iteration_header._action_position is None:
            # Do the transformation for the first time
            if rename_map is not None:
                new_iteration_header.rename_columns(rename_map, no_new_header=True)
            old_positions_list = list()
            sub_pos = 0
            for parent_position, old_column_name in enumerate(self._columns_in_order):
                remove_column = True
                new_column_name = new_iteration_header._columns_in_order[sub_pos]
                if old_column_name not in exclude:
                    if keep_only is None or new_column_name in keep_only:
                        old_positions_list.append(parent_position)
                        new_iteration_header._columns_positions[new_column_name] = sub_pos
                        sub_pos += 1
                        remove_column = False
                if remove_column:
                    del new_iteration_header._columns_in_order[sub_pos]
                    del new_iteration_header._columns_positions[new_column_name]
            new_iteration_header._column_count = len(new_iteration_header._columns_in_order)
            new_iteration_header._action_position = old_positions_list
            # These should already be None unless running in the debugger, since it might have called
            # on the column_set or positioned_column_set properties.
            new_iteration_header._clear_caches()
        # Build the new row based on the _action_position details
        # Protected access is required here since we can't call setitem it calls this method.
        # noinspection PyProtectedMember
        sub_row._data_values = [row._data_values[old_pos] for old_pos in new_iteration_header._action_position]
        return sub_row

    def _add_column(
            self,
            column_name: str,
            ) -> int:
        position = self._column_count
        self._column_count += 1
        self._columns_in_order.append(column_name)
        self._columns_positions[column_name] = position
        self._clear_caches()
        return position

    def _clear_caches(self):
        self._cached_column_set = None
        self._cached_positioned_column_set = None
        self._cached_columns_in_order_tuple = None
