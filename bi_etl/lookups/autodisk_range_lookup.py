# -*- coding: utf-8 -*-
"""
Created on Jan 5, 2016

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import typing

from bi_etl.components.row.row import Row
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.lookups.autodisk_lookup import AutoDiskLookup
from bi_etl.lookups.disk_range_lookup import DiskRangeLookup
from bi_etl.lookups.range_lookup import RangeLookup

if typing.TYPE_CHECKING:
    from bi_etl.components.etlcomponent import ETLComponent


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

    def __init__(self,
                 lookup_name: str,
                 lookup_keys: list,
                 parent_component: ETLComponent,
                 begin_date,
                 end_date,
                 config: BI_ETL_Config_Base = None,
                 use_value_cache: bool = True,
                 path=None,
                 ):
        """
        Optional parameter path controls where the data is persisted
        """
        RangeLookup.__init__(self,
                             lookup_name=lookup_name,
                             lookup_keys=lookup_keys,
                             use_value_cache=use_value_cache,
                             parent_component=parent_component,
                             begin_date=begin_date,
                             end_date=end_date,
                             config=config,
                             )
        AutoDiskLookup.__init__(self,
                                lookup_name=lookup_name,
                                lookup_keys=lookup_keys,
                                parent_component=parent_component,
                                config=config,
                                path=path,
                                begin_date=begin_date,
                                end_date=end_date,
                                use_value_cache=use_value_cache,
                                init_parent=False,  # Don't have it call the parent init because RangeLookup will have done that
                                )
        self.MemoryLookupClass = RangeLookup
        self.DiskLookupClass = DiskRangeLookup

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
        AutoDiskLookup.cache_row(self, row, allow_update=allow_update)

    def find_in_cache(self, row, **kwargs):
        return RangeLookup.find_in_cache(self, row=row, **kwargs)
