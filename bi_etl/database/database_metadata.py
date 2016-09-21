# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: woodd
"""
import logging
import sqlalchemy


#pylint: disable=abstract-method
class DatabaseMetadata(sqlalchemy.schema.MetaData):
    """
    A light wrapper over sqlalchemy.schema.MetaData
    """

    def _set_parent(self, parent):
        pass

    def execute(self, sql):        
        with self.bind.connect() as connection:
            return connection.execute(sql)
    
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
        ##TODO: Capture statistics (basic Timer)
        ##TODO: support other database
        log = logging.getLogger(__name__)
        sql_command = 'BEGIN {}; END;'.format(procedure_name)         
        log.debug("SQL = {}".format(sql_command))
        self.execute(sql_command)
