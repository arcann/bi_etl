"""
Created on May 15, 2015

@author: woodd
"""
from configparser import ConfigParser

from bi_etl.lookups.disk_lookup import DiskLookup
from bi_etl.lookups.range_lookup import RangeLookup

__all__ = ['DiskRangeLookup']


class DiskRangeLookup(RangeLookup, DiskLookup):
    def __init__(self,
                 lookup_name: str,
                 lookup_keys: list,
                 parent_component: 'bi_etl.components.etlcomponent.ETLComponent',
                 begin_date,
                 end_date,
                 config: ConfigParser = None,
                 path: str = None):
        """
        Optional parameter path controls where the data is persisted
        """
        RangeLookup.__init__(self, 
                             lookup_name=lookup_name,
                             lookup_keys=lookup_keys,
                             parent_component=parent_component,
                             begin_date=begin_date,
                             end_date=end_date,
                             config=config,
                             )
        DiskLookup.__init__(
            self,
            lookup_name=lookup_name,
            lookup_keys=lookup_keys,
            parent_component=parent_component,
            begin_date=begin_date,
            end_date=end_date,
            config=config,
            path=path,
            init_parent=False,  # Don't have it call the parent init because RangeLookup will have done that
        )
        # Add on part of DiskLookup init that isn't covered by RangeLookup.__init__
        # self._set_path(path)

    def init_cache(self):
        DiskLookup.init_cache(self)
