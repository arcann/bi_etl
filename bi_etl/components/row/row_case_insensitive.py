# -*- coding: utf-8 -*-
"""
Created on Sep 17, 2014

@author: Derek Wood
"""
from typing import Union, MutableMapping, NamedTuple

from pydicti import dicti

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header_case_insensitive import RowIterationHeaderCaseInsensitive
from bi_etl.components.row.row_status import RowStatus
from bi_etl.utility.case_insensitive_set import CaseInsensitiveFrozenSet


class RowCaseInsensitive(Row):
    """
    Replacement for core SQL Alchemy, CSV or other dictionary based rows.
    Handles converting column names (keys) between upper and lower case.
    Handles column names (keys) that are SQL Alchemy column objects.
    Keeps order of the columns (see columns_in_order) 
    """
    RowIterationHeader_Class = RowIterationHeaderCaseInsensitive
    # For performance with the Column to str conversion we keep a cache of converted values
    # The dict lookup tests as twice as fast as just the lower function
    __name_map_db = dict()

    def __init__(self,
                 iteration_header: RowIterationHeaderCaseInsensitive,
                 data: Union[MutableMapping, list, NamedTuple, None] = None,
                 status: RowStatus | None = None,
                 allocate_space=True):
        assert isinstance(iteration_header, RowIterationHeaderCaseInsensitive)
        super().__init__(data=data,
                         iteration_header=iteration_header,
                         status=status,
                         allocate_space=allocate_space
                         )

    @property
    def as_dict(self) -> dict:
        # noinspection PyTypeChecker
        return dicti(zip(self.columns_in_order, self._data_values))

    @property
    def column_set(self) -> frozenset:
        return CaseInsensitiveFrozenSet(self.columns_in_order)
