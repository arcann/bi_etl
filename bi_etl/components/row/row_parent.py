'''
Created on May 26, 2015

@author: woodd
'''

class RowParent(object):
    '''
    Pseudo component to act only as a default parent for :class:`~bi_etl.components.row.row_case_insensitive.Row` objects
    '''

    def __init__(self,
                 logical_name = None,
                 primary_key= None,
                 ):        
        self.logical_name = logical_name or id(self)
        self.primary_key = primary_key
        