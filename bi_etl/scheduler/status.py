# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: Derek Wood
"""
from enum import IntEnum, unique


@unique
class Status(IntEnum):
    new = 0
    running = 10
    succeeded = 100
    failed = -99
