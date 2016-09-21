# -*- coding: utf-8 -*-
"""
Created on Jan 5, 2016

@author: woodd
"""

from bi_etl.lookups.autodisk_lookup import AutoDiskLookup
from bi_etl.lookups.range_lookup import RangeLookup
from bi_etl.lookups.disk_range_lookup import DiskRangeLookup

class AutoDiskRangeLookup(AutoDiskLookup, RangeLookup):
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
        AutoDiskLookup.__init__(self, 
                             lookup_name= lookup_name, 
                             lookup_keys= lookup_keys, 
                             parent_component= parent_component,
                             config= config,
                             path= path,
                             begin_date= begin_date,
                             end_date= end_date, 
                             )
        self.MemoryLookupClass = RangeLookup
        self.DiskLookupClass = DiskRangeLookup
        
    def cache_row(self, row, allow_update = True):
        AutoDiskLookup.cache_row(self, row, allow_update=allow_update)
        
    def find_in_cache(self, row, effective_date= None):
        return AutoDiskLookup.find_in_cache(self, row=row, effective_date=effective_date)