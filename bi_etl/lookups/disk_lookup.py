"""
Created on May 15, 2015

@author: woodd
"""
import shelve
import semidbm
import math 
import tempfile
import string
import os
import dbm
import sys

from bi_etl.lookups.lookup import Lookup
from bi_etl.memory_size import get_dir_size
from bi_etl.memory_size import get_size_gc
import pickle
        
__all__ = ['DiskLookup']


class DiskLookup(Lookup):
    DEFAULT_PATH = None
    
    def __init__(self, lookup_name, lookup_keys, parent_component, config=None, path= None, **kwargs):
        """
        Optional parameter path where the lookup files should be persisted to disk
        """        
        super(DiskLookup, self).__init__(lookup_name= lookup_name, 
                                         lookup_keys= lookup_keys, 
                                         parent_component= parent_component, 
                                         config= config,
                                         **kwargs
                                         )
        self._set_path(path)
        self.dbm = None
        self.cache_dir_mgr = None
        self.cache_file_path = None
        
    def _set_path(self, path):
        if path is not None:
            self.path = path
        else:
            if self.config is not None:
                self.path = self.config.get_or_default('Cache', 'path', DiskLookup.DEFAULT_PATH)
            else:
                self.path = DiskLookup.DEFAULT_PATH
            
    def init_cache(self):
        if self.cache_enabled is None:
            self.cache_enabled = True
        if self.cache_enabled:
            file_prefix = ''.join([c for c in self.lookup_name if c in string.ascii_letters])
            self.cache_dir_mgr = tempfile.TemporaryDirectory(dir=self.path, prefix=file_prefix)
            self.cache_file_path = self.cache_dir_mgr.name
            self.log.info("Creating cache in {}".format(self.cache_file_path))
            if sys.platform.startswith('win'):
                self.dbm = semidbm.open(self.cache_file_path, 'n')            
            else:
                file = os.path.join(self.cache_file_path,'data')
                self.dbm = dbm.open(file, 'n')
            self.cache = shelve.BsdDbShelf(self.dbm, 
                                           protocol=pickle.HIGHEST_PROTOCOL,
                                           writeback=False,)
        
    def __len__(self):
        if self.cache is not None:
            return len(self.dbm.keys())
        else:
            return 0
        
    def _get_first_row_size(self, row):
        if self.dbm:
            # Slow but shouldn't be too bad twice
            self._row_size = get_size_gc(self.dbm)
        
    def get_estimate_row_size(self, force_now=False):
        if force_now or not self._done_get_estimate_row_size:
            row_cnt = min(len(self),1000)
            total_row_sizes = 0
            row_num = 0
            for row in self:
                total_row_sizes += get_size_gc(self.get_hashable_combined_key(row))
                row_num += 1
                if row_num >= row_cnt:
                    break      
            self._row_size = math.ceil(total_row_sizes / row_cnt)
            msg = '{lookup_name} row key size (in memory) now estimated at {size:,} bytes per row'
            msg = msg.format(lookup_name= self.lookup_name,
                             size= self._row_size)
            self.log.debug(msg)
            self._done_get_estimate_row_size = True   
        
    def get_disk_size(self):
        if self.cache_file_path:
            return get_dir_size(self.cache_file_path)
        else:
            return 0
        
    def get_hashable_combined_key(self, row):
        # shelve expects str keys
        result = str(self.get_list_of_lookup_column_values(row))
        return result

    def __del__(self):
        self.clear_cache()            

    def clear_cache(self):
        if self.cache is not None:
            self.cache.close()
            self.cache_dir_mgr.cleanup()
        self.cache = None
