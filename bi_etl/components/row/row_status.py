# -*- coding: utf-8 -*-
"""
Created on Jan 20, 2016

@author: Derek Wood
"""
from enum import IntEnum, unique


@unique
class RowStatus(IntEnum):
    """
    Row status values
    """
    existing = 1
    insert = 2
    update_whole = 3
    update_partial = 4
    deleted = 5
    unknown = 99
