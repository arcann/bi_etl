"""
Created on May 15, 2015

@author: woodd
"""
import dbm
import math
import os
import pickle
import shelve
import string
import sys
import tempfile
import weakref

import semidbm
from bi_etl.lookups.lookup import Lookup
from bi_etl.memory_size import get_dir_size
from bi_etl.memory_size import get_size_gc

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
        self.use_value_cache = False
        self._finalizer = None
        
    def _set_path(self, path):
        if path is not None:
            self.path = path
        else:
            if self.config is not None:
                self.path = self.config.get('Cache', 'path', fallback=DiskLookup.DEFAULT_PATH)
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
                file = os.path.join(self.cache_file_path, 'data')
                self.dbm = dbm.open(file, 'n')
            self.cache = shelve.BsdDbShelf(self.dbm, 
                                           protocol=pickle.HIGHEST_PROTOCOL,
                                           writeback=False,)
            self._finalizer = weakref.finalize(self, self._cleanup)

    def __len__(self):
        if self.cache is not None:
            return len(self.dbm.keys())
        else:
            return 0
        
    def _get_first_row_size(self, row):
        if self.dbm:
            # Slow but shouldn't be too bad twice
            self._row_size = get_size_gc(self.dbm)
        
    def _check_estimate_row_size(self, force_now=False):
        if force_now or not self._done_get_estimate_row_size:
            row_cnt = min(len(self), 1000)
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

    def _cleanup(self):
        print("Cleanup")
        self.clear_cache()            

    def clear_cache(self):
        if self.cache is not None:
            self.cache.close()
            self.cache_dir_mgr.cleanup()
        self.cache = None


def test():
    from _datetime import datetime
    from bi_etl.timer import Timer
    from bi_etl.tests.dummy_etl_component import DummyETLComponent
    from bi_etl.components.row.row_iteration_header import RowIterationHeader
    from bi_etl.components.row.row import Row

    iteration_header = RowIterationHeader()
    data = list()
    for i in range(10000):
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
    dc = DiskLookup("test", ['col1'], parent_component=parent_component)
    start_time = Timer()
    for row in parent_component:
        dc.cache_row(row)
    print(start_time.seconds_elapsed_formatted)


if __name__ == "__main__":
    test()
