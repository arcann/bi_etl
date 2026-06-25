# -*- coding: utf-8 -*-
"""
Created on Dec 23, 2015

@author: Derek Wood
"""
import logging
import textwrap
from typing import Sequence

import sqlalchemy
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import DEFAULT_NAMING_CONVENTION

from bi_etl.utility.case_insensitive_set import CaseInsensitiveSet


class DatabaseMetadata(sqlalchemy.schema.MetaData):
    """
    A light wrapper over :class:`sqlalchemy.schema.MetaData`
    """

    # noinspection PyDefaultArgument
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
        """
        Initialize database metadata wrapper.

        Parameters
        ----------
        bind : sqlalchemy.engine.Engine, optional
            Database engine to bind to
        reflect : bool, optional
            Whether to reflect database schema, by default False
        schema : str, optional
            Default schema name
        quote_schema : bool, optional
            Whether to quote schema names
        naming_convention : dict, optional
            Naming convention for constraints
        info : dict, optional
            Optional metadata dictionary
        database_name : str, optional
            Name of the database
        uses_bytes_length_limits : bool, optional
            Whether database uses byte-based column length limits
        """
        super().__init__(
            schema=schema,
            quote_schema=quote_schema,
            naming_convention=naming_convention,
            info=info,
        )
        # Save parameters not saved by the base class for use in __reduce_ex__

        self.bind = bind

        self._save_reflect = reflect
        self._save_quote_schema = quote_schema

        self._table_inventory = None
        self.database_name = database_name
        self._uses_bytes_length_limits = uses_bytes_length_limits

        self._connection_pool = dict()
        self.default_connection_name = 'default'

        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def __reduce_ex__(self, protocol: int) -> tuple:
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

    def _set_parent(self, parent, **kwargs):
        pass

    def resolve_connection_name(self, connection_name: str | None = None) -> str:
        """
        Resolve connection name to use, applying database-specific rules and defaults.

        Parameters
        ----------
        connection_name : str, optional
            Connection name to resolve, uses default if None

        Returns
        -------
        str
            Resolved connection name
        """
        if connection_name is None:
            connection_name = self.default_connection_name
        # When using sqlite don't make new connections, reuse the existing one
        if self.dialect_name == 'sqlite':
            connection_name = 'sqlite'
        return connection_name

    def _connect(self) -> sqlalchemy.engine.base.Connection:
        self.log.debug(f"Connecting connection {self.bind}")
        return self.bind.connect()

    def connection(
            self,
            connection_name: str | None = None,
            open_if_not_exist: bool = True,
            open_if_closed: bool = True,
    ) -> sqlalchemy.engine.base.Connection:
        """
        Get or create a database connection from the pool by name (with a default).

        Parameters
        ----------
        connection_name : str, optional
            Name of the connection to retrieve. Default is used if not provided.
        open_if_not_exist : bool, optional
            Create connection if it doesn't exist, by default True
        open_if_closed : bool, optional
            Reopen connection if closed, by default True

        Returns
        -------
        sqlalchemy.engine.base.Connection
            Database connection

        Raises
        ------
        ValueError
            If connection doesn't exist and open_if_not_exist is False
        """
        connection_name = self.resolve_connection_name(connection_name)
        connection_key = (connection_name,)
        if connection_key in self._connection_pool:
            con = self._connection_pool[connection_key]
            if con.closed and open_if_closed:
                con = self._connect()
                self._connection_pool[connection_key] = con
        else:
            if open_if_not_exist:
                con = self._connect()
                self._connection_pool[connection_key] = con
            else:
                raise ValueError(f"Connection {connection_name} does not exist, and open_if_not_exist = False")
        return con

    def connect(
            self,
            connection_name: str | None = None,
    ) -> sqlalchemy.engine.base.Connection:
        """
        Open or retrieve (if already open) a database connection.

        Parameters
        ----------
        connection_name : str, optional
            Name of the connection

        Returns
        -------
        sqlalchemy.engine.base.Connection
            Database connection
        """
        return self.connection(
            connection_name,
            open_if_not_exist=True,
            open_if_closed=True,
        )

    def is_connected(self, connection_name: str | None = None) -> bool:
        """
        Check if a connection exists and is open.

        Parameters
        ----------
        connection_name : str, optional
            Name of the connection to check

        Returns
        -------
        bool
            True if connection exists and is open
        """
        try:
            con = self.connection(connection_name, open_if_not_exist=False, open_if_closed=False)
            return con.closed
        except ValueError:
            return False

    def close_connection(self, connection_name: str | None = None):
        """
        Close a specific connection.

        Parameters
        ----------
        connection_name : str, optional
            Name of the connection to close
        """
        try:
            con = self.connection(connection_name, open_if_not_exist=False, open_if_closed=False)
            con.close()
        except ValueError:
            pass

    def close_connections(self, exceptions: set | None = None):
        """
        Close all connections except those in the exceptions set.

        Parameters
        ----------
        exceptions : set, optional
            Set of connection names to exclude from closing
        """
        if exceptions is None:
            exceptions = set()
        for connection_key, con in self._connection_pool.items():
            connection_name = connection_key[0]
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

    def session(self) -> Session:
        """
        Create a new SQLAlchemy ORM session.

        Returns
        -------
        sqlalchemy.orm.Session
            New database session
        """
        return Session(bind=self.bind)

    def _begin(self, connection_name: str) -> sqlalchemy.engine.base.Transaction:
        tx = self.connection(connection_name=connection_name).begin()
        return tx

    def begin(self, connection_name: str | None = None) -> sqlalchemy.engine.base.Transaction:
        """
        Begin a new transaction or return the active transaction.

        Parameters
        ----------
        connection_name : str, optional
            Name of the connection

        Returns
        -------
        sqlalchemy.engine.base.Transaction
            Active transaction
        """
        connection_name = self.resolve_connection_name(connection_name)
        tx = self.transaction(connection_name=connection_name)
        if tx is None:
            tx = self._begin(connection_name)
        else:
            if not tx.is_active:
                tx = self._begin(connection_name)
        return tx

    def transaction(self, connection_name: str | None = None) -> sqlalchemy.engine.base.Transaction | None:
        """
        Get the current transaction for a connection or None if no transaction has been started.

        Parameters
        ----------
        connection_name : str, optional
            Name of the connection

        Returns
        -------
        sqlalchemy.engine.base.Transaction
            Current transaction, or None if no active transaction
        """
        conn = self.connection(connection_name=connection_name)
        nested_trans = conn.get_nested_transaction()
        if nested_trans is not None:
            return nested_trans
        else:
            return conn.get_transaction()

    def has_active_transaction(self, connection_name: str | None = None) -> bool:
        """
        Check if a connection has an active transaction.

        Parameters
        ----------
        connection_name : str, optional
            Name of the connection to check

        Returns
        -------
        bool
            True if an active transaction exists
        """
        tx = self.transaction(connection_name=connection_name)
        if tx is None:
            return False
        return tx.is_active

    def commit(self, connection_name: str | None = None):
        """
        Commit based on a connection name rather than via a
        'sqlalchemy.engine.base.Transaction' object (which you could call .commit() on)

        Parameters
        ----------
        connection_name
        """
        if not self.has_active_transaction(connection_name=connection_name):
            self.log.debug(f"Commit: There is no active transaction recorded for {self} {connection_name}")
        else:
            tx = self.transaction(connection_name=connection_name)
            self.log.info(f'Commit on {self} {connection_name} connection started')
            if tx is None:
                self.log.debug(f"Commit: There is no active transaction recorded for {self} {connection_name}")
            assert tx is not None
            tx.commit()
            self.log.debug(f'Commit on {self} {connection_name} connection done')

    def rollback(self, connection_name: str | None = None):
        """
        Rollback the active transaction for a connection.

        Parameters
        ----------
        connection_name : str, optional
            Name of the connection

        Raises
        ------
        RuntimeError
            If no active transaction exists
        """
        if not self.has_active_transaction(connection_name=connection_name):
            raise RuntimeError(f"rollback: There is no active transaction recorded for {self} {connection_name}")
        else:
            tx = self.transaction(connection_name=connection_name)
            if tx is None:
                raise RuntimeError(f"rollback: There is no active transaction recorded for {self} {connection_name}")
            tx.rollback()
            self.log.info(f'Rollback on {self} {connection_name} connection done')

    def execute(
            self,
            sql: str | sqlalchemy.sql.expression.Executable,
            *list_params,
            transaction: bool = True,
            auto_close: bool = True,
            connection_name: str | None = None,
            **params
    ) -> sqlalchemy.engine.Result | sqlalchemy.engine.CursorResult:
        """
        Execute SQL statement with optional transaction management.

        Parameters
        ----------
        sql : str or sqlalchemy.sql.expression.Executable
            SQL statement to execute
        *list_params : tuple
            Positional parameters for the SQL
        transaction : bool, optional
            Whether to wrap in a transaction, by default True
        auto_close : bool, optional
            Whether to close connection after execution, by default True
        connection_name : str, optional
            Name of the connection to use
        **params : dict
            Named parameters for the SQL

        Returns
        -------
        sqlalchemy.engine.Result
            Query result
        """
        connection = None
        try:
            connection = self.connect(
                connection_name=connection_name,
            )
            if isinstance(sql, str):
                sql = sqlalchemy.text(sql)

            current_transaction = None
            if transaction or not connection.in_transaction():
                do_begin = True
                current_transaction = connection.get_transaction()
                if current_transaction is not None:
                    if not current_transaction.is_active:
                        # Work-around for connection.begin in Name: sqlalchemy Version: 2.0.49
                        # which only checks if _transaction is None it does not check for is_active
                        connection._transaction = None
                        current_transaction = None
                    else:
                        # Already in active transaction
                        do_begin = False
                # Equivalent to Autocommit
            else:
                do_begin = False

            try:
                if do_begin:
                    with connection.begin():
                        result = connection.execute(sql, *list_params, **params)
                else:
                    result = connection.execute(sql, *list_params, **params)
            except InvalidRequestError as e:
                if current_transaction is not None:
                    self.log.error(f"{e} with trans {current_transaction!r}")
                else:
                    self.log.error(f"{e}")
                raise

            return result
        finally:
            if auto_close:
                if connection is not None:
                    connection.close()

    def execute_inside_trans(
            self,
            sql: str | sqlalchemy.sql.expression.Executable,
            *list_params,
            connection_name: str | None = None,
            **params
    ):
        """
        Execute SQL within an existing transaction without auto-closing.

        Parameters
        ----------
        sql : str or sqlalchemy.sql.expression.Executable
            SQL statement to execute
        *list_params : tuple
            Positional parameters for the SQL
        connection_name : str, optional
            Name of the connection to use
        **params : dict
            Named parameters for the SQL
        """
        self.execute(
            sql=sql,
            connection_name=connection_name,
            transaction=False,
            auto_close=False,
            *list_params,
            **params
        )

    def execute_procedure(
            self,
            procedure_name: str,
            *args,
            return_results: bool = False,
            dpapi_connection=None
    ) -> Sequence[sqlalchemy.engine.Row] | None:
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
        log.debug(f"Calling procedure {procedure_name} {args}")

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
            sql: str,
            return_results: bool = False
    ) -> Sequence[sqlalchemy.engine.Row] | None:
        """
        Execute SQL directly using raw DBAPI connection.

        Parameters
        ----------
        sql : str
            SQL statement to execute
        return_results : bool, optional
            Whether to return result rows, by default False

        Returns
        -------
        list or None
            List of result rows if return_results is True, otherwise None
        """
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

    def table_inventory(self, schema: str | None = None, force_reload: bool = False) -> set[str]:
        """
        Get a case-insensitive set of table names for a schema.

        Parameters
        ----------
        schema : str, optional
            Schema name to query, None for default schema
        force_reload : bool, optional
            Whether to force reload from database, by default False

        Returns
        -------
        CaseInsensitiveSet
            Set of table names in the schema
        """
        if self._table_inventory is None:
            self._table_inventory = dict()
        if schema not in self._table_inventory or force_reload:
            try:
                from sqlalchemy import inspect
            except ImportError:
                inspect = Inspector.from_engine
            inspector = inspect(self.bind)
            self._table_inventory[schema] = CaseInsensitiveSet(inspector.get_table_names(schema=schema))
        return self._table_inventory[schema]

    @staticmethod
    def qualified_name(schema: str | None, table: str) -> str:
        """
        Create a qualified table name from schema and table.

        Parameters
        ----------
        schema : str or None
            Schema name
        table : str
            Table name

        Returns
        -------
        str
            Qualified table name (schema.table) or just table name if no schema
        """
        if schema is not None:
            return schema + '.' + table
        else:
            return table

    def rename_table(self, schema: str | None, table_name: str, new_table_name: str):
        """
        Rename a table using database-specific syntax.

        Parameters
        ----------
        schema : str or None
            Schema containing the table
        table_name : str
            Current table name
        new_table_name : str
            New table name
        """
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
            table_name: str,
            schema: str | None = None,
            connection_name: str | None = None,
            transaction: bool = False,
            auto_close: bool = False,
    ):
        """
        Drop a table if it exists using database-specific syntax.

        Parameters
        ----------
        table_name : str
            Name of the table to drop
        schema : str, optional
            Schema containing the table
        connection_name : str, optional
            Name of the connection to use
        transaction : bool, optional
            Whether to use a transaction, by default False
        auto_close : bool, optional
            Whether to close connection after execution, by default False
        """
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
    def dialect(self) -> sqlalchemy.engine.interfaces.Dialect:
        """
        Get the SQLAlchemy dialect for the bound engine.

        Returns
        -------
        sqlalchemy.engine.interfaces.Dialect
            Database dialect
        """
        return self.bind.dialect

    @property
    def dialect_name(self) -> str:
        """
        Get the name of the database dialect.

        Returns
        -------
        str
            Dialect name (e.g., 'mssql', 'oracle', 'sqlite')
        """
        return self.bind.dialect.name

    @property
    def uses_bytes_length_limits(self) -> bool:
        """
        Check if database uses byte-based rather than character-based length limits.

        Returns
        -------
        bool
            True if database uses byte-based length limits (e.g., Oracle, Redshift)
        """
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
