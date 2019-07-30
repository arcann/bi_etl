"""
Created on Apr 3, 2015

@author: Derek Wood
"""

class NoResultFound(Exception):
    pass

class MultipleResultsFound(Exception):
    pass

class BeforeAllExisting(Exception):    
    def __init__(self, first_existing_row, effective_date):
        self.first_existing_row = first_existing_row
        self.effective_date = effective_date
    
    def __str__(self):
        return 'First row = {} \n not yet started at {}'.format(self.first_existing_row, self.effective_date)

class AfterExisting(Exception):    
    def __init__(self, prior_row, effective_date):
        self.prior_row = prior_row
        self.effective_date = effective_date
        
    def __str__(self):
        return 'Last row = {} \n ends before {}'.format(self.prior_row, self.effective_date)

class ColumnMappingError(Exception):
    def __init__(self, msg):
        self.msg = str(msg)
        
    def __str__(self):
        return self.msg