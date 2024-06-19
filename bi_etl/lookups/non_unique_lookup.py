"""
Created on Feb 27, 2015

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import typing

from bi_etl.components.row.row import Row
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.exceptions import NoResultFound
from bi_etl.lookups.lookup import Lookup

if typing.TYPE_CHECKING:
    from bi_etl.components.etlcomponent import ETLComponent

__all__ = ['NonUniqueLookup']


class NonUniqueLookup(Lookup):
    def __init__(self,
                 lookup_name: str,
                 lookup_keys: list,
                 parent_component: ETLComponent,
                 config: BI_ETL_Config_Base = None,
                 use_value_cache: bool = True,
                 value_for_none='<None>',  # Needs to be comparable to datatypes in the key actual None is not.
                 ):
        super(NonUniqueLookup, self).__init__(
            lookup_name=lookup_name,
            lookup_keys=lookup_keys,
            parent_component=parent_component,
            use_value_cache=use_value_cache,
            config=config,
            )
        self.value_for_none = value_for_none
        self._remote_lookup_stmt_no_date = None
        self._len = 0

    def __len__(self):
        return self._len

    def get_list_of_lookup_column_values(self, row: Lookup.ROW_TYPES) -> list:
        results = super().get_list_of_lookup_column_values(row)

        # We expect that non-unique lookups might have nulls, we need to eliminate those
        results_2 = list()
        for value in results:
            if value is None:
                value = self.value_for_none
            results_2.append(value)

        return results_2

    def cache_row(
            self,
            row: Row,
            allow_update: bool = True,
            allow_insert: bool = True,
    ):
        """
        Adds the given row to the cache for this lookup.

        Parameters
        ----------
        row: Row
            The row to cache

        allow_update: boolean
            Allow this method to update an existing row in the cache.

        allow_insert: boolean
            Allow this method to insert a new row into the cache

        Raises
        ------
        ValueError
            If allow_update is False and an already existing row (lookup key) is passed in.

        """
        if self.cache_enabled:
            assert isinstance(row, Row), f"cache_row requires Row and not {type(row)}"

            if self.use_value_cache:
                self._update_with_value_cache(row)

            lk_tuple = self.get_hashable_combined_key(row)
            if self._cache is None:
                self.init_cache()
            matching_rows = self._cache.get(lk_tuple, None)
            try:
                # noinspection PyUnresolvedReferences
                primary_key = self.parent_component.get_primary_key_value_tuple(row)
                assert isinstance(primary_key, tuple)
            except KeyError:
                primary_key = None
            except AttributeError as e:
                raise ValueError(f"The lookup parent_component needs to be a ReadOnlyTable or related child (needs get_primary_key_value_tuple method) {e}")

            if matching_rows is None:
                matching_rows = Lookup.VERSION_COLLECTION_TYPE()
                self._cache[lk_tuple] = matching_rows

            try:
                if primary_key is None:
                    self._len += 1
                    matching_rows[self._len] = row
                elif primary_key in matching_rows:
                    if allow_update:
                        matching_rows[primary_key] = row
                    else:
                        self.log.error('Key already in lookup!')
                        self.log.error(f'Existing row = {repr(matching_rows[primary_key])}')
                        self.log.error(f'New duplicate row = {repr(row)}')
                        raise ValueError(f'Key {lk_tuple} + primary_key {primary_key} already in cache and allow_update was False')
                else:
                    self._len += 1
                    matching_rows[primary_key] = row
            except TypeError:
                raise

            # Capture memory usage snapshots
            if self._row_size is None:
                self._get_first_row_size(row)
            else:
                self.check_estimate_row_size()

    def uncache_row(self, row: Lookup.ROW_TYPES):
        if isinstance(row, tuple) or isinstance(row, list):
            raise ValueError(
                f"{self.__class__.__name__}.uncache_row requires a Row not a tuple since it needs the date"
                )
        else:
            lk_tuple = self.get_hashable_combined_key(row)
        if self._cache is not None:
            existing_rows = self._cache.get(lk_tuple, None)
            # noinspection PyUnresolvedReferences
            primary_key = self.parent_component.get_primary_key_value_tuple(row)
            assert isinstance(primary_key, tuple)

            if existing_rows:
                # Look for and remove existing instance that are exactly the same date
                try:
                    del existing_rows[primary_key]
                except (KeyError, ValueError):
                    # Not found, that's OK
                    pass

    def uncache_set(self, row: Lookup.ROW_TYPES):
        if self._cache is not None:
            if isinstance(row, self._hashable_key_type):
                lk_tuple = row
            else:
                lk_tuple = self.get_hashable_combined_key(row)
            del self._cache[lk_tuple]

    def __iter__(self):
        """
        The natural keys will come out in any order. However, the versions within a natural key set will come out in ascending order.
        """
        if self._cache is not None:
            for row_list in list(self._cache.values()):
                for row in row_list.values():
                    yield row

    def find_in_cache(self, row: Lookup.ROW_TYPES, **kwargs) -> Row:
        """
        Find an existing row in the cache effective on the date provided.
        Can raise ValueError if the cache is not setup.
        Can raise NoResultFound if the key is not in the cache.
        Can raise BeforeAllExisting is the effective date provided is before all existing records.
        """
        matches = self.find_matches_in_cache(row, **kwargs)
        if len(matches) != 1:
            raise ValueError(f"Multiple matches ({len(matches)}) found for find_in_cache. Matches are {matches}")
        else:
            return matches[0]

    def find_matches_in_cache(self, row: Lookup.ROW_TYPES, **kwargs) -> typing.Sequence[Row]:
        """
        Find an existing row in the cache effective on the date provided.
        Can raise ValueError if the cache is not setup.
        Can raise NoResultFound if the key is not in the cache.
        Can raise BeforeAllExisting is the effective date provided is before all existing records.
        """
        assert self.cache_enabled, f"Cache not enabled for {self}"
        assert self._cache is not None, f"Cache not created for {self}"
        if isinstance(row, self._hashable_key_type):
            lk_tuple = row
            primary_key = None
        elif isinstance(row, list) or isinstance(row, tuple):
            lk_tuple = self._hashable_key_type(row)
            primary_key = None
        else:
            lk_tuple = self.get_hashable_combined_key(row)
            try:
                # noinspection PyUnresolvedReferences
                primary_key = self.parent_component.get_primary_key_value_tuple(row)
            except AttributeError as e:
                raise ValueError(f"The lookup parent_component needs to be a ReadOnlyTable or related child (needs get_primary_key_value_tuple method) {e}")
        matching_rows = self._cache.get(lk_tuple, None)
        if matching_rows is None:
            raise NoResultFound()

        if primary_key is None:
            return list(matching_rows.values())
        else:
            try:
                return [matching_rows[primary_key]]
            except KeyError as e:
                raise TypeError(
                    f"{e}\n"
                    f"matching_rows = {matching_rows}\n"
                    f"matching_rows key[0]= {next(matching_rows.keys())}\n"
                    f"primary_key = {primary_key}"
                )

    def find_in_remote_table(self, row: Lookup.ROW_TYPES, **kwargs) -> Row:
        """
        Find a matching row in the lookup based on the lookup index (keys)

        Only works if parent_component is based on bi_etl.components.readonlytable
        """
        raise NotImplementedError()

    def find_versions_list_in_remote_table(self, row: Lookup.ROW_TYPES) -> typing.Sequence[Row]:
        """
        Find a matching row in the lookup based on the lookup index (keys)

        Only works if parent_component is based on bi_etl.components.readonlytable
        """
        from bi_etl.components.readonlytable import ReadOnlyTable
        if not isinstance(self.parent_component, ReadOnlyTable):
            raise ValueError(
                "find_in_remote_table requires that parent_component be ReadOnlyTable. "
                f" got {repr(self.parent_component)}"
            )

        self.stats.timer.start()
        if self._remote_lookup_stmt is None:
            stmt = self.parent_component.select()
            stmt = super()._add_remote_stmt_where_clause(stmt)
            stmt = stmt.order_by(self.parent_component.primary_key)
            self._remote_lookup_stmt = stmt.compile(bind=self.parent_component.database.bind)

        values_dict = super()._get_remote_stmt_where_values(row)

        # noinspection PyUnresolvedReferences
        result = list(self.parent_component.execute(self._remote_lookup_stmt, values_dict))
        rows = list()
        for result_proxy_row in result:
            row = self.parent_component.Row(data=result_proxy_row)
            rows.append(row)
        self.stats.timer.stop()
        if len(rows) == 0:
            raise NoResultFound()
        else:
            return rows
