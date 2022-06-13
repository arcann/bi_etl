"""
Created on May 15, 2015

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import typing

from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.lookups.disk_lookup import DiskLookup
from bi_etl.lookups.range_lookup import RangeLookup

if typing.TYPE_CHECKING:
    from bi_etl.components.etlcomponent import ETLComponent

__all__ = ['DiskRangeLookup']


class DiskRangeLookup(RangeLookup, DiskLookup):
    def __init__(self,
                 lookup_name: str,
                 lookup_keys: list,
                 parent_component: ETLComponent,
                 begin_date,
                 end_date,
                 config: BI_ETL_Config_Base = None,
                 use_value_cache: bool = True,
                 path: str = None):
        """
        Optional parameter path controls where the data is persisted
        """
        RangeLookup.__init__(self, 
                             lookup_name=lookup_name,
                             lookup_keys=lookup_keys,
                             parent_component=parent_component,
                             use_value_cache=use_value_cache,
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
