"""
Created on Feb 27, 2015

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import typing
from datetime import datetime

from sqlalchemy.sql.expression import bindparam
from sqlalchemy.sql.selectable import GenerativeSelect

from bi_etl.components.row.row import Row
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.conversions import ensure_datetime
from bi_etl.exceptions import BeforeAllExisting, AfterExisting, NoResultFound
from bi_etl.lookups.lookup import Lookup
from bi_etl.utility import dict_to_str

if typing.TYPE_CHECKING:
    from bi_etl.components.etlcomponent import ETLComponent


__all__ = ['RangeLookup']


class RangeLookup(Lookup):
    def __init__(self,
                 lookup_name: str,
                 lookup_keys: list,
                 parent_component: ETLComponent,
                 begin_date,
                 end_date,
                 config: BI_ETL_Config_Base = None,
                 use_value_cache: bool = True,
                 ):
        super().__init__(
            lookup_name=lookup_name,
            lookup_keys=lookup_keys,
            parent_component=parent_component,
            use_value_cache=use_value_cache,
            config=config
        )
        self.begin_date = begin_date
        self.end_date = end_date
        self._remote_lookup_stmt_no_date = None
        self._len = 0

    def __len__(self):
        return self._len

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
            versions_collection = self._cache.get(lk_tuple, None)
            effective_date = ensure_datetime(row[self.begin_date])
            assert isinstance(effective_date, datetime)
                
            if versions_collection is None:
                versions_collection = Lookup.VERSION_COLLECTION_TYPE()

            if effective_date in versions_collection:
                if not allow_update:
                    self.log.error('Key already in lookup!')
                    self.log.error(f'Existing row = {repr(versions_collection[effective_date])}')
                    self.log.error(f'New duplicate row = {repr(row)}')
                    raise ValueError(
                        f'Key {lk_tuple} + date {effective_date} already in cache and allow_update was False'
                        )
            else:
                self._len += 1
            
            versions_collection[effective_date] = row
            # TODO: Move above into if versions_collection is None so it's done only once
            self._cache[lk_tuple] = versions_collection
            
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
            versions_collection = self._cache.get(lk_tuple, None)
            effective_date = ensure_datetime(row[self.begin_date])
                
            if versions_collection:                
                # Look for and remove existing instance that are exactly the same date
                try:
                    del versions_collection[effective_date]
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
            for versions_collection in list(self._cache.values()):
                for row in versions_collection.values():
                    yield row

    def get_versions_collection(self, row: Lookup.ROW_TYPES) -> typing.MutableMapping[datetime, Row]:
        """
        This method exists for compatibility with range caches

        Parameters
        ----------
        row
            The row with keys to search row

        Returns
        -------
        A MutableMapping of rows
        """

        if isinstance(row, self._hashable_key_type):
            lk_tuple = row
        else:
            lk_tuple = self.get_hashable_combined_key(row)

        if not self.cache_enabled:
            raise ValueError(f"Lookup {self.lookup_name} cache not enabled")
        if self._cache is None:
            self.init_cache()

        try:
            versions_collection = self._cache[lk_tuple]
            return versions_collection
        except KeyError:
            raise NoResultFound()

    def find_in_cache(self, row: Lookup.ROW_TYPES, **kwargs) -> Row:
        """
        Find an existing row in the cache effective on the date provided.
        Can raise ValueError if the cache is not setup.
        Can raise NoResultFound if the key is not in the cache.
        Can raise BeforeAllExisting is the effective date provided is before all existing records.
        """
        effective_date = kwargs.get('effective_date')
        if effective_date is None:
            effective_date = ensure_datetime(row[self.begin_date])

        versions_collection = self.get_versions_collection(row)
        try:
            return self._get_version(versions_collection, effective_date)
        except TypeError as e:
            # noinspection PyTypeChecker
            raise TypeError(
                f"{e}\n"
                f"versions_collection = {versions_collection}\n"
                f"versions_collection key[0]= {next(versions_collection.keys())}\n"
                f"effective_date = {effective_date}"
            )
                
    def _add_remote_stmt_where_clause(self, stmt: GenerativeSelect) -> GenerativeSelect:
        stmt = super(RangeLookup, self)._add_remote_stmt_where_clause(stmt)
        # noinspection PyUnresolvedReferences
        stmt = stmt.where(bindparam('eff_date') >= self.parent_component.get_column(self.begin_date))
        # noinspection PyUnresolvedReferences
        stmt = stmt.where(bindparam('eff_date') <= self.parent_component.get_column(self.end_date))
        return stmt

    def _get_remote_stmt_where_values(
            self,
            row: Lookup.ROW_TYPES,
            effective_date: datetime = None,
            ) -> dict:
        values_dict = super(RangeLookup, self)._get_remote_stmt_where_values(row)
        if effective_date is None:
            if isinstance(row, tuple) or isinstance(row, list):
                effective_date_value_name = f'k{len(row)}'
                effective_date = ensure_datetime(values_dict[effective_date_value_name])
                del values_dict[effective_date_value_name]
            else:
                effective_date = ensure_datetime(row[self.begin_date])
        values_dict['eff_date'] = effective_date
        return values_dict
    
    def find_in_remote_table(
            self,
            row: Lookup.ROW_TYPES,
            **kwargs
            ) -> Row:
        """
        Find a matching row in the lookup based on the lookup index (keys)
        
        Only works if parent_component is based on bi_etl.components.readonlytable
        """

        effective_date = kwargs.get('effective_date')

        from bi_etl.components.readonlytable import ReadOnlyTable
        if not isinstance(self.parent_component, ReadOnlyTable):
            raise ValueError(
                "find_in_remote_table requires that parent_component be ReadOnlyTable. "
                f" got {repr(self.parent_component)}"
            )

        parent_table: ReadOnlyTable = self.parent_component
        
        if self._remote_lookup_stmt is None:
            stmt = parent_table.select()
            stmt = self._add_remote_stmt_where_clause(stmt)
            self._remote_lookup_stmt = stmt.compile(bind=self.parent_component.database.bind)
            # Build a second statement that does the lookup without dates
            # Which is what our parent Lookup does, so we call that
            stmt_no_date = parent_table.select()
            stmt_no_date = super(RangeLookup, self)._add_remote_stmt_where_clause(stmt_no_date)
            # order by the begin date
            stmt_no_date = stmt_no_date.order_by(parent_table.get_column(self.begin_date))
            self._remote_lookup_stmt_no_date = stmt_no_date.compile(bind=self.parent_component.database.bind)

        values_dict = self._get_remote_stmt_where_values(row, effective_date)

        rows = list(parent_table.execute(self._remote_lookup_stmt, values_dict))
        if len(rows) == 0:
            # Use the second statement that does the lookup without dates
            # Which is what our parent Lookup does, so we call that to set values
            values_dict = super(RangeLookup, self)._get_remote_stmt_where_values(row)
            results = parent_table.execute(self._remote_lookup_stmt_no_date, values_dict)
            all_key_rows = results.fetchall()
            if len(all_key_rows) == 0:
                raise NoResultFound()
            else:
                row_counter = 0
                for row in all_key_rows:
                    row_counter += 1
                    if row_counter == 1 and effective_date < row[self.begin_date]:
                        raise BeforeAllExisting(self.parent_component.Row(row), effective_date=row[self.begin_date])
                    elif (ensure_datetime(row[self.begin_date])
                          >= ensure_datetime(effective_date)
                          >= ensure_datetime(row[self.end_date])
                          ):
                        return row
                # If we reach this point return the last row in an AfterExisting exception
                raise AfterExisting(prior_row=row, effective_date=effective_date)

        elif len(rows) == 1:
            return self.parent_component.Row(rows[0])
        else:
            msg = (
                f'dict_to_str statement {self._remote_lookup_stmt}\n'
                f'using keys {dict_to_str(values_dict)}\n'
                'matched multiple records: \n'
            )
            row_cnt = 0
            for r in rows:
                row_cnt += 1
                if row_cnt >= 10:
                    msg += '...'
                    break
                msg += dict_to_str(self.get_list_of_lookup_column_values(r), depth=2)
                msg += '\n--------------------------\n' 
            raise RuntimeError(msg)

    def find_versions_list_in_remote_table(self, row: Lookup.ROW_TYPES) -> list:
        """
        Find a matching row in the lookup based on the lookup index (keys)

        Only works if parent_component is based on bi_etl.components.readonlytable
        """
        from bi_etl.components.readonlytable import ReadOnlyTable
        if not isinstance(self.parent_component, ReadOnlyTable):
            raise ValueError(
                "find_versions_list_in_remote_table requires that parent_component be ReadOnlyTable. "
                f" got {repr(self.parent_component)}"
            )

        self.stats.timer.start()
        if self._remote_lookup_stmt_no_date is None:
            # noinspection PyUnresolvedReferences
            stmt = self.parent_component.select()
            # Call parent _add_remote_stmt_where_clause so that it doesn't add the date filter
            stmt = super()._add_remote_stmt_where_clause(stmt)
            stmt = stmt.order_by(self.begin_date)
            self._remote_lookup_stmt_no_date = stmt.compile(bind=self.parent_component.database.bind)

        values_dict = super()._get_remote_stmt_where_values(row)

        # noinspection PyUnresolvedReferences
        result = list(self.parent_component.execute(self._remote_lookup_stmt_no_date, values_dict))
        rows = list()
        for result_proxy_row in result:
            row = self.parent_component.Row(data=result_proxy_row)
            rows.append(row)
        self.stats.timer.stop()
        if len(rows) == 0:
            raise NoResultFound()
        else:
            return rows
