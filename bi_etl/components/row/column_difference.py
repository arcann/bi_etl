# -*- coding: utf-8 -*-
"""
Created on Jan 20, 2016

@author: Derek Wood
"""
import typing


class ColumnDifference(object):
    def __init__(self, 
                 column_name: typing.Optional[str] = None,
                 old_value=None,
                 new_value=None,
                 ):
        self.column_name = column_name
        self.old_value = old_value
        self.new_value = new_value

    def __str__(self):
        return f"{self.column_name} changed from {self.old_value} to {self.new_value}"

    def __repr__(self):
        return str(self)
