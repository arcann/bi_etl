# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: Derek Wood
"""
import logging
import textwrap

import sqlalchemy

from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import DEFAULT_NAMING_CONVENTION

from bi_etl.utility.case_insentive_set import CaseInsentiveSet


class DatabaseMetadata(sqlalchemy.schema.MetaData):
    """
    A light wrapper over sqlalchemy.schema.MetaData
    """

    def __init__(self, bind=None, reflect=False, schema=None,
                 quote_schema=None,
                 naming_convention=DEFAULT_NAMING_CONVENTION,
                 info=None,
                 database_name=None,
                 uses_bytes_length_limits=None,
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
        self._uses_bytes_length_limits = uses_bytes_length_limits
        self._connection = None
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))

    def _set_parent(self, parent):
        pass

    def connect(self):
        if self.dialect_name == 'sqlite':
            if self._connection is None or self._connection.closed:
                self._connection = self.bind.connect()
            return self._connection
        else:
            return self.bind.connect()

    def session(self, autocommit: bool = False):
        return Session(bind=self.bind, autocommit=autocommit)

    def begin(self):
        return self.connect().begin()

    def execute(self, sql, transaction: bool = True):
        if transaction:
            with self.connect() as connection:
                with connection.begin() as transaction:
                    result = connection.execute(sql)
                    if result.returns_rows:
                        result = list(result)
                    transaction.commit()
                    return result
        else:
            with self.connect() as connection:
                result = connection.execute(sql)
                if result.returns_rows:
                    return list(result)
                else:
                    return result
    
    def execute_procedure(self, procedure_name, *args, return_results=False, dpapi_connection=None):
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

        dpapi_connection:
            A raw dpapi connection to use. Optional.
            
        Raises
        ------
        sqlalchemy.exc.DBAPIError:
            API error            
        sqlalchemy.exc.DatabaseError:
            Proxy for database error
        """
        log = logging.getLogger(__name__)
        log.debug("Calling procedure {} {}".format(procedure_name, args))

        if dpapi_connection is None:
            dpapi_connection = self.bind.raw_connection()
            close_connection = True
        else:
            close_connection = False
        results = None
        try:
            cursor = dpapi_connection.cursor()
            if hasattr(cursor, 'callproc'):
                cursor.callproc(procedure_name, args)
                if return_results:
                    results = list(cursor.fetchall())
                cursor.close()
            else:
                # Stopped using CALL because of issues like those mentioned on https://stackoverflow.com/a/34179375
                # if False: # 'pyodbc' in self.bind.dialect.dialect_description == 'mssql+pyodbc':
                #     if len(args) > 0:
                #         sql = f"{{CALL {procedure_name}({','.join([qmark for qmark in ['?'] * len(args)])}) }}"
                #     else:
                #         sql = f"{{CALL {procedure_name}}}"
                # else:
                # sql = f"EXEC {procedure_name} {','.join([qmark for qmark in ['?'] * len(args)])}"
                sql = f"EXEC {procedure_name} "
                args2 = []
                delim = ''
                for arg in args:
                    if isinstance(arg, str):
                        arg = arg.strip()
                    # Handle keyword named parameters
                    if arg[0] == '@':
                        param, value = arg.split('=')
                        param = param.strip()
                        param = f'{param}=?'
                        value = value.strip()
                        # Likely the opening quote of the value has not been removed yet
                        if value[0] == "'":
                            value = value[1:]
                    else:
                        param = '?'
                        value = arg
                    sql += delim + param
                    delim = ', '
                    args2.append(value)

                cursor.execute(sql, args2)

                if return_results:
                    results = list(cursor.fetchall())
                cursor.close()
            dpapi_connection.commit()
        finally:
            if close_connection:
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

    def table_inventory(self, schema=None, force_reload=False):
        if self._table_inventory is None:
            self._table_inventory = dict()
        if schema not in self._table_inventory or force_reload:
            inspector = Inspector.from_engine(self.bind)
            self._table_inventory[schema] = CaseInsentiveSet(inspector.get_table_names(schema=schema))
        return self._table_inventory[schema]

    @staticmethod
    def qualified_name(schema, table):
        if schema is not None:
            return schema + '.' + table
        else:
            return table

    def rename_table(self, schema, table_name, new_table_name):
        if self.dialect_name == 'mssql':
            self.execute_procedure(
                'sp_rename',
                self.qualified_name(schema, table_name),
                new_table_name
            )
        else:
            sql = f"alter table {self.qualified_name(schema, table_name)} rename to {new_table_name}"
            self.log.debug(sql)
            self.execute(sql)

    def drop_table_if_exists(self, table_name, schema=None):
        if schema is None:
            if '.' in table_name:
                schema, table_name = table_name.split('.')
        # SQL Server 2016+ can use IF EXISTS but rather than checking version use compatible mode
        if self.dialect_name == 'mssql':
            if table_name[0] == '#':
                # Temp table
                sql = textwrap.dedent(f"""\
                    IF OBJECT_ID('tempdb.dbo.{table_name}', 'U') IS NOT NULL 
                    DROP TABLE {self.qualified_name(schema, table_name)}; 
                """)
            else:
                sql = textwrap.dedent(f"""\
                    IF OBJECT_ID('{self.qualified_name(schema, table_name)}', 'U') IS NOT NULL 
                    DROP TABLE {self.qualified_name(schema, table_name)}; 
                """)
        else:
            sql = f"drop table IF EXISTS {self.qualified_name(schema, table_name)}"
        self.log.debug(sql)
        self.execute(sql)


    @property
    def dialect(self):
        return self.bind.dialect

    @property
    def dialect_name(self):
        return self.bind.dialect.name

    @property
    def uses_bytes_length_limits(self):
        if self._uses_bytes_length_limits is None:
            # Note: Oracle can use either VARCHAR2(10 CHAR) or VARCHAR2(10 BYTE)
            #       However, if not specified (and NLS_LENGTH_SEMANTICS is default), it's char so we assume that.
            if self.dialect_name in {
                'redshift', 'oracle'
            }:
                self._uses_bytes_length_limits = True
            else:
                self._uses_bytes_length_limits = False
        return self._uses_bytes_length_limits
