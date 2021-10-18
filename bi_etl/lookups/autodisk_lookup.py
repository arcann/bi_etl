# -*- coding: utf-8 -*-
"""
Created on Jan 5, 2016

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import typing

import gc
from configparser import ConfigParser
from datetime import datetime

import psutil
from bi_etl.components.row.row import Row

from bi_etl.exceptions import NoResultFound
from bi_etl.lookups.disk_lookup import DiskLookup
from bi_etl.lookups.lookup import Lookup
from bi_etl.timer import Timer

if typing.TYPE_CHECKING:
    from bi_etl.components.etlcomponent import ETLComponent

__all__ = ['AutoDiskLookup']


class AutoDiskLookup(Lookup):
    """
    Automatic memory / disk lookup cache.
    
    This version divides the cache into N chunks (default is 10). If RAM usage gets beyond limits, it starts moving chunks to disk.
    Once a chunk is on disk, it stays there.
    
    TODO: For use cases where the lookup will be used in a mostly sequential fashion, it would be useful to have a version that uses ranges
    instead of a hash function. Then when find_in_cache is called on a disk segment, we could swap a different segment out and bring that 
    segment in. That's a lot more complicated. We'd also want to maintain a last used date for each segment so that if we add rows to the 
    cache, we can choose the best segment to swap to disk.
    
    Also worth considering is that if we bring a segment in from disk, it would best to keep the disk version. At that point any additions 
    to that segment would need to go to both places.

    """
    def __init__(self,
                 lookup_name: str,
                 lookup_keys: list,
                 parent_component: ETLComponent,
                 use_value_cache: bool = True,
                 config: ConfigParser = None,
                 path=None,
                 max_percent_ram_used=None,
                 max_process_ram_usage_mb=None,
                 init_parent: bool = True,
                 **kwargs
                 ):
        if init_parent:
            super().__init__(
                lookup_name=lookup_name,
                lookup_keys=lookup_keys,
                parent_component=parent_component,
                use_value_cache=use_value_cache,
                config=config,
                )
        self._cache = None
        self.rows_cached = 0
        # First try and use passed value
        self.max_percent_ram_used = max_percent_ram_used
        # If not passed in config
        if self.max_percent_ram_used is None:
            if self.config is not None:
                self.max_percent_ram_used = self.config.getfloat('Limits',
                                                                 'disk_swap_at_percent_ram_used',
                                                                 fallback=None)
        # Finally default value
        if self.max_percent_ram_used is None:
            # Needs to be less than the default in bi_etl.components.table.Table.fill_cache
            self.max_percent_ram_used = 70
                        
        self.max_process_ram_usage_mb = max_process_ram_usage_mb
        # If not passed in config
        if self.max_process_ram_usage_mb is None:
            if self.config is not None:
                self.max_process_ram_usage_mb = self.config.getfloat('Limits',
                                                                     'disk_swap_at_process_ram_usage_mb',
                                                                     fallback=None)
        # Finally default value
        if self.max_process_ram_usage_mb is None:
            self.max_process_ram_usage_mb = 2.5 * 1024**3
            
        self._set_path(path)
        
        self.ram_check_row_interval = 5000
        self.last_ram_check_at_row = 0
        self.disk_cache = None
        self.MemoryLookupClass = Lookup
        self.DiskLookupClass = DiskLookup
        if kwargs is None:
            kwargs = dict()
        kwargs['use_value_cache'] = use_value_cache
        self.lookup_class_args = kwargs
         
    def _set_path(self, path):
        if path is not None:
            self.path = path
        else:
            if self.config is not None:
                self.path = self.config.get('Cache', 'path', fallback=DiskLookup.DEFAULT_PATH)
            else:
                self.path = DiskLookup.DEFAULT_PATH

    def _init_mem_cache(self):
        self._cache = self.MemoryLookupClass(lookup_name=self.lookup_name,
                                             lookup_keys=self.lookup_keys,
                                             parent_component=self.parent_component,
                                             config=self.config,
                                             **self.lookup_class_args
                                             )
        self._cache.init_cache()
    
    def init_cache(self):
        if self.cache_enabled is None:
            self.cache_enabled = True
        if self.cache_enabled:
            self._init_mem_cache()        
    
    def get_memory_size(self):
        ram_size = 0
        if self._cache is not None:
            ram_size += self._cache.get_memory_size()
        if self.disk_cache is not None:
            ram_size += self.disk_cache.get_memory_size()
        return ram_size 
        
    def get_disk_size(self):
        disk_size = 0
        if self._cache is not None:
            disk_size += self._cache.get_disk_size()
        if self.disk_cache is not None:
            disk_size += self.disk_cache.get_disk_size()
        return disk_size     
        
    def clear_cache(self):
        if self._cache is not None:
            self._cache.clear_cache()
            del self._cache
        if self.disk_cache is not None:
            self.disk_cache.clear_cache()
            del self.disk_cache 
                    
        self._cache = None
        self.disk_cache = None
    
    def __len__(self):
        total_len = 0
        if self._cache is not None:
            total_len += len(self._cache)
        if self.disk_cache is not None:
            total_len += len(self.disk_cache) 
        return total_len

    def init_disk_cache(self):
        if self.disk_cache is None:
            self.disk_cache = self.DiskLookupClass(lookup_name=self.lookup_name,
                                                   lookup_keys=self.lookup_keys,
                                                   parent_component=self.parent_component,
                                                   config=self.config,
                                                   path=self.path,
                                                   **self.lookup_class_args
                                                   )
            self.disk_cache.init_cache()
            # Do not warn about protected access to _get_estimate_row_size
            # pylint: disable=protected-access
            self._cache.check_estimate_row_size(force_now=True)
            self.disk_cache._row_size = self._cache.estimated_row_size()
            self.disk_cache._done_get_estimate_row_size = self._cache.has_done_get_estimate_row_size()

    def flush_to_disk(self):
        if self._cache is not None and len(self._cache) > 0:
            rows_before = len(self)
            self.init_disk_cache()
            timer = Timer()
            self.log.info('Flushing {rows:,} rows to disk.'.format(rows=len(self._cache)))
            gc.collect()
            before_move_mb = self.our_process.memory_info().rss/(1024**2)
            for row in self._cache:
                self.disk_cache.cache_row(row)
            self._cache.clear_cache()
            del self._cache
            self._cache = None
            self._init_mem_cache()
            if len(self) != rows_before:
                msg = "Row count changed during flush to disk." \
                      " Rows before flush = {}, rows after flush = {}".format(rows_before, len(self))
                raise AssertionError(msg)
            self.log.info('Flushing rows took {} seconds'.format(timer.seconds_elapsed_formatted))
            gc.collect()
            after_move_mb = self.our_process.memory_info().rss/(1024**2)
            self.log.info(
                f'Flushing rows freed {before_move_mb - after_move_mb:,.3f} MB from process '
                f'before {before_move_mb:,.3f} after {after_move_mb:,.3f})'
            )

    def memory_limit_reached(self) -> bool:
        if self.max_percent_ram_used is not None:
            if psutil.virtual_memory().percent > self.max_percent_ram_used:
                self.log.warning(
                    f"{self.lookup_name} system memory limit reached "
                    f"{psutil.virtual_memory().percent} > {self.max_percent_ram_used}% "
                    f"with {self.rows_cached:,} rows of data"
                )
                return True
        process_mb = self.our_process.memory_info().rss / (1024 ** 2)
        if self.max_process_ram_usage_mb is not None:
            if process_mb > self.max_process_ram_usage_mb:
                self.log.warning("{name} process memory limit reached"
                                 " {usg:,} > {usg_limit:,} KB with {rows:,} rows of data"
                                 .format(name=self.lookup_name,
                                         rows=self.rows_cached,
                                         usg=process_mb,
                                         usg_limit=self.max_process_ram_usage_mb,
                                         )
                                 )
                return True
        return False

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
            if self._cache is None:
                self.init_cache()
    
            self.rows_cached += 1
            
            # Note: The memory check needs to be here and not in Table.fill_cache since rows can be added to cache 
            #       during the load and not just by fill_cache.

            # Python memory is hard to free... so read first rows into RAM and then use disk for all rows after

            # Every X rows check memory limits
            if (self.disk_cache is None
                and (self.rows_cached - self.last_ram_check_at_row) >= self.ram_check_row_interval
               ):
                # Double check our cache size. Calls to cache_row might have overwritten existing rows
                self.rows_cached = len(self)
                self.last_ram_check_at_row = self.rows_cached
                if self.memory_limit_reached():
                    self.init_disk_cache()

            # Now cache the row
            if self.disk_cache is None:
                self._cache.cache_row(row, allow_update=allow_update)
            else:
                # We need to make sure each row is in only once place
                lk_tuple = self.get_hashable_combined_key(row)
                if lk_tuple in self._cache:
                    # Move existing key date ranges to disk
                    versions_collection = self.get_versions_collection(row)
                    self._cache.uncache_set(lk_tuple)
                    # Change collection type if needed
                    if not isinstance(versions_collection, DiskLookup.VERSION_COLLECTION_TYPE):
                        versions_collection = DiskLookup.VERSION_COLLECTION_TYPE(versions_collection)
                    disk_lk_tuple = self.disk_cache.get_hashable_combined_key(row)
                    self.disk_cache.cache_set(disk_lk_tuple, versions_collection)

                # Put add new row to disk as well
                self.disk_cache.cache_row(row, allow_update=allow_update)

    def uncache_row(self, row: Lookup.ROW_TYPES):
        if self._cache is not None:
            self._cache.uncache_row(row)
        if self.disk_cache is not None:
            self.disk_cache.uncache_row(row)

    def __iter__(self):
        """
        The rows will come out in any order.  DO NOT MODIFY cache during the loop
        """
        if self._cache is not None:
            for row in self._cache:
                yield row
        if self.disk_cache is not None:
            for row in self.disk_cache:
                yield row

    def get_versions_collection(
            self,
            row: Lookup.ROW_TYPES
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

        try:
            return self._cache.get_versions_collection(row)
        except NoResultFound:
            if self.disk_cache is not None:
                return self.disk_cache.get_versions_collection(row)
            else:
                raise NoResultFound()

    def report_on_value_cache_effectiveness(self, lookup_name: str = None):
        if lookup_name is None:
            lookup_name = self.lookup_name
        if self._cache:
            self._cache.report_on_value_cache_effectiveness(f'{lookup_name} RAM')
        if self.disk_cache:
            self.disk_cache.report_on_value_cache_effectiveness(f'{lookup_name} DISK')


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
    dc = AutoDiskLookup("test", ['col1'], parent_component=parent_component)
    dc.ram_check_row_interval = int(rows_to_use * 0.5)
    dc.max_process_ram_usage_mb = 1
    start_time = Timer()
    for row in parent_component:
        dc.cache_row(row)
    print(start_time.seconds_elapsed_formatted)


if __name__ == "__main__":
    test()
