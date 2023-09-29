# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: Derek Wood
"""

import logging


class MockDatabaseMetadata(object):
    """
    Mock testing of sqlalchemy metadata
    """
    def __init__(self):
        self.execute_calls = list()
    
    def execute(self, sql):
        self.execute_calls.append(sql)    
    
    def execute_procedure(self, procedure_name):
        """
        Execute a stored procedure 
        
        Parameters
        ----------
        procedure_name: str
            The procedure to run.
            
        Raises
        ------
        sqlalchemy.exc.DBAPIError:
            API error            
        sqlalchemy.exc.DatabaseError:
            Maybe?            
        """
        # TODO: Capture statistics (basic Timer)
        # TODO: support other database
        log = logging.getLogger(__name__)
        sql_command = f'BEGIN {procedure_name}; END;'
        log.debug(f"SQL = {sql_command}")
        self.execute(sql_command)
