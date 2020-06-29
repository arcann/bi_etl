"""
Created on Sep 17, 2014

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import functools
import typing
from datetime import datetime
from operator import attrgetter
from typing import Iterable

import sqlalchemy
from sqlalchemy.sql import sqltypes, functions
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.schema import Column

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.database import DatabaseMetadata
from bi_etl.exceptions import NoResultFound, MultipleResultsFound
from bi_etl.lookups.lookup import Lookup
from bi_etl.scheduler.task import ETLTask
from bi_etl.statistics import Statistics
from bi_etl.utility import dict_to_str

__all__ = ['ReadOnlyTable']


# Pylint does not like references to self.table.columns aka self.columns
# pylint: disable=unsupported-membership-test, unsubscriptable-object, not-an-iterable


class ReadOnlyTable(ETLComponent):
    """ 
    Reads all columns from a database table or view. 
    Rows can be filtered using the :py:meth:`~bi_etl.components.readonlytable.ReadOnlyTable.where` method.
    
    Parameters
    ----------
    task : ETLTask
        The  instance to register in (if not None)

    database : bi_etl.scheduler.task.Database
        The database to find the table/view in.

    table_name : str
        The name of the table/view.

    include_only_columns : list, optional
        Optional. A list of specific columns to include when reading the table/view.
        All other columns are excluded.

    exclude_columns : list, optional
        Optional. A list of columns to exclude when reading the table/view.
         
    Attributes
    ----------    
    delete_flag : str, optional
        The name of the delete_flag column, if any.
    
    delete_flag_yes : str, optional
        The value of delete_flag for deleted rows.
    
    delete_flag_no : str, optional
        The value of delete_flag for *not* deleted rows.
        
    special_values_descriptive_columns: list, optional
         A list of columns that should get longer descriptive text (e.g. 'Missing' instead of '?') in 
         :meth:`get_missing_row`, 
         :meth:`get_invalid_row`, 
         :meth:`get_not_applicable_row`, 
         :meth:`get_various_row`
    
    log_first_row : boolean
        Should we log progress on the the first row read. *Only applies if Table is used as a source.*
        (inherited from ETLComponent)
        
    max_rows : int, optional
        The maximum number of rows to read. *Only applies if Table is used as a source.*
        (inherited from ETLComponent)
        
    maintain_cache_during_load: boolean
        Default = True. Should we maintain the lookup caches as we load records.
        Can safely be set to False for sources that will never use a key combination twice
        during a single load. Setting it to False should improve performance.
        
    primary_key: list
        The name of the primary key column(s). Only impacts trace messages.  Default=None.
        If not passed in, will use the database value, if any.
        (inherited from ETLComponent)

    natural_key: list
        The list of natural key columns (as Column objects).
        Default is None
        
    progress_frequency: int
        How often (in seconds) to output progress messages. None for no progress messages.
        (inherited from ETLComponent)
    
    progress_message: str
        The progress message to print. Default is ``"{logical_name} row # {row_number}"``. 
        Note ``logical_name`` and ``row_number`` subs.
        (inherited from ETLComponent)
    
    """
    PK_LOOKUP = 'PK'
    NK_LOOKUP = 'NK'
    DEFAULT_CONNECTION_NAME = 'default'

    def __init__(self,
                 task: typing.Optional[ETLTask],
                 database: DatabaseMetadata,
                 table_name: str,
                 table_name_case_sensitive: bool = False,
                 schema: str = None,
                 exclude_columns: list = None,
                 include_only_columns: list = None,
                 **kwargs
                 ):
        # Don't pass kwargs up. They should be set here at the end
        super(ReadOnlyTable, self).__init__(task=task,
                                            logical_name=table_name,
                                            )
        self.trace_sql = False
        self.always_fallback_to_db = True
        self._maintain_cache_during_load = True

        self.__compile_cache = {}
        self.__delete_flag = None
        self.delete_flag_yes = 'Y'
        self.delete_flag_no = 'N'

        self.special_values_descriptive_columns = set()
        self.special_values_descriptive_min_length = 14  # Long enough to hold 'Not Applicable'

        self.database = database
        self.__connection_pool = dict()
        self._table = None
        self._columns = None
        self._column_names = None
        self._column_name_index = None
        self._excluded_columns = None
        self._table_name = table_name
        self.schema = schema
        if table_name is not None:
            # Note from sqlalchemy:
            # Names which contain no upper case characters will be treated as case insensitive names, and will not 
            # be quoted unless they are a reserved word. 
            # Names with any number of upper case characters will be quoted and sent exactly. Note that this behavior
            # applies even for databases which standardize upper case names as case insensitive such as Oracle.
            if '.' in table_name:
                self.schema, table_name = table_name.split('.', 1)

            if not table_name_case_sensitive:
                table_name = table_name.lower()
            try:
                self.table = sqlalchemy.schema.Table(table_name, database, schema=self.schema, autoload=True, quote=False)
            except Exception as e:
                try:
                    self.log.debug(f"Exception {repr(e)} occurred while obtaining definition of {table_name} from the database schema {self.schema}")
                finally:
                    raise

        self.__natural_key_override = False
        self.__natural_key = None

        if exclude_columns:
            self.exclude_columns(exclude_columns)

        if include_only_columns:
            self.include_only_columns(include_only_columns)

        self.custom_special_values = dict()

        # Should be the last call of every init            
        self.set_kwattrs(**kwargs)

    def __repr__(self):
        template = "{cls}(task={task}," \
            "logical_name={logical_name}," \
            "primary_key={primary_key}," \
            "delete_flag={delete_flag})"
        return template.format(
            cls=self.__class__.__name__,
            task=self.task,
            logical_name=self.logical_name,
            primary_key=self.primary_key,
            delete_flag=self.delete_flag,
        )

    @property
    def delete_flag(self):
        return self.__delete_flag

    @delete_flag.setter
    def delete_flag(self, value):
        self.__delete_flag = value
        if self.__delete_flag is not None:
            self.custom_special_values[self.delete_flag] = self.delete_flag_no

    @property
    def table_name(self):
        """
        The table name
        """
        return self._table_name

    @property
    def qualified_table_name(self):
        """
        The table name
        """
        if self._table.schema is not None:
            return self._table.schema + '.' + self._table_name
        else:
            return self._table_name

    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, new_table_object):
        self._table = new_table_object
        self._columns = list(self._table.columns)
        self.column_names = list(map(attrgetter('name'), self._columns))
        self._column_name_index = dict()
        for column in self._columns:
            index_version_of_column_name = column.name.lower()
            if index_version_of_column_name in self._column_name_index:
                existing_entry = self._column_name_index[index_version_of_column_name]
                if isinstance(existing_entry, list):
                    existing_entry.append(column)
                else:
                    new_list = list()
                    new_list.append(existing_entry)
                    new_list.append(column)
                    self._column_name_index[index_version_of_column_name] = new_list
                self._column_name_index[index_version_of_column_name] = column
            else:  # New entry
                self._column_name_index[index_version_of_column_name] = column
        self.logical_name = self._table_name = new_table_object.name
        # Get the primary key from the table
        self.primary_key = list(self._table.primary_key)

    @property
    def connection_pool(self):
        return self.__connection_pool.copy()

    @property
    def maintain_cache_during_load(self) -> bool:
        return True

    @maintain_cache_during_load.setter
    def maintain_cache_during_load(self, value: bool):
        self._maintain_cache_during_load = value

    def set_columns(self, columns):
        # Remove columns from the table
        for col in self._columns:
            col.table = None
        # Clear table from columns passed in
        for col in columns:
            col.table = None
        # Remove the table definition so we can add it back below
        self._columns = columns
        self._column_names = None
        self.database.remove(self.table)
        self.table = sqlalchemy.schema.Table(self.table_name, self.database, *self._columns, schema=self.schema, quote=False)

    def exclude_columns(self, columns_to_exclude):
        """
        Exclude columns from the table. Removes them from all SQL statements.
        
        columns_to_exclude : list
            A list of columns to exclude when reading the table/view.
        """

        # =======================================================================
        # Implementation notes:
        # This method accesses protected _columns in the table and removes them.
        # 
        # This implementation needs to reverse what this does...
        #     # see https://github.com/zzzeek/sqlalchemy/blob/master/lib/sqlalchemy/sql/selectable.py
        #     # see class TableClause(Immutable, FromClause):
        #     def append_column(self, c):
        #         self._columns[c.key] = c
        #         c.table = self
        # ===================================================================
        # for ex_name in columns_to_exclude:                
        #     if ex_name in self.columns:
        #         exclude_column_obj = self.columns[ex_name]
        #         self.log.debug('Excluding column {}'.format(exclude_column_obj))
        #         exclude_column_obj.table = None
        #         self.table._columns.remove(exclude_column_obj)
        # self._columns = list(self.table.columns)
        # self.column_names = list(map(attrgetter('name'), self._columns))
        # =======================================================================
        if columns_to_exclude is not None:
            # This method builds a new Table object with the non-excluded columns.
            if self._excluded_columns is None:
                self._excluded_columns = set(columns_to_exclude)
            else:
                self._excluded_columns.update(columns_to_exclude)

        # noinspection PyTypeChecker
        for ex_name in self._excluded_columns:
            try:
                exclude_column_obj = self.get_column(ex_name)
                if exclude_column_obj in self._columns:
                    self.log.debug('Excluding column {}'.format(exclude_column_obj))
                    self._columns.remove(exclude_column_obj)
            except KeyError:
                # Already not there
                pass
        self.set_columns(self._columns)

    def include_only_columns(self, columns_to_include):
        """
        Include only specified columns in the table definition.
        Columns that are non included are removed them from all SQL statements.

        columns_to_include : list
            A list of columns to include when reading the table/view.
        """
        columns_to_exclude = self.column_names_set.difference(columns_to_include)
        self.exclude_columns(columns_to_exclude)

    def _get_usable_connection_name(self, connection_name: typing.Optional[str] = None) -> str:
        if connection_name is None:
            connection_name = self.DEFAULT_CONNECTION_NAME
        # When using sqlite don't make new connections, reuse the existing one
        if self.database.dialect_name == 'sqlite':
            connection_name = 'sqlite'
        return connection_name

    def is_connected(self, connection_name: typing.Optional[str] = None) -> bool:
        try:
            con = self.connection(connection_name, open_if_not_exist=False, open_if_closed=False)
            return con.closed
        except ValueError:
            return False

    def connection(
            self,
            connection_name: typing.Optional[str] = None,
            open_if_not_exist: bool = True,
            open_if_closed: bool = True,
    ) -> sqlalchemy.engine.base.Connection:
        if self.table is None:
            raise ValueError("connection called with no table defined")
        connection_name = self._get_usable_connection_name(connection_name)

        if connection_name in self.__connection_pool:
            con = self.__connection_pool[connection_name]
            if con.closed and open_if_closed:
                con = self.database.connect()
                self.__connection_pool[connection_name] = con
        else:
            if open_if_not_exist:
                con = self.database.connect()
                self.__connection_pool[connection_name] = con
            else:
                raise ValueError(f'Connection {connection_name} does not exist, and open_if_not_exist = False')
        return con

    def set_connection(self, connection, connection_name: str = None):
        connection_name = self._get_usable_connection_name(connection_name)
        if connection_name in self.__connection_pool:
            self.__connection_pool[connection_name].close()
        self.__connection_pool[connection_name] = connection

    def close_connection(self, connection_name: str = None):
        connection_name = self._get_usable_connection_name(connection_name)
        if connection_name in self.__connection_pool:
            self.log.debug(f'Closing connection {self} {connection_name}')
            con = self.__connection_pool[connection_name]
            con.close()

    def close_connections(self, exceptions: typing.Optional[set] = None):
        if exceptions is None:
            exceptions = set()
        for connection_name, con in self.__connection_pool.items():
            if connection_name not in exceptions:
                self.log.debug(f'Closing connection {self} {connection_name}')
                con.close()

    def close(self):
        for lookup in self.lookups.values():
            lookup.add_size_to_stats()
        if len(self.__compile_cache) > 0:
            cache_stats = self.get_stats_entry('compile cache', print_start_stop_times=False)
            cache_stats['entries'] = len(self.__compile_cache)
            del self.__compile_cache
        self.close_connections()
        super(ReadOnlyTable, self).close()

    def __del__(self):
        self.close_connections()

    def __exit__(self, exit_type, exit_value, exit_traceback):  # @ReservedAssignment
        # Close the database connection
        self.close()

    def execute(self, statement, *list_params, **params) -> sqlalchemy.engine.ResultProxy:
        """

        Parameters
        ----------
        statement:
            The SQL statement to execute

        connection_name:
            Name of the pooled connection to use
            Defaults to DEFAULT_CONNECTION_NAME

        Returns
        -------
        sqlalchemy.engine.ResultProxy with results
        """
        # compiled_cache created huge memory usage. It seems like each lookup created it's own entry
        # execution_options(compiled_cache=self.__compile_cache)
        if self.trace_sql:
            self.log.debug('SQL={}'.format(statement))
            try:
                self.log.debug('parameters={}'.format(dict_to_str(statement.parameters)))
            # pylint: disable=broad-except
            except Exception as e:
                self.log.debug(e)
            self.log.debug('list_params={}'.format(list_params))
            self.log.debug('params={}'.format(params))
            self.log.debug('-------------------------')
        if 'connection_name' in params:
            connection_name = params['connection_name'] or self.DEFAULT_CONNECTION_NAME
            del params['connection_name']
        else:
            connection_name = self.DEFAULT_CONNECTION_NAME
        connection = self.connection(connection_name=connection_name)
        return connection.execute(statement, *list_params, **params)

    def get_one(self, statement=None, connection_name: str = 'get_one'):
        """
        Executes and gets one row from the statement.

        Parameters
        ----------
        statement:
            The SQL statement to execute

        connection_name:
            Name of the pooled connection to use
            Defaults to 'get_one'
        
        Returns
        -------
        row : :class:`~bi_etl.components.row.row_case_insensitive.Row`
            The row returned
            
        Raises
        ------
        NoResultFound
            No rows returned.
            
        MultipleResultsFound
            More than one row was returned.
        """
        if statement is None:
            statement = self.select()
        results = self.execute(statement, connection_name=connection_name)
        row1 = results.fetchone()
        if row1 is None:
            raise NoResultFound()
        row2 = results.fetchone()
        if connection_name == 'get_one':
            self.close_connection(connection_name)
        if row2 is not None:
            raise MultipleResultsFound([row1, row2])
        return self.Row(row1)

    def select(self, column_list: typing.Optional[list] = None,
               exclude_cols: typing.Optional[set] = None) -> sqlalchemy.sql.expression.Select:
        """
        Builds a select statement for this table. 
        
        Returns
        -------
        statement: 
                    
        """
        if exclude_cols is not None and column_list is not None:
            raise ValueError("select can't accept both column_list and exclude_cols")
        if column_list is None:
            if exclude_cols is None:
                return sqlalchemy.select(self.columns)
            else:
                # Make sure all entries are column objects
                if isinstance(exclude_cols, str):
                    exclude_cols = [exclude_cols]
                # noinspection PyTypeChecker
                exclude_col_objs = set([self.get_column(c) for c in exclude_cols])
                filtered_column_list = [c for c in self.columns if c not in exclude_col_objs]
                return sqlalchemy.select(filtered_column_list)
        else:
            column_obj_list = list()
            # noinspection PyTypeChecker
            for c in column_list:
                if isinstance(c, str):
                    column_obj_list.append(self.get_column(c))
                else:
                    column_obj_list.append(c)
            return sqlalchemy.select(column_obj_list)

    def _generate_key_values_dict(self, key_names=None, key_values=None, lookup_name=None, other_values_dict=None):

        if key_names is not None and lookup_name is not None:
            raise ValueError('Both key_names and lookup_name provided. Please use one or the other')

        # Get key names from key_names or lookup
        if key_names is None:
            if lookup_name is not None:
                key_names = self.get_lookup(lookup_name).lookup_keys
            else:
                self._check_pk_lookup()
                key_names = self.primary_key
        else:
            # Handle case where we have a single key name item and not a list or dict
            if isinstance(key_names, str):
                key_names = [key_names]

        # Handle case where we have a single key value item and not a list
        if isinstance(key_values, str):
            key_values = [key_values]

        key_values_dict = dict()
        if isinstance(key_values, typing.MutableMapping):
            for key_name in key_names:
                if key_name in key_values:
                    key_values_dict[key_name] = key_values[key_name]
                elif other_values_dict is not None and key_name in other_values_dict:
                    key_values_dict[key_name] = other_values_dict[key_name]
                else:
                    raise ValueError('No key value provided for {}'.format(key_name))
        elif key_values is None:
            if other_values_dict is None:
                raise ValueError('No key values provided')
            else:
                for key_name in key_names:
                    if key_name in other_values_dict:
                        key_values_dict[key_name] = other_values_dict[key_name]
                    else:
                        raise ValueError('No key value provided for {}'.format(key_name))
        else:
            # Otherwise we'll assume key_values is a list or iterable like one
            key_values_dict = dict()
            assert len(key_names) == len(key_names), 'key values list does not match length of key names list'
            for key_name, key_value in zip(key_names, key_values):
                key_values_dict[key_name] = key_value
        return key_values_dict

    def cache_iterator(self):
        pk_lookup = None
        try:
            pk_lookup = self.get_pk_lookup()
            if not pk_lookup.cache_enabled:
                for lookup_name in self.__lookups:
                    lookup = self.get_lookup(lookup_name)
                    if lookup.cache_enabled:
                        pk_lookup = lookup
                        break
        except KeyError:
            pass

        if pk_lookup is None:
            raise LookupError("Unable to find filled lookup for cache_iterator")
        else:
            # Note in this case the outer call where / iter_result will process the criteria
            self.log.debug(f"Using lookup {pk_lookup} as source for cache_iterator")
            return pk_lookup

    # We add the following args at this level
    #   criteria: so they can be passed down to the database
    #   use_cache_as_source: to we can use the cache instead of the database
    #   stats_id, parent_stats: So we can capture SQL execution time in the right place.
    def _raw_rows(self,
                  criteria_list: list = None,
                  criteria_dict: dict = None,
                  order_by: list = None,
                  column_list: list = None,
                  exclude_cols: list = None,
                  use_cache_as_source: bool = None,
                  connection_name: str = None,
                  stats_id: str = None,
                  parent_stats: Statistics = None):
        """
        Iterate over rows matching ``criteria``
        
        Parameters
        ----------
        criteria_list : string or list of strings
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            http://docs.sqlalchemy.org/en/rel_1_0/core/selectable.html?highlight=where#sqlalchemy.sql.expression.Select.where
        criteria_dict : dict
            Dict keys should be columns, values are set using = or in
        order_by: string or list of strings
            Each value should represent a column to order by.
        exclude_cols: list
            List of columns to exclude from the results. (Only if getting from the database)
        use_cache_as_source: bool
            Should we read rows from the cache instead of the table
        stats_id: string
            Name of this step for the ETLTask statistics.
        parent_stats: bi_etl.statistics.Statistics
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        connection_name:
            The name of the pooled connection to use
    
        Yields
        ------
        row: :class:`~bi_etl.components.row.row_case_insensitive.Row`
            Row object with contents of a table/view row that matches ``criteria_list`` and ``criteria_dict``
        """
        if stats_id is None:
            stats_id = self.default_stats_id
        stats = self.get_stats_entry(stats_id=stats_id, parent_stats=parent_stats)

        if use_cache_as_source is None:
            use_cache_as_source = True
            use_cache_as_source_requested = False
        else:
            use_cache_as_source_requested = use_cache_as_source

        pk_lookup = None
        if use_cache_as_source:
            if not (self.cache_filled and self.cache_clean):
                use_cache_as_source = False
                if use_cache_as_source_requested:
                    self.log.warning("Cache not filled requires using database as source for {}".format(stats))
            elif order_by is not None:
                use_cache_as_source = False
                if use_cache_as_source_requested:
                    self.log.warning("where had to use DB source to honor order_by (and possibly criteria)")
            elif criteria_list is not None:
                if use_cache_as_source_requested:
                    raise ValueError(f"Non dict criteria ({criteria_list}) requires using database as source for {stats} on {self}")
            else:
                # Find the filled cache
                try:
                    pk_lookup = self.get_pk_lookup()
                    if not pk_lookup.cache_enabled:
                        use_cache_as_source = False
                        if use_cache_as_source_requested:
                            self.log.debug("PK cache not filled. "
                                           "Looking for another lookup to use for {}".format(stats))
                        for lookup_name in self.__lookups:
                            lookup = self.get_lookup(lookup_name)
                            if lookup.cache_enabled:
                                use_cache_as_source = True
                                pk_lookup = lookup
                                break
                        if not use_cache_as_source:
                            if use_cache_as_source_requested:
                                self.log.debug("Unable to find filled lookup. "
                                               "Requires using database as source for {}".format(stats))
                except KeyError:
                    use_cache_as_source = False
                    if use_cache_as_source_requested:
                        self.log.debug("KeyError finding lookup. "
                                       "Requires using database as source for {}".format(stats))

        if use_cache_as_source:
            # Note in this case the outer call where / iter_result will process the criteria
            self.log.debug("Using lookup {} as source for {}".format(pk_lookup, stats))
            self._iterator_applied_filters = False
            return pk_lookup
        else:
            self.log.debug("Using database as source for {}".format(stats))
            self._iterator_applied_filters = True
            stmt = self.select(column_list=column_list,
                               exclude_cols=exclude_cols,
                               )
            if criteria_dict is not None:
                for col, value in criteria_dict.items():
                    stmt = stmt.where(self.get_column(col) == value)
            if criteria_list is not None:
                if isinstance(criteria_list, list):
                    for c in criteria_list:
                        if isinstance(c, str):
                            stmt = stmt.where(text(c))
                        elif isinstance(c, typing.Mapping):
                            for col, value in c.items():
                                stmt = stmt.where(self.get_column(col) == value)
                        else:
                            stmt = stmt.where(c)
                elif isinstance(criteria_list, str):
                    stmt = stmt.where(text(criteria_list))
                else:
                    stmt = stmt.where(criteria_list)
            if order_by is not None:
                if isinstance(order_by, list):
                    stmt = stmt.order_by(*order_by)
                else:
                    stmt = stmt.order_by(order_by)
            self.log.debug(stmt)
            stats.timer.start()
            select_result = self.execute(stmt, connection_name=connection_name)
            stats.timer.stop()
            return select_result

    def where(self,
              criteria_list: list = None,
              criteria_dict: dict = None,
              order_by: list = None,
              column_list: typing.List[typing.Union[Column, str]] = None,
              exclude_cols: typing.List[typing.Union[Column, str]] = None,
              use_cache_as_source: bool = None,
              connection_name: str = 'select',
              progress_frequency: int = None,
              stats_id: str = None,
              parent_stats: Statistics = None,
              ) -> Iterable[Row]:
        """

        Parameters
        ----------
        criteria_list:
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            http://docs.sqlalchemy.org/en/rel_1_0/core/selectable.html?highlight=where#sqlalchemy.sql.expression.Select.where
        criteria_dict:
            Dict keys should be columns, values are set using = or in
        order_by:
            List of sort keys
        column_list:
            List of columns (str or Column)
        exclude_cols
        use_cache_as_source
        connection_name:
            Name of the pooled connection to use
        progress_frequency
        stats_id
        parent_stats

        Returns
        -------
        rows

        """
        result_rows_iter = self._raw_rows(criteria_list=criteria_list,
                                          criteria_dict=criteria_dict,
                                          order_by=order_by,
                                          column_list=column_list,
                                          exclude_cols=exclude_cols,
                                          use_cache_as_source=use_cache_as_source,
                                          connection_name=connection_name,
                                          stats_id=stats_id,
                                          parent_stats=parent_stats,
                                          )
        return self.iter_result(result_rows_iter,
                                criteria_dict=criteria_dict,
                                progress_frequency=progress_frequency,
                                stats_id=stats_id,
                                parent_stats=parent_stats,
                                columns_in_order=column_list,
                                )

    def order_by(self,
                 order_by: list,
                 stats_id: str = None,
                 parent_stats: Statistics = None,
                 ) -> Iterable[Row]:
        """
        Iterate over all rows in order provided.
        
        Parameters
        ----------
        order_by: string or list of strings
            Each value should represent a column to order by.
        stats_id: string
            Name of this step for the ETLTask statistics.
        parent_stats: bi_etl.statistics.Statistics
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.          
    
        Yields
        ------
        row: :class:`~bi_etl.components.row.row_case_insensitive.Row`
            :class:`~bi_etl.components.row.row_case_insensitive.Row` object with contents of a table/view row
        """
        return self.where(order_by=order_by,
                          stats_id=stats_id,
                          parent_stats=parent_stats
                          )

    @property
    def columns(self) -> typing.List['sqlalchemy.sql.expression.ColumnElement']:
        """
        A named-based collection of :class:`sqlalchemy.sql.expression.ColumnElement` objects in this table/view. 
        
        """
        return self._columns

    def get_column(self, column: typing.Union[str, Column]) -> Column:
        """
        Get the :class:`sqlalchemy.sql.expression.ColumnElement` object for a given column name.
        """
        if isinstance(column, Column):
            if column.table == self.table:
                return column
            else:
                return self.get_column(column.name)
        else:
            if column.lower() in self._column_name_index:
                index_entry = self._column_name_index[column.lower()]
                if isinstance(index_entry, list):
                    # More than one column with that name. 
                    # Case sensitivity required
                    raise KeyError('{} does not have a column named {} '
                                   'however multiple other case versions exist'.format(self.table_name, column))
                else:
                    return index_entry
            else:
                raise KeyError(
                    '{} does not have a column named {} (or lowercase {}) it does have {}'.format(self.table_name, column, column.lower(), self._column_name_index.keys()))

    def get_column_name(self, column):
        """
        Get the column name given a possible :class:`sqlalchemy.sql.expression.ColumnElement` object.
        """
        if isinstance(column, Column):
            return self.table.columns[column.name].name
        else:
            return self.table.columns[column].name

    def max(self, column, where=None, connection_name: str = 'max'):
        """
        Query the table/view to get the maximum value of a given column. 
        
        Parameters
        ----------
        column: str or :class:`sqlalchemy.sql.expression.ColumnElement`.
            The column to get the max value of

        where: string or list of strings
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`
            http://docs.sqlalchemy.org/en/rel_1_0/core/selectable.html?highlight=where#sqlalchemy.sql.expression.Select.where

        connection_name:
            Name of the pooled connection to use
            Defaults to 'max'
        
        Returns
        -------
        max : depends on column datatype
            
        """
        c = self.get_column(column)
        stmt = self.select([functions.max(c).label("max_1")])
        if where is not None:
            if isinstance(where, list):
                for c in where:
                    stmt = stmt.where(c)
            else:
                stmt = stmt.where(where)
        max_row = self.get_one(stmt, connection_name=connection_name)
        if connection_name == 'max':
            self.close_connection(connection_name)
        max_value = max_row['max_1']
        return max_value

    def count(self, column: str = None, where=None) -> int:
        """
        Query the table/view to get the count of a given column.

        Parameters
        ----------
        column: str or :class:`sqlalchemy.sql.expression.ColumnElement`.
            The column to get the max value of
        where: string or list of strings
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`
            http://docs.sqlalchemy.org/en/rel_1_0/core/selectable.html?highlight=where#sqlalchemy.sql.expression.Select.where

        Returns
        -------
        count : int

        """
        if column is not None:
            column = self.get_column(column)
        stmt = self.select([functions.count(column).label("count_1")]).select_from(self.table)
        if where is not None:
            if isinstance(where, list):
                for c in where:
                    stmt = stmt.where(c)
            else:
                stmt = stmt.where(where)
        row = self.get_one(stmt)
        count_value = row['count_1']
        return count_value

    @property
    @functools.lru_cache(maxsize=16)
    def row_name(self):
        return str(self.table)

    def generate_iteration_header(self, logical_name=None, columns_in_order=None):
        if logical_name is None:
            logical_name = self.row_name

        if columns_in_order is None:
            columns_in_order = self.column_names
            result_primary_key = self.primary_key
        else:
            result_primary_key = None

        return RowIterationHeader(logical_name=logical_name,
                                  primary_key=result_primary_key,
                                  parent=self,
                                  columns_in_order=columns_in_order)

    def get_special_row(self,
                        short_char,
                        long_char,
                        int_value,
                        date_value,
                        ):
        if self._special_row_header is None:
            self._special_row_header = self.generate_iteration_header(logical_name='get_special_row')
        row = self.Row(iteration_header=self._special_row_header)
        for column in self.columns:
            target_type = column.type
            if self.custom_special_values and column.name in self.custom_special_values:
                custom_value = self.custom_special_values[column.name]
                if custom_value == '[short_char]':
                    custom_value = short_char
                elif custom_value == '[long_char]':
                    custom_value = long_char
                elif custom_value == '[int_value]':
                    custom_value = int_value
                elif custom_value == '[date_value]':
                    custom_value = date_value
                # Note: We test for setitem because dict like containers have it but str doesn't have it.
                if hasattr(custom_value, '__setitem__'):
                    row[column.name] = custom_value[short_char]
                else:
                    row[column.name] = custom_value
            elif column.name == self.delete_flag:
                row[column.name] = 'N'
            elif isinstance(target_type, sqltypes.String):
                if column.name in self.special_values_descriptive_columns:
                    row[column.name] = long_char
                if column.type.length is None:
                    row[column.name] = long_char
                elif self.special_values_descriptive_min_length and column.type.length \
                        >= self.special_values_descriptive_min_length:
                    row[column.name] = long_char
                else:
                    row[column.name] = short_char
            elif (isinstance(target_type, sqltypes.DATE)
                  or isinstance(target_type, sqltypes.DATETIME)
                  or isinstance(target_type, sqlalchemy.types.DateTime)
                  ):
                row[column.name] = date_value
            elif (isinstance(target_type, sqltypes.INTEGER)
                  or isinstance(target_type, sqltypes.Numeric)
                  ):
                row[column.name] = int_value
            elif (isinstance(target_type, sqltypes.FLOAT)
                  or isinstance(target_type, sqltypes.Numeric)
                  ):
                row[column.name] = float(int_value)
        return row

    def get_missing_row(self):
        """
        Get a :class:`~bi_etl.components.row.row_case_insensitive.Row` 
        with the Missing special values filled in for all columns.
        
        =========== =========
        Type        Value
        =========== =========
        Integer     -9999
        Short Text  '?'
        Long Text   'Missing'
        Date        9999-9-1
        =========== =========
        """
        return self.get_special_row('?', 'Missing', -9999, datetime(9999, 9, 1))

    def get_invalid_row(self):
        """
        Get a :class:`~bi_etl.components.row.row_case_insensitive.Row` 
        with the Invalid special values filled in for all columns.
        
        =========== =========
        Type        Value
        =========== =========
        Integer     -8888
        Short Text  '!'
        Long Text   'Invalid'
        Date        9999-8-1
        =========== ========= 
        
        """
        return self.get_special_row('!', 'Invalid', -8888, datetime(9999, 8, 1))

    def get_not_applicable_row(self):
        """
        Get a :class:`~bi_etl.components.row.row_case_insensitive.Row` 
        with the Not Applicable special values filled in for all columns.
        
        =========== =========
        Type        Value
        =========== =========
        Integer     -7777
        Short Text  '~'
        Long Text   'Not Available'
        Date        9999-7-1
        =========== =========          
        """
        return self.get_special_row('~', 'Not Available', -7777, datetime(9999, 7, 1))

    def get_various_row(self):
        """
        Get a :class:`~bi_etl.components.row.row_case_insensitive.Row` 
        with the Various special values filled in for all columns.
        
        =========== =========
        Type        Value
        =========== =========
        Integer     -6666
        Short Text  '*'
        Long Text   'Various'
        Date        9999-6-1
        =========== =========
        """
        return self.get_special_row('*', 'Various', -6666, datetime(9999, 6, 1))

    def _check_pk_lookup(self):
        # Check that we have setup the PK lookup.
        # Late binding so that it will take overrides to the default lookup class
        if ReadOnlyTable.PK_LOOKUP not in self.lookups:
            if self.primary_key:
                self.define_lookup(ReadOnlyTable.PK_LOOKUP, self.primary_key)

    def fill_cache_from_source(
            self,
            source: ETLComponent,
            progress_frequency: float = 10,
            progress_message="{component} fill_cache current row # {row_number:,}",
            criteria_list: list = None,
            criteria_dict: dict = None,
            column_list: list = None,
            exclude_cols: list = None,
            order_by: list = None,
            assume_lookup_complete: bool = None,
            row_limit: int = None,
            parent_stats: Statistics = None,
            ):
        """
        Fill all lookup caches from the table.

        Parameters
        ----------
        source:
            Source compontent to get rows from.
        progress_frequency : int, optional
            How often (in seconds) to output progress messages. Default 10. None for no progress messages.
        progress_message : str, optional
            The progress message to print.
            Default is ``"{component} fill_cache current row # {row_number:,}"``. Note ``logical_name`` and ``row_number``
            substitutions applied via :func:`format`.
        criteria_list : string or list of strings
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            https://goo.gl/JlY9us
        criteria_dict : dict
            Dict keys should be columns, values are set using = or in
        column_list:
            List of columns to include
        exclude_cols: list
            Optional. Columns to exclude when filling the cache
        order_by: list
            list of columns to sort by when filling the cache (helps range caches)
        assume_lookup_complete: boolean
            Should later lookup calls assume the cache is complete?
            If so, lookups will raise an Exception if a key combination is not found.
            Default to False if filtering criteria was used, otherwise defaults to True.
        row_limit: int
            limit on number of rows to cache.
        parent_stats: bi_etl.statistics.Statistics
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        """
        super().fill_cache_from_source(
            source=source,
            progress_frequency=progress_frequency,
            progress_message=progress_message,
            criteria_list=criteria_list,
            criteria_dict=criteria_dict,
            column_list=column_list,
            exclude_cols=exclude_cols,
            order_by=order_by,
            assume_lookup_complete=assume_lookup_complete,
            row_limit=row_limit,
            parent_stats=parent_stats,
            )
        # Set the table always_fallback_to_db value based on if criteria
        # were used to load the cache and the assume_lookup_complete parameter
        if criteria_list is not None or criteria_dict is not None:
            # If criteria is used we'll default to not assuming the lookup is complete
            if assume_lookup_complete is None:
                assume_lookup_complete = False
        else:
            # If criteria is NOT used we'll default to assuming the lookup is complete
            if assume_lookup_complete is None:
                assume_lookup_complete = True
        self.always_fallback_to_db = not assume_lookup_complete
        self.log.info(f'Lookups will always_fallback_to_db = {self.always_fallback_to_db}')

    def get_lookup(self, lookup_name) -> Lookup:
        self._check_pk_lookup()

        if lookup_name is None:
            lookup_name = ReadOnlyTable.PK_LOOKUP
        return super().get_lookup(lookup_name=lookup_name)

    def get_pk_lookup(self):
        return self.get_lookup(ReadOnlyTable.PK_LOOKUP)

    def get_primary_key_value_list(self, row) -> list:
        self._check_pk_lookup()
        return self.lookups[ReadOnlyTable.PK_LOOKUP].get_list_of_lookup_column_values(row)

    def get_primary_key_value_tuple(self, row) -> tuple:
        self._check_pk_lookup()
        return self.lookups[ReadOnlyTable.PK_LOOKUP].get_hashable_combined_key(row)

    @property
    def natural_key(self) -> list:
        """
        Get this tables natural key
        """
        return self.__natural_key

    @natural_key.setter
    def natural_key(self, value: list):
        self.__natural_key_override = True
        nk = list()
        for colname in value:
            k = self.get_column_name(colname)
            nk.append(k)
        self.__natural_key = nk
        self.ensure_nk_lookup()

    def _get_nk_lookup_name(self):
        if self.__natural_key_override:
            return self.NK_LOOKUP
        else:
            return self.PK_LOOKUP

    def get_nk_lookup_name(self):
        self.ensure_nk_lookup()
        return self._get_nk_lookup_name()

    def ensure_nk_lookup(self):
        nk_lookup_name = self._get_nk_lookup_name()
        if nk_lookup_name not in self.lookups:
            if self.natural_key:
                self.define_lookup(nk_lookup_name, self.natural_key)

    def get_nk_lookup(self) -> Lookup:
        self.ensure_nk_lookup()
        nk_lookup_name = self._get_nk_lookup_name()
        return self.get_lookup(nk_lookup_name)

    def get_natural_key_value_list(self, row: Row) -> list:
        if self.natural_key is None:
            return self.get_primary_key_value_list(row)
        else:
            natural_key_values = [row[k] for k in self.natural_key]
            return natural_key_values

    def get_natural_key_tuple(self, row) -> tuple:
        if self.natural_key is None:
            return self.get_primary_key_value_tuple(row)
        else:
            return self.get_nk_lookup().get_hashable_combined_key(row)
            # # We need to make sure to rstrip any string values to that it matches what Lookup uses
            # return tuple([Lookup.rstrip_key_value(row[k]) for k in self.natural_key])

    def get_by_key(self,
                   source_row: Row,
                   stats_id: str = 'get_by_key',
                   parent_stats: Statistics = None, ) -> Row:
        """
        Get by the primary key.
        """
        if not isinstance(source_row, Row):
            if isinstance(source_row, list):
                source_row = self.Row(zip(self.primary_key, source_row))
            elif isinstance(source_row, dict):
                source_row = self.Row(source_row)
            else:
                source_row = self.Row(zip(self.primary_key, [source_row]))
        return self.get_by_lookup(ReadOnlyTable.PK_LOOKUP,
                                  source_row,
                                  stats_id=stats_id,
                                  parent_stats=parent_stats)

    def get_by_lookup(self,
                      lookup_name: str,
                      source_row: Row,
                      stats_id: str = 'get_by_lookup',
                      parent_stats: typing.Optional[Statistics] = None,
                      fallback_to_db: bool = False,
                      ) -> Row:

        if lookup_name is None:
            lookup_name = ReadOnlyTable.PK_LOOKUP

        fallback_to_db = fallback_to_db or self.always_fallback_to_db or not self.cache_clean

        return super().get_by_lookup(
            lookup_name=lookup_name,
            source_row=source_row,
            stats_id=stats_id,
            parent_stats=parent_stats,
            fallback_to_db=fallback_to_db,
        )
