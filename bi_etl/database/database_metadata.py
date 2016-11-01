# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: woodd
"""
import logging
import sqlalchemy


#pylint: disable=abstract-method
from sqlalchemy.exc import OperationalError


class DatabaseMetadata(sqlalchemy.schema.MetaData):
    """
    A light wrapper over sqlalchemy.schema.MetaData
    """

    def _set_parent(self, parent):
        pass

    def execute(self, sql):        
        with self.bind.connect() as connection:
            return connection.execute(sql)
    
    def execute_procedure(self, procedure_name, *args):
        """
        Execute a stored procedure 
        
        Parameters
        ----------
        procedure_name: str
            The procedure to run.
        args:
            The arguments to pass
            
        Raises
        ------
        sqlalchemy.exc.DBAPIError:
            API error            
        sqlalchemy.exc.DatabaseError:
            Maybe?            
        """
        log = logging.getLogger(__name__)
        log.debug("Calling procedure {} {}".format(procedure_name, args))
        dpapi_connection = self.bind.raw_connection()
        try:
            cursor = dpapi_connection.cursor()
            cursor.callproc(procedure_name, args)
            results = list(cursor.fetchall())
            cursor.close()
            dpapi_connection.commit()
        finally:
            dpapi_connection.close()
        return results

    def execute_direct(self, sql, return_results=False):
        log = logging.getLogger(__name__)
        log.debug(sql)
        dpapi_connection = self.bind.raw_connection()
        try:
            cursor = dpapi_connection.cursor()
            cursor.execute(sql)
            results = None
            if return_results:
                results = list(cursor.fetchall())
            cursor.close()
            dpapi_connection.commit()
        finally:
            dpapi_connection.close()
        return results
