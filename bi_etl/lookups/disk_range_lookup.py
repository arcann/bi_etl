"""
Created on May 15, 2015

@author: woodd
"""
from bi_etl.lookups.range_lookup import RangeLookup
from bi_etl.lookups.disk_lookup import DiskLookup

__all__ = ['DiskRangeLookup']

class DiskRangeLookup(RangeLookup, DiskLookup):
    def __init__(self, lookup_name, lookup_keys, parent_component, begin_date, end_date, config=None, path=None):
        """
        Optional parameter path controls where the data is persisted
        """
        RangeLookup.__init__(self, 
                             lookup_name= lookup_name, 
                             lookup_keys= lookup_keys, 
                             parent_component= parent_component,
                             begin_date= begin_date, 
                             end_date= end_date, 
                             config= config, 
                             )
        ## Add on part of DiskLookup init that isn't covered by RangeLookup.__init__      
        self._set_path(path)

    def init_cache(self):
        DiskLookup.init_cache(self)