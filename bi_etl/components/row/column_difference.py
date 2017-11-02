# -*- coding: utf-8 -*-
"""
Created on Jan 20, 2016

@author: woodd
"""


class ColumnDifference(object):
    def __init__(self, 
                 column_name: str=None,
                 old_value=None,
                 new_value=None,
                 ):
        self.column_name = column_name
        self.old_value = old_value
        self.new_value = new_value

    def __str__(self):
        return "{self.column_name} changed from {self.old_value} to {self.new_value}".format(self=self)

    def __repr__(self):
        return str(self)
