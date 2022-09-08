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
    A light wrapper over :class:`sqlalchemy.schema.MetaData`
    """

    def __init__(self,
                 bind=None,
                 reflect=False,
                 schema=None,
                 quote_schema=None,
                 naming_convention=DEFAULT_NAMING_CONVENTION,
                 info=None,
                 database_name=None,
                 uses_bytes_length_limits=None,
                 ):
        super().__init__(
            bind=bind,
            schema=schema,
            quote_schema=quote_schema,
            naming_convention=naming_convention,
            info=info,
        )
        # Save parameters not saved by the base class for use in __reduce_ex__

        self._save_reflect = reflect
        self._save_quote_schema = quote_schema

        self._table_inventory = None
        self.database_name = database_name
        self._uses_bytes_length_limits = uses_bytes_length_limits

        self._connection_pool = dict()
        self._transactions = dict()
        self.default_connection_name = 'default'

        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def __reduce_ex__(self, protocol):
        return (
            # A callable object that will be called to create the initial version of the object.
            self.__class__,

            # A tuple of arguments for the callable object. An empty tuple must be given if the callable does not accept any argument
            (self.bind.url, self._save_reflect, self.schema, self._save_quote_schema, self.naming_convention, self.info, self.database_name, self._uses_bytes_length_limits),

            # Optionally, the object’s state, which will be passed to the object’s __setstate__() method as previously described.
            # If the object has no such method then, the value must be a dictionary and it will be added to the object’s __dict__ attribute.
            None,

            # Optionally, an iterator (and not a sequence) yielding successive items.
            # These items will be appended to the object either using obj.append(item) or, in batch, using obj.extend(list_of_items).

            # Optionally, an iterator (not a sequence) yielding successive key-value pairs.
            # These items will be stored to the object using obj[key] = value

            # PROTOCOL 5+ only
            # Optionally, a callable with a (obj, state) signature.
            # This callable allows the user to programmatically control the state-updating behavior of a specific object,
            # instead of using obj’s static __setstate__() method.
            # If not None, this callable will have priority over obj’s __setstate__().
        )

    def _set_parent(self, parent):
        pass

    def resolve_connection_name(self, connection_name: str = None) -> str:
        if connection_name is None:
            connection_name = self.default_connection_name
        # When using sqlite don't make new connections, reuse the existing one
        if self.dialect_name == 'sqlite':
            connection_name = 'sqlite'
        return connection_name

    def _connect(self) -> sqlalchemy.engine.base.Connection:
        return self.bind.connect()

    def connection(
            self,
            connection_name: str = None,
            open_if_not_exist: bool = True,
            open_if_closed: bool = True,
    ) -> sqlalchemy.engine.base.Connection:
        connection_name = self.resolve_connection_name(connection_name)
        if connection_name in self._connection_pool:
            con = self._connection_pool[connection_name]
            if con.closed and open_if_closed:
                con = self._connect()
                self._connection_pool[connection_name] = con
        else:
            if open_if_not_exist:
                con = self._connect()
                self._connection_pool[connection_name] = con
            else:
                raise ValueError(f"Connection {connection_name} does not exist, and open_if_not_exist = False")
        return con

    def connect(self, connection_name: str = None) -> sqlalchemy.engine.base.Connection:
        return self.connection(connection_name, open_if_not_exist=True, open_if_closed=True)

    def is_connected(self, connection_name: str = None) -> bool:
        try:
            con = self.connection(connection_name, open_if_not_exist=False, open_if_closed=False)
            return con.closed
        except ValueError:
            return False

    def close_connection(self, connection_name: str = None):
        try:
            con = self.connection(connection_name, open_if_not_exist=False, open_if_closed=False)
            con.close()
        except ValueError:
            pass

    def close_connections(self, exceptions: set = None):
        if exceptions is None:
            exceptions = set()
        for connection_name, con in self._connection_pool.items():
            if connection_name not in exceptions:
                self.log.debug(f'Closing connection {self} {connection_name}')
                con.close()

    def dispose(self):
        """
        This method leaves the possibility of checked-out connections
        remaining open, as it only affects connections that are
        idle in the pool.
        """
        self.close_connections()
        self.bind.pool.dispose()

    def session(self, autocommit: bool = False):
        return Session(bind=self.bind, autocommit=autocommit)

    def _begin(self, connection_name: str) -> sqlalchemy.engine.base.Transaction:
        tx = self.connection(connection_name=connection_name).begin()
        self._transactions[connection_name] = tx
        return tx

    def begin(self, connection_name: str = None) -> sqlalchemy.engine.base.Transaction:
        connection_name = self.resolve_connection_name(connection_name)
        if connection_name not in self._transactions:
            tx = self._begin(connection_name)
        else:
            tx = self._transactions[connection_name]
            if not tx.is_active:
                tx = self._begin(connection_name)
        return tx

    def has_active_transaction(self, connection_name: str = None):
        connection_name = self.resolve_connection_name(connection_name)
        if connection_name not in self._transactions:
            return False
        else:
            tx = self._transactions[connection_name]
            return tx.is_active

    def commit(self, connection_name: str = None):
        """
        Commit based on a connection name rather than via a
        'sqlalchemy.engine.base.Transaction' object (which you could call .commit() on

        Parameters
        ----------
        connection_name
        """
        connection_name = self.resolve_connection_name(connection_name)
        if connection_name not in self._transactions:
            self.log.debug(f"Commit: There is no transaction recorded for {self} {connection_name}")
        else:
            tx = self._transactions[connection_name]
            if tx.is_active:
                tx.commit()
                self.log.debug(f'Commit on {self} {connection_name} connection done')
            else:
                self.log.debug(f'Connection {self} {connection_name} transaction not active (commit called)')

    def rollback(self, connection_name: str = None):
        connection_name = self.resolve_connection_name(connection_name)
        if connection_name not in self._transactions:
            raise RuntimeError(f"rollback: There is no transaction recorded for {self} {connection_name}")
        else:
            tx = self._transactions[connection_name]
            if tx.is_active:
                tx.rollback()
                self.log.debug(f'Rollback on {self} {connection_name} connection done')
            else:
                raise RuntimeError(f'Connection {self} {connection_name} transaction not active (rollback called)')

    def execute(
            self,
            sql,
            *list_params,
            transaction: bool = True,
            auto_close: bool = True,
            connection_name: str = None,
            **params
    ):
        connection = None
        transaction_ctl = None
        try:
            connection = self.connect(connection_name=connection_name)
            if transaction:
                transaction_ctl = connection.begin()
            else:
                transaction_ctl = None
            result = connection.execute(sql, *list_params, **params)
            return result
        finally:
            if transaction:
                if transaction_ctl is not None:
                    transaction_ctl.commit()
            if auto_close:
                if connection is not None:
                    connection.close()
    
    def execute_procedure(
            self,
            procedure_name,
            *args,
            return_results=False,
            dpapi_connection=None
    ):
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

    def execute_direct(
            self,
            sql,
            return_results=False
    ):
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
            try:
                from sqlalchemy import inspect
            except ImportError:
                inspect = Inspector.from_engine
            inspector = inspect(self.bind)
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

    def drop_table_if_exists(
            self,
            table_name,
            schema=None,
            connection_name: str = None,
            transaction: bool = False,
            auto_close: bool = False,
    ):
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
        elif self.dialect_name == 'oracle':
            sql = textwrap.dedent(f"""\
            BEGIN
               EXECUTE IMMEDIATE 'DROP TABLE {table_name}';
            EXCEPTION
               WHEN OTHERS THEN
                  IF SQLCODE != -942 THEN
                     RAISE;
                  END IF;
            END;
            """)
        else:
            sql = f"drop table IF EXISTS {self.qualified_name(schema, table_name)}"
        self.log.debug(sql)
        self.execute(
            sql,
            transaction=transaction,
            auto_close=auto_close,
            connection_name=connection_name,
        )

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
