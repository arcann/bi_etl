"""
Created on Feb 26, 2015

@author: woodd
"""
import weakref
from datetime import datetime
import warnings
import logging
from typing import Union

import psutil
import math

from sortedcontainers.sorteddict import SortedDict

from sqlalchemy.sql.expression import bindparam

from bi_etl.exceptions import NoResultFound
from bi_etl.memory_size import get_size_gc
from bi_etl.components.row.row import Row
from bi_etl.exceptions import BeforeAllExisting
from bi_etl.exceptions import AfterExisting

__all__ = ['Lookup']


class Lookup(object):
    def __init__(self, lookup_name, lookup_keys, parent_component, config=None, **kwargs):
        self.lookup_name = lookup_name
        self.lookup_keys = lookup_keys
        self.config = config
        self.cache = None
        self.parent_component = parent_component
        self.stats = parent_component.get_unique_stats_entry(stats_id='{cls} {name}'.format(cls= self.__class__.__name__, name=self.lookup_name))
        self.log = logging.getLogger(self.__module__)
        self._remote_lookup_stmt = None
        self._row_size = None
        self.our_process = psutil.Process()
        self._first_row_process_size = None
        self._row_count_to_get_estimate_row_size = 1000        
        self._done_get_estimate_row_size = False
        self.cache_enabled = True
        self.use_value_cache = True
        self._value_cache = dict()
        
    def __repr__(self):
        return "{cls}(lookup_name={name}, lookup_keys={keys})".format(cls= self.__class__.__name__, name=self.lookup_name, keys=self.lookup_keys)
    
    def _set_log_level(self, log_level):
        self.log.setLevel(log_level)

    def get_memory_size(self) -> int:
        if self._row_size is not None:
            return self._row_size * len(self)
        else:
            if len(self) > 0:
                msg = '{lookup_name} Row size was 0 on call to get_memory_size with non zero row count ({cnt:,})'
                msg = msg.format(
                    lookup_name = self.lookup_name,
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

    def get_list_of_lookup_column_values(self, row: Row) -> list:
        lookup_values = list()

        for k in self.lookup_keys:
            lookup_values.append(row[k])
        return lookup_values

    def get_hashable_combined_key(self, row: Row):
        return tuple(self.get_list_of_lookup_column_values(row))

    def clear_cache(self) -> None:
        """
        Removes cache and resets to un-cached state
        """        
        if self.cache is not None:
            del self.cache
        self.cache = None
    
    def __len__(self) -> int:
        if self.cache is not None:
            return len(self.cache)
        else:
            return 0

    def __contains__(self, item):
        return self.cache.has_row(item)

    def init_cache(self) -> None:
        """
        Initializes the cache as empty.
        """
        if self.cache_enabled is None:
            self.cache_enabled = True
        if self.cache_enabled:         
            self.cache = dict()

    def _get_first_row_size(self, row) -> int:
        # get_size_gc is slow but shouldn't be too bad twice (once here and once below in _get_estimate_row_size)
        self._row_size = get_size_gc(row)
        # self.log.debug('First row memory size {:,} bytes (includes overhead)'.format(self._row_size ))
        
    def _check_estimate_row_size(self, force_now=False):
        if force_now or not self._done_get_estimate_row_size:
            row_cnt = len(self)        
            if force_now or row_cnt >= self._row_count_to_get_estimate_row_size:
                # Tag the estimate as done so we don't keep doing it
                self._done_get_estimate_row_size = True

                # get_size_gc is slow but shouldn't be too bad twice (once here and once above in _get_first_row_size)
                total_cache_size = get_size_gc(self.cache)
                new_row_size = math.ceil(total_cache_size / row_cnt)
                self.log.debug('{lookup_name} Row memory size now estimated at {size:,} '
                               'bytes per row using cache of {cnt:,} rows'
                               .format(lookup_name = self.lookup_name,
                                       size=new_row_size,
                                       cnt=row_cnt)
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
            if self.cache is None:
                self.init_cache()
            if not allow_update:
                if lk_tuple in self.cache:
                    raise ValueError('Key value {} already in cache and allow_update was False.'
                                     ' Possible error with the keys defined for this lookup {} {}.'
                                     .format(lk_tuple, self.lookup_name, self.lookup_keys)
                    )
            self.cache[lk_tuple] = row
            
            # Capture memory usage snapshots
            if self._row_size is None:   
                self._get_first_row_size(row)
            else:
                self._check_estimate_row_size()

    def commit(self):
        """
        Placeholder for other implementations that might need it
        """
        pass
        
    def uncache_row(self, row: Row):
        if self.cache is not None:
            try:
                lk_tuple = self.get_hashable_combined_key(row)
                del self.cache[lk_tuple]
            except KeyError:
                # This lookup uses columns not in the row provided.
                # That means it's dirty beyond repair. Wipe it out.
                warnings.warn("uncache_row called on {lookup} with insufficient values {row}"
                    .format(
                        lookup=self,
                        row=row
                    )
                )
                del self.cache
                self.cache = None

    def __iter__(self):
        """
        Iterates over rows in the lookup cache
        The rows will come out in any order.
        """
        if self.cache is not None:
            for row in self.cache.values():
                yield row

    def find_where(self, key_names: list, key_values_dict: dict, limit: int = None):
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
            
    def uncache_where(self, key_names: list, key_values_dict: dict):
        """
        Scan all cached rows (expensive) to find rows to remove.
        """
        deletes = self.find_where(key_names, key_values_dict)
        for row in deletes:
            self.uncache_row(row)

    def get_versions_collection(self, row) -> Union[Row, SortedDict]:
        """
        This method exists for compatibility with range caches

        Parameters
        ----------
        row
            The row with keys to search row

        Returns
        -------
        A single row or an SortedDict of rows
        """
        if not self.cache_enabled:
            raise ValueError("Lookup {} cache not enabled".format(self.lookup_name))
        if self.cache is None:
            self.init_cache()

        lk_tuple = self.get_hashable_combined_key(row)
        try:
            return self.cache[lk_tuple]
        except KeyError as e:
            raise NoResultFound(e)

    def find_in_cache(self, row, **kwargs):
        """
        Find a matching row in the lookup based on the lookup index (keys)
        """
        assert len(kwargs) == 0, "lookup.find_in_cache got unexpected args {}".format(kwargs)
        return self.get_versions_collection(row)

    def has_row(self, row):
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
            
    def _add_remote_stmt_where_clause(self, stmt):
        """
        Only works if parent_component is based on bi_etl.components.readonlytable
        """
        col_num = 1
        for key_col in self.lookup_keys:            
            stmt = stmt.where(self.parent_component.get_column(key_col) == bindparam('k{}'.format(col_num)))
            col_num += 1
        return stmt
        
    def _get_remote_stmt_where_values(self, row: Row) -> dict:
        values_dict = dict()
        col_num = 1
        for key_val in self.get_list_of_lookup_column_values(row):            
            values_dict['k{}'.format(col_num)] = key_val
            col_num += 1
        return values_dict
    
    def find_in_remote_table(self, row: Row) -> Row:
        """
        Find a matching row in the lookup based on the lookup index (keys)
        
        Only works if parent_component is based on bi_etl.components.readonlytable
        """
        self.stats.timer.start()        
        if self._remote_lookup_stmt is None:
            stmt = self.parent_component.select()           
            stmt = self._add_remote_stmt_where_clause(stmt)
            self._remote_lookup_stmt = stmt.compile()      
        values_dict = self._get_remote_stmt_where_values(row)     
        rows = list(self.parent_component.execute(self._remote_lookup_stmt, values_dict))
        self.stats.timer.stop()
        if len(rows) == 0:
            raise NoResultFound()
        elif len(rows) == 1:
            return self.parent_component.Row(data=rows[0])
        else:
            msg = "{lookup_name} find_in_remote_table {row} matched multiple records {rows}"
            msg = msg.format(lookup_name = self.lookup_name,
                             row=row,
                             rows=rows
                             )
            raise RuntimeError(msg)

    def _update_with_value_cache(self, row):
        for column_number, column_value in enumerate(row.values_in_order()):
            if isinstance(column_value, str) or isinstance(column_value, datetime):
                if column_value in self._value_cache:
                    row.set_by_zposition(column_number, self._value_cache[column_value])
                else:
                    self._value_cache[column_value] = column_value


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
