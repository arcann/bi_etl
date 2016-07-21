# -*- coding: utf-8 -*-
'''
Created on Jan 5, 2016

@author: woodd
'''

from bi_etl.exceptions import NoResultFound
from bi_etl.lookups.lookup import Lookup
from bi_etl.lookups.disk_lookup import DiskLookup
from bi_etl.timer import Timer
import gc
import psutil

__all__ = ['Lookup']

class AutoDiskLookup(Lookup):
    '''
    Automatic memory / disk lookup cache.
    
    This version divides the cache into N chunks (default is 10). If RAM usage gets beyond limits, it starts moving chunks to disk.
    Once a chunk is on disk, it stays there.
    
    TODO: For use cases where the lookup will be used in a mostly sequential fashion, it would be useful to have a version that uses ranges
    instead of a hash function. Then when find_in_cache is called on a disk segment, we could swap a different segment out and bring that 
    segment in. That's a lot more complicated. We'd also want to maintain a last used date for each segment so that if we add rows to the 
    cache, we can choose the best segment to swap to disk.
    
    Also worth considering is that if we bring a segment in from disk, it would best to keep the disk version. At that point any additions 
    to that segment would need to go to both places.

    '''
    def __init__(self, 
                 lookup_name, 
                 lookup_keys, 
                 parent_component, 
                 config=None,
                 path=None,
                 max_percent_ram_used = None,
                 max_process_ram_usage_mb = None,
                 **kwargs
                 ):
        Lookup.__init__(self,
                        lookup_name= lookup_name, 
                        lookup_keys= lookup_keys, 
                        parent_component= parent_component, 
                        config= config
                        )
        self.cache = None
        self.rows_cached = 0
        ## First try and use passed value
        self.max_percent_ram_used = max_percent_ram_used
        ## If not passed in config
        if self.max_percent_ram_used is None:
            if self.config is not None:
                self.max_percent_ram_used = self.config.getfloat_or_default('Limits','disk_swap_at_percent_ram_used',default= None)
        ## Finally default value
        if self.max_percent_ram_used is None:
            self.max_percent_ram_used = 70 ## Needs to be less than the default in bi_etl.components.table.Table.fill_cache
                        
        self.max_process_ram_usage_mb = max_process_ram_usage_mb
        ## If not passed in config
        if self.max_process_ram_usage_mb is None:
            if self.config is not None:
                self.max_process_ram_usage_mb = self.config.getfloat_or_default('Limits','disk_swap_at_process_ram_usage_mb', default= None)
        ## Finally default value
        if self.max_process_ram_usage_mb is None:
            self.max_process_ram_usage_mb = 2.5 * 1024**3
            
        self._set_path(path)
        
        self.ram_check_row_interval = 1000
        self.last_ram_check_at_row = 0
        self.disk_cache = None   
        self.MemoryLookupClass = Lookup
        self.DiskLookupClass = DiskLookup
        self.lookup_class_args = kwargs
         
    def _set_path(self, path):
        if path is not None:
            self.path = path
        else:
            if self.config is not None:
                self.path = self.config.get_or_default('Cache','path',DiskLookup.DEFAULT_PATH)
            else:
                self.path = DiskLookup.DEFAULT_PATH

    #pylint: disable=unused-argument, no-self-use  
    def get_unique_stats_entry(self, stats_id, parent_stats=None, print_start_stop_times= None):
        ## Since we aren't capturing any useful stats in the sub caches yet, skip creating stats entries
        #=======================================================================
        # total_stats_id = '{cls} {name} {sub}'.format(cls= self.__class__.__name__, 
        #                                        name=self.lookup_name,
        #                                        sub=stats_id
        #                                        )
        # return self.parent_component.get_unique_stats_entry(stats_id=total_stats_id, 
        #                                                     parent_stats=parent_stats, 
        #                                                     print_start_stop_times=print_start_stop_times
        #                                                     )
        #=======================================================================        
        return None

    def _init_mem_cache(self):
        self.cache = self.MemoryLookupClass(lookup_name= self.lookup_name, 
                                            lookup_keys= self.lookup_keys, 
                                            parent_component= self, 
                                            config= self.config,
                                            **self.lookup_class_args
                                            )
    
    def init_cache(self):
        if self.cache_enabled is None:
            self.cache_enabled = True
        if self.cache_enabled:
            self._init_mem_cache()        
        
    
    def get_memory_size(self):
        ram_size = 0
        if self.cache is not None:
            ram_size += self.cache.get_memory_size()
        if self.disk_cache is not None:
            ram_size += self.disk_cache.get_memory_size()
        return ram_size 
        
    def get_disk_size(self):
        disk_size = 0
        if self.cache is not None:
            disk_size +=  self.cache.get_disk_size()
        if self.disk_cache is not None:
            disk_size += self.disk_cache.get_disk_size()
        return disk_size     
        
    def clear_cache(self):
        if self.cache is not None:
            self.cache.clear_cache()
            del self.cache
        if self.disk_cache is not None:
            self.disk_cache.clear_cache()
            del self.disk_cache 
                    
        self.cache = None
        self.disk_cache = None
    
    def __len__(self):
        total_len = 0
        if self.cache is not None:
            total_len += len(self.cache)
        if self.disk_cache is not None:
            total_len += len(self.disk_cache) 
        return total_len
        
    def flush_to_disk(self):
        if self.cache is not None and len(self.cache) > 0:
            if self.disk_cache is None:
                self.disk_cache = self.DiskLookupClass(lookup_name= self.lookup_name, 
                                                       lookup_keys= self.lookup_keys, 
                                                       parent_component= self, 
                                                       config= self.config,
                                                       path= self.path,
                                                       **self.lookup_class_args
                                                       )            
                ## Do not warn about protected access to _get_estimate_row_size
                #pylint: disable=protected-access
                self.cache._get_estimate_row_size(force_now=True)
                self.disk_cache._row_size = self.cache._row_size
                self.disk_cache._done_get_estimate_row_size = self.cache._done_get_estimate_row_size
            timer = Timer()
            self.log.info('Flushing {rows:,} rows to disk.'.format(rows= len(self.cache)))
            gc.collect()
            before_move_mb = self.our_process.memory_info().rss/(1024**2)
            for row in self.cache:
                self.disk_cache.cache_row(row)
            self.cache.clear_cache()
            del self.cache
            self.cache = None         
            self._init_mem_cache()       
            self.log.info('Flushing rows took {} seconds'.format(timer.seconds_elapsed_formatted))
            gc.collect()
            after_move_mb = self.our_process.memory_info().rss/(1024**2)
            self.log.info('Flushing rows freed {:,.3f} MB from process (before {:,.3f} after {:,.3f})'.format(before_move_mb - after_move_mb, before_move_mb, after_move_mb))
            
    def check_memory(self):
        ## Only check memory if we have rows in memory
        if self.cache is not None and len(self.cache) > 0:
            ## Every X rows check memory limits
            if (self.rows_cached - self.last_ram_check_at_row) >= self.ram_check_row_interval:                                
                ## Double check our cache size. Calls to cache_row might have overwritten existing rows                
                self.rows_cached = len(self)
                self.last_ram_check_at_row = self.rows_cached
                
                limit_reached = False
                
                if self.max_percent_ram_used is not None:
                    if psutil.virtual_memory().percent > self.max_percent_ram_used:
                        limit_reached = True                
                        self.log.warning("{name}.fill_cache moving a segment to disk at due to system memory limit {pct} > {pct_limit}% with {rows:,} rows of data".format(
                                                                                                                                              name = self.lookup_name,
                                                                                                                                              rows = self.rows_cached,
                                                                                                                                              pct = psutil.virtual_memory().percent,
                                                                                                                                              pct_limit = self.max_percent_ram_used,
                                                                                                                                              )
                                  )
                process_mb = self.our_process.memory_info().rss/(1024**2)
                if self.max_process_ram_usage_mb is not None:
                    if process_mb > self.max_process_ram_usage_mb:
                        ## Set flag to clean out the cache built so far below
                        limit_reached = True
                        self.log.warning("{name}.fill_cache moving a segment to disk at due to process memory limit {usg:,} > {usg_limit:,} KB with {rows:,} rows of data".format(
                                                                                                                                              name = self.lookup_name,
                                                                                                                                              rows = self.rows_cached,
                                                                                                                                              usg = process_mb,
                                                                                                                                              usg_limit = self.max_process_ram_usage_mb,
                                                                                                                                              )
                                  )
                if limit_reached:
                    self.flush_to_disk()    
        
        

    def cache_row(self, row, allow_update= True):
        if self.cache_enabled:        
            if self.cache is None:
                self.init_cache()
    
            self.rows_cached += 1
            
            ## Note: The memory check needs to be here and not in Table.fill_cache since rows can be added to cache 
            ##       during the load and not just by fill_cache.
            self.check_memory()
            
            ## We need to make sure each row is in only once place
            ## Since disk_cache keeps a memory index, has_row should be fast
            if self.disk_cache is not None and self.disk_cache.has_row(row):
                self.disk_cache.cache_row(row, allow_update= allow_update)
            else:
                self.cache.cache_row(row, allow_update= allow_update)
        
    def uncache_row(self, row):
        if self.cache is not None:
            self.cache.uncache_row(row)
        if self.disk_cache is not None:
            self.disk_cache.uncache_row(row)
            

    def __iter__(self):
        '''
        The rows will come out in any order.
        '''
        if self.cache is not None:

            ##TODO: Turn off the flush to disk during this operation so that we don't change the dict
            ## Also needs to work with uncache_row 
            
            for row in self.cache:
                yield row
        if self.disk_cache is not None:
            for row in self.disk_cache:
                yield row
  
    def find_in_cache(self, row, **kwargs):
        """Find a matching row in the lookup based on the lookup index (keys)"""
        if not self.cache_enabled:
            raise ValueError("Lookup {} cache not enabled".format(self.lookup_name))
        if self.cache is None:
            raise ValueError("Lookup {} not initialized".format(self.lookup_name))
        else:
            try:                
                return self.cache.find_in_cache(row, **kwargs)            
            except NoResultFound:
                if self.disk_cache is not None:
                    return self.disk_cache.find_in_cache(row, **kwargs)
                else:
                    raise NoResultFound()
    
    