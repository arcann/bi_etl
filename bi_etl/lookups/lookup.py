"""
Created on Feb 26, 2015

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations
import logging
import sys

import math
import traceback
import warnings
from configparser import ConfigParser
from datetime import datetime
import typing

import psutil
from BTrees.OOBTree import OOBTree
from sqlalchemy.sql import Selectable
from sqlalchemy.sql.expression import bindparam

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_status import RowStatus
from bi_etl.conversions import ensure_datetime
from bi_etl.exceptions import AfterExisting
from bi_etl.exceptions import BeforeAllExisting
from bi_etl.exceptions import NoResultFound
from bi_etl.memory_size import get_size_gc
from bi_etl.statistics import Statistics

if typing.TYPE_CHECKING:
    from bi_etl.components.etlcomponent import ETLComponent

__all__ = ['Lookup']


class Lookup(object):
    COLLECTION_INDEX = datetime(year=1900, month=1, day=1, hour=0, minute=0, second=0)
    ROW_TYPES = typing.Union[Row, typing.Sequence]
    DB_LOOKUP_WARNING = 1000

    def __init__(self,
                 lookup_name: str,
                 lookup_keys: list,
                 parent_component: ETLComponent,
                 config: ConfigParser = None,
                 use_value_cache: bool = True,
                 **kwargs):
        self.lookup_name = lookup_name
        self.lookup_keys = lookup_keys
        self.config = config
        self._cache = None
        self.parent_component = parent_component
        self.stats = parent_component.get_unique_stats_entry(
            stats_id='{cls} {name}'.format(cls=self.__class__.__name__, name=self.lookup_name)
        )
        self.log = logging.getLogger(self.__module__)
        self._remote_lookup_stmt = None
        self._row_size = None
        self.our_process = psutil.Process()
        self._first_row_process_size = None
        self._row_count_to_get_estimate_row_size = 1000        
        self._done_get_estimate_row_size = False
        self.cache_enabled = True
        self.use_value_cache = use_value_cache
        self._value_cache_str = dict()
        self._value_cache_str_usage = dict()
        self._value_cache_datetime = dict()
        self._value_cache_datetime_usage = dict()
        # OOBTree.BTree is now used instead of SortedDict
        # It ran tests in 80% of the time of the SortedDict equivalent
        # http://pythonhosted.org/BTrees/index.html
        # self.version_collection_type = SortedDict
        self.version_collection_type = OOBTree
        self._hashable_key_type = tuple
        self._fallback_to_db_count = 0

    # noinspection PyUnresolvedReferences
    def _get_version(self, versions_collection: MutableMapping[datetime, Row], effective_date: datetime):
        # SortedDict version
        # first_effective_index = versions_collection.bisect_right(effective_date) - 1
        # if first_effective_index <= -1:
        #    raise BeforeAllExisting(versions_collection[versions_collection.iloc[0]], effective_date)
        try:
            first_effective_index = versions_collection.maxKey(effective_date)
        except ValueError:
            raise BeforeAllExisting(versions_collection[versions_collection.minKey()], effective_date)
        first_effective_row = versions_collection[first_effective_index]
        # Check that record doesn't end before our date
        if ensure_datetime(first_effective_row[self.end_date]) < effective_date:
            raise AfterExisting(first_effective_row, effective_date)
        return first_effective_row
        
    def __repr__(self):
        return "{cls}(lookup_name={name}, lookup_keys={keys})".format(cls=self.__class__.__name__, name=self.lookup_name, keys=self.lookup_keys)
    
    def _set_log_level(self, log_level):
        self.log.setLevel(log_level)

    def estimated_row_size(self):
        return self._row_size

    def has_done_get_estimate_row_size(self):
        return self._done_get_estimate_row_size

    def get_memory_size(self) -> int:
        if self._row_size is not None:
            return self._row_size * len(self)
        else:
            if len(self) > 0:
                msg = '{lookup_name} Row size was 0 on call to get_memory_size with non zero row count ({cnt:,})'
                msg = msg.format(
                    lookup_name=self.lookup_name,
                    cnt=len(self)
                )
                self.log.warning(msg)
            return 0

    def get_disk_size(self) -> int:
        return 0
    
    def add_size_to_stats(self) -> None:
        self.stats['Final Row Count'] = len(self)
        self.stats['Memory Size'] = self.get_memory_size()
        self.stats['Disk Size'] = self.get_disk_size()

    def get_list_of_lookup_column_values(self, row: ROW_TYPES) -> list:
        if isinstance(row, tuple):
            return list(row)
        elif isinstance(row, list):
            return row
        else:
            lookup_values = [row[k] for k in self.lookup_keys]
            return lookup_values

    def get_hashable_combined_key(self, row: ROW_TYPES) -> typing.Sequence:
        if isinstance(row, self._hashable_key_type):
            return row
        elif isinstance(row, tuple):
            return self._hashable_key_type(row)
        elif isinstance(row, list):
            return self._hashable_key_type(tuple(row))
        else:
            if self._hashable_key_type == tuple:
                return self._hashable_key_type(self.get_list_of_lookup_column_values(row))
            else:
                return self._hashable_key_type(tuple(self.get_list_of_lookup_column_values(row)))

    def clear_cache(self) -> None:
        """
        Removes cache and resets to un-cached state
        """        
        if self._cache is not None:
            del self._cache
        self._cache = None
    
    def __len__(self) -> int:
        if self._cache is not None:
            return len(self._cache)
        else:
            return 0

    def __contains__(self, item):
        return self.has_row(item)

    def init_cache(self) -> None:
        """
        Initializes the cache as empty.
        """
        if self.cache_enabled is None:
            self.cache_enabled = True
        if self.cache_enabled:         
            self._cache = dict()

    def _get_first_row_size(self, row) -> int:
        # get_size_gc is slow but shouldn't be too bad twice (once here and once below in _get_estimate_row_size)
        self._row_size = get_size_gc(row)
        # self.log.debug('First row memory size {:,} bytes (includes overhead)'.format(self._row_size ))
        return self._row_size
        
    def check_estimate_row_size(self, force_now=False):
        if force_now or not self._done_get_estimate_row_size:
            row_cnt = len(self)        
            if force_now or row_cnt >= self._row_count_to_get_estimate_row_size:
                # Tag the estimate as done so we don't keep doing it
                self._done_get_estimate_row_size = True

                # get_size_gc is slow but shouldn't be too bad twice (once here and once above in _get_first_row_size)
                total_cache_size = get_size_gc(self._cache)
                new_row_size = math.ceil(total_cache_size / row_cnt)
                self.log.debug(
                    f'{self.lookup_name} Row memory size now estimated at {new_row_size:,} '
                    f'bytes per row using cache of {row_cnt:,} rows'
                )
                
                self._row_size = new_row_size     

    def cache_row(self, row: Row, allow_update: bool = True):
        """
        Adds the given row to the cache for this lookup.
        
        Parameters
        ----------
        row: Row
            The row to cache
            
        allow_update: boolean
            Allow this method to update an existing row in the cache.
            
        Raises
        ------
        ValueError
            If allow_update is False and an already existing row (lookup key) is passed in.
        
        """        
        if self.cache_enabled:
            assert isinstance(row, Row), "cache_row requires Row and not {}".format(type(row))

            if self.use_value_cache:
                self._update_with_value_cache(row)

            lk_tuple = self.get_hashable_combined_key(row)
            if self._cache is None:
                self.init_cache()
            if not allow_update:
                if lk_tuple in self._cache:
                    raise ValueError(
                        f'Key value {lk_tuple} already in cache and allow_update was False.'
                        f' Possible error with the keys defined for this lookup {self.lookup_name} {self.lookup_keys}.'
                    )
            self._cache[lk_tuple] = row
            
            # Capture memory usage snapshots
            if self._row_size is None:   
                self._get_first_row_size(row)
            else:
                self.check_estimate_row_size()

    def cache_set(
            self,
            lk_tuple: tuple,
            version_collection: typing.MutableMapping[datetime, Row],
            allow_update: bool = True
            ):
        """
        Adds the given set of rows to the cache for this lookup.

        Parameters
        ----------
        lk_tuple:
            The key tuple to store the rows under

        version_collection:
            The set of rows to cache

        allow_update: boolean
            Allow this method to update an existing row in the cache.

        Raises
        ------
        ValueError
            If allow_update is False and an already existing row (lookup key) is passed in.

        """
        if self.cache_enabled:
            assert isinstance(version_collection, self.version_collection_type), "cache_row requires {} and not {}".format(self.version_collection_type, type(version_collection))

            if self.use_value_cache:
                for row in version_collection.values():
                    self._update_with_value_cache(row)

            if self._cache is None:
                self.init_cache()
            if not allow_update:
                if lk_tuple in self._cache:
                    raise ValueError('Key value {} already in cache and allow_update was False.'
                                     ' Possible error with the keys defined for this lookup {} {}.'
                                     .format(lk_tuple, self.lookup_name, self.lookup_keys)
                                     )
            self._cache[lk_tuple] = version_collection

            # Capture memory usage snapshots
            if self._row_size is None:
                self._get_first_row_size(version_collection)
            else:
                self.check_estimate_row_size()

    def commit(self):
        """
        Placeholder for other implementations that might need it
        """
        pass
        
    def uncache_row(self, row: ROW_TYPES):
        if self._cache is not None:
            try:
                lk_tuple = self.get_hashable_combined_key(row)
            except KeyError as e:
                # This lookup uses columns not in the row provided.
                raise ValueError(f"uncache_row called on {self} with insufficient values {row}. {e}")
            try:
                del self._cache[lk_tuple]
            except KeyError as e:
                pass

    def uncache_set(self, row: ROW_TYPES):
        self.uncache_row(row)

    def __iter__(self) -> typing.Iterable[Row]:
        """
        Iterates over rows in the lookup cache.  Returns clones of rows in case they are modified.

        The rows will come out in any order.
        """
        if self._cache is not None:
            for row in self._cache.values():
                # Do not return the actual instance of the row since the caller might modify it to no longer be
                # compatible with the parent table
                yield row.clone()

    def _iter_raw(self) -> typing.Iterable[Row]:
        """
        Iterates over rows in the lookup cache. Returns actual cached rows. Be careful! Direct modifications to
        the cached rows could break the later use of the cache.

        The rows will come out in any order.
        :return:
        """
        if self._cache is not None:
            for row in self._cache.values():
                yield row

    def find_where(
            self,
            key_names: typing.Sequence,
            key_values_dict: typing.Mapping,
            limit: int = None
            ):
        """
        Scan all cached rows (expensive) to find list of rows that match criteria.
        """
        results = list()
        for row in self:
            matches = True
            for key in key_names:
                if row[key] != key_values_dict[key]:
                    matches = False
                    break
            if matches:
                results.append(row)
                if limit is not None and len(results) >= limit:
                    break
        return results
            
    def uncache_where(
            self,
            key_names: typing.Sequence,
            key_values_dict: typing.Mapping):
        """
        Scan all cached rows (expensive) to find rows to remove.
        """
        deletes = self.find_where(key_names, key_values_dict)
        for row in deletes:
            self.uncache_row(row)

    def get_versions_collection(
            self,
            row: ROW_TYPES
            ) -> typing.MutableMapping[datetime, Row]:
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
        if not self.cache_enabled:
            raise ValueError("Lookup {} cache not enabled".format(self.lookup_name))
        if self._cache is None:
            self.init_cache()

        lk_tuple = self.get_hashable_combined_key(row)
        try:
            return self.version_collection_type({Lookup.COLLECTION_INDEX: self._cache[lk_tuple]})
        except KeyError as e:
            raise NoResultFound(e)

    def find_in_cache(self, row: ROW_TYPES, **kwargs) -> Row:
        """
        Find a matching row in the lookup based on the lookup index (keys)
        """
        assert len(kwargs) == 0, "lookup.find_in_cache got unexpected args {}".format(kwargs)
        versions_collection = self.get_versions_collection(row)
        return versions_collection[Lookup.COLLECTION_INDEX]

    def find_matches_in_cache(self, row: ROW_TYPES, **kwargs) -> typing.Sequence[Row]:
        return list(self.find_in_cache(row, **kwargs))

    def has_row(self, row: ROW_TYPES) -> bool:
        """
        Does the row exist in the cache (for any date if it's a date range cache)

        Parameters
        ----------
        row

        Returns
        -------

        """
        try:
            self.get_versions_collection(row)
        except (NoResultFound, BeforeAllExisting, AfterExisting):
            return False
        return True
            
    def _add_remote_stmt_where_clause(self, stmt: Selectable) -> Selectable:
        """
        Only works if parent_component is based on bi_etl.components.readonlytable
        """
        col_num = 1
        for key_col in self.lookup_keys:
            # This statement only works if parent_component is based on bi_etl.components.readonlytable
            # noinspection PyUnresolvedReferences
            stmt = stmt.where(self.parent_component.get_column(key_col) == bindparam('k{}'.format(col_num)))
            col_num += 1
        return stmt

    def _get_remote_stmt_where_values(
            self,
            row: ROW_TYPES,
            effective_date: datetime = None,
            ) -> dict:
        values_dict = dict()
        col_num = 1
        values_list = self.get_list_of_lookup_column_values(row)

        for key_val in values_list:
            values_dict['k{}'.format(col_num)] = key_val
            col_num += 1
        return values_dict

    def find_in_remote_table(
            self,
            row: ROW_TYPES,
            **kwargs
            ) -> Row:
        """
        Find a matching row in the lookup based on the lookup index (keys)
        
        Only works if parent_component is based on bi_etl.components.readonlytable

        Parameters
        ----------
        row
            The row with keys to search row

        Returns
        -------
        A row
        """
        assert hasattr(self.parent_component, 'execute'), f'ReadOnlyTable or class with execute method needed for DB lookup {type(self.parent_component)} will not work'

        self.stats.timer.start()        
        if self._remote_lookup_stmt is None:
            # noinspection PyUnresolvedReferences
            stmt = self.parent_component.select()
            stmt = self._add_remote_stmt_where_clause(stmt)
            self._remote_lookup_stmt = stmt.compile()

        values_dict = self._get_remote_stmt_where_values(row)

        # noinspection PyUnresolvedReferences
        rows = list(self.parent_component.execute(self._remote_lookup_stmt, values_dict))
        self.stats.timer.stop()
        if len(rows) == 0:
            raise NoResultFound()
        elif len(rows) == 1:
            # noinspection PyUnresolvedReferences
            return self.parent_component.Row(data=rows[0])
        else:
            msg = "{lookup_name} find_in_remote_table {row} matched multiple records {rows}"
            msg = msg.format(lookup_name=self.lookup_name,
                             row=row,
                             rows=rows
                             )
            raise RuntimeError(msg)

    def find_versions_list_in_remote_table(self, row: ROW_TYPES) -> list:
        return [self.find_in_remote_table(row)]

    def find_versions_list(
            self,
            row: ROW_TYPES,
            fallback_to_db: bool = True,
            maintain_cache: bool = True,
            stats: Statistics = None,
            ) -> list:
        """

        Parameters
        ----------
        row:
            row or tuple to find
        fallback_to_db:
            Use db to search if not found in cached copy
        maintain_cache:
            Add DB lookup rows to the cached copy?
        stats:
            Statistics to maintain

        Returns
        -------
        A MutableMapping of rows
        """
        if self.cache_enabled:
            try:
                rows = list(self.get_versions_collection(row).values())
                if stats is not None:
                    stats['Found in cache'] += 1
                    stats.timer.stop()
                return rows
            except NoResultFound as e:
                if stats is not None:
                    stats['Not in cache'] += 1
                if not fallback_to_db:
                    #  Don't pass onto SQL if the lookup cache has initialized but the value isn't there
                    if stats is not None:
                        stats.timer.stop()
                    raise e
                    # Otherwise we'll continue to the DB query below
            except (KeyError, ValueError):
                if stats is not None:
                    stats['Cache not setup'] += 1
                # Lookup not cached. Allow database lookup to proceed, but give warning since we thought it was cached
                warnings.warn("WARNING: {lkp} caching is enabled, but find_in_cache returned error {e}".format(
                    lkp=self,
                    e=traceback.format_exc()
                )
                )
            except AfterExisting as e:
                stats['After all in cache'] += 1
                if stats is not None:
                    stats['Not in cache'] += 1
                if not fallback_to_db:
                    #  Don't pass onto SQL if the lookup cache has initialized but the value isn't there
                    stats.timer.stop()
                    # return the last existing row since that what we'll update
                    return e.prior_row
                    # Otherwise we'll continue to the DB query below
                    # BeforeExisting exceptions are returned to the caller

        # Do a lookup on the database
        try:
            if stats is not None:
                stats['DB lookup performed'] += 1
            rows = self.find_versions_list_in_remote_table(row)
            for row in rows:
                row.status = RowStatus.existing
                if maintain_cache and self.cache_enabled:
                    self.cache_row(row, allow_update=False)
                if stats is not None:
                    stats['DB lookup found row'] += 1
        finally:
            if stats is not None:
                stats.timer.stop()
        return rows

    def find(self,
             row: ROW_TYPES,
             fallback_to_db: bool = True,
             maintain_cache: bool = True,
             stats: Statistics = None,
             **kwargs
             ) -> Row:
        if self.cache_enabled:
            try:
                row = self.find_in_cache(row, **kwargs)
                if stats is not None:
                    stats['Found in cache'] += 1
                    stats.timer.stop()
                return row
            except NoResultFound as e:
                if stats is not None:
                    stats['Not in cache'] += 1
                if fallback_to_db:
                    self._fallback_to_db_count += 1
                    if (self._fallback_to_db_count % self.DB_LOOKUP_WARNING) == 0:
                        self.log.warning(f"{self} has done {self._fallback_to_db_count} lookups on the DB due to fallback_to_db")
                else:
                    #  Don't pass onto SQL if the lookup cache has initialized but the value isn't there
                    if stats is not None:
                        stats.timer.stop()
                    raise e
                    # Otherwise we'll continue to the DB query below
            except (KeyError, ValueError):
                if stats is not None:
                    stats['Cache not setup'] += 1
                # Lookup not cached. Allow database lookup to proceed, but give warning since we thought it was cached
                warnings.warn("WARNING: {lkp} caching is enabled, but find_in_cache returned error {e}".format(
                    lkp=self,
                    e=traceback.format_exc()
                )
                )
            except AfterExisting as e:
                stats['After all in cache'] += 1
                if stats is not None:
                    stats['Not in cache'] += 1

                if fallback_to_db:
                    if (stats['Not in cache'] % self.DB_LOOKUP_WARNING) == 0:
                        self.log.warning(
                            f"{self} has done {stats['Not in cache']} lookups on the DB due to fallback_to_db")
                else:
                    #  Don't pass onto SQL if the lookup cache has initialized but the value isn't there
                    stats.timer.stop()
                    # return the last existing row since that what we'll update
                    return e.prior_row
                    # Otherwise we'll continue to the DB query below
                    # BeforeExisting exceptions are returned to the caller

        # Do a lookup on the database
        try:
            if stats is not None:
                stats['DB lookup performed'] += 1
            row = self.find_in_remote_table(row, **kwargs)
            row.status = RowStatus.existing
            if maintain_cache and self.cache_enabled:
                self.cache_row(row, allow_update=False)
            if stats is not None:
                stats['DB lookup found row'] += 1
        finally:
            if stats is not None:
                stats.timer.stop()
        return row

    def _update_with_value_cache(self, row):
        """
        Update a row with str and datetime de-duplication references

        :param row:
        :return:
        """
        for column_number, column_value in enumerate(row.values_in_order()):
            if isinstance(column_value, str):
                if column_value in self._value_cache_str:
                    # Replace with value cache reference
                    row.set_by_zposition_unsafe(column_number, self._value_cache_str[column_value])
                    self._value_cache_str_usage[column_value] += 1
                else:
                    # Add to value cache
                    self._value_cache_str[column_value] = column_value
                    self._value_cache_str_usage[column_value] = 0
            elif isinstance(column_value, datetime):
                if column_value in self._value_cache_datetime:
                    # Replace with value cache reference
                    row.set_by_zposition_unsafe(column_number, self._value_cache_datetime[column_value])
                    self._value_cache_datetime_usage[column_value] += 1
                else:
                    # Don't bother adding microsecond level datetime values to the dict
                    # It will perform better if smaller
                    if column_value.microsecond in {0, 999990, 999999}:
                        # Add to value cache
                        self._value_cache_datetime[column_value] = column_value
                        self._value_cache_datetime_usage[column_value] = 0

    @staticmethod
    def _str_report_on_value_cache_usage(lookup_name: str, type_name: str, value_cache: dict) -> str:
        key_count = len(value_cache)
        if key_count > 0:
            max_usage = max(value_cache.values())
            total_usage = sum(value_cache.values())
            total_bytes_saved = sum([sys.getsizeof(key) * value for key, value in value_cache.items()])
            return f'{lookup_name} {type_name} value cache stored {key_count:,} values. Max key usage = {max_usage:,}. Avg key usage = {100.0 * total_usage / key_count :.2f}%. total_bytes_saved = {total_bytes_saved:,}'
        else:
            return f'{lookup_name} {type_name} value cache stored no values in cache'

    def report_on_value_cache_effectiveness(self, lookup_name: str = None):
        if lookup_name is None:
            lookup_name = self.lookup_name
        self.log.info(self._str_report_on_value_cache_usage(lookup_name, 'str', self._value_cache_str_usage))
        self.log.info(self._str_report_on_value_cache_usage(lookup_name, 'datetime', self._value_cache_datetime_usage))


def test():
    from _datetime import datetime
    from bi_etl.timer import Timer
    from bi_etl.tests.dummy_etl_component import DummyETLComponent
    from bi_etl.components.row.row_iteration_header import RowIterationHeader
    from bi_etl.components.row.row import Row

    iteration_header = RowIterationHeader()
    data = list()
    rows_to_use = 100000
    for i in range(rows_to_use):
        row = Row(iteration_header,
                  data={'col1': i,
                        'col2': 'Two',
                        'col3': datetime(2012, 1, 3, 12, 25, 33),
                        'col4': 'All good pickles',
                        'col5': 123.23,
                        'col6': 'This is a long value. It should be ok.',
                        })
        data.append(row)

    parent_component = DummyETLComponent(data=data)
    dc = Lookup("test", ['col1'], parent_component=parent_component)
    dc.ram_check_row_interval = rows_to_use // 2
    dc.max_process_ram_usage_mb = 1
    start_time = Timer()
    for row in parent_component:
        dc.cache_row(row)
    print(start_time.seconds_elapsed_formatted)


if __name__ == "__main__":
    test()
