# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: woodd
"""
import logging
import sqlalchemy

from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.sql.schema import DEFAULT_NAMING_CONVENTION


class DatabaseMetadata(sqlalchemy.schema.MetaData):
    """
    A light wrapper over sqlalchemy.schema.MetaData
    """

    def __init__(self, bind=None, reflect=False, schema=None,
                 quote_schema=None,
                 naming_convention=DEFAULT_NAMING_CONVENTION,
                 info=None,
                 database_name=None,
                 ):
        super().__init__(
            bind=bind,
            reflect=reflect,
            schema=schema,
            quote_schema=quote_schema,
            naming_convention=naming_convention,
            info=info,
        )
        self._table_inventory = None
        self.database_name = database_name

    def _set_parent(self, parent):
        pass

    def execute(self, sql):        
        with self.bind.connect() as connection:
            return connection.execute(sql)
    
    def execute_procedure(self, procedure_name, *args, return_results=False):
        """
        Execute a stored procedure 
        
        Parameters
        ----------
        procedure_name: str
            The procedure to run.
        args:
            The arguments to pass

        return_results:
            Needs to be a keyword param. Should we try and get result rows
            from the procedure.
            
        Raises
        ------
        sqlalchemy.exc.DBAPIError:
            API error            
        sqlalchemy.exc.DatabaseError:
            Proxy for database error
        """
        log = logging.getLogger(__name__)
        log.debug("Calling procedure {} {}".format(procedure_name, args))
        dpapi_connection = self.bind.raw_connection()
        try:
            cursor = dpapi_connection.cursor()
            cursor.callproc(procedure_name, args)
            results = None
            if return_results:
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

    def table_inventory(self, force_reload=False):
        if self._table_inventory is None or force_reload:
            inspector = Inspector.from_engine(self.bind)
            self._table_inventory = inspector.get_table_names()
        return self._table_inventory
