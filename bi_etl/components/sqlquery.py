"""
Created on Sep 17, 2014

@author: Derek Wood
"""
import typing
from enum import IntEnum, unique

import sqlalchemy

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.database import DatabaseMetadata
from bi_etl.scheduler.task import ETLTask


class SQLQuery(ETLComponent):
    """
    A class for reading an arbitrary SQL statement.
    Consider using sqlalchemy.sql.text to wrap the SQL.
    http://docs.sqlalchemy.org/en/latest/core/tutorial.html#using-text
    
    
    """
    @unique
    class ParamType(IntEnum):
        """
        Row status values
        """
        bind = 1
        format = 2

    def __init__(self,
                 task: typing.Optional[ETLTask],
                 database: DatabaseMetadata,
                 sql: str,
                 logical_name: typing.Optional[str] = None,
                 **kwargs
                 ):
        # Don't pass kwargs up. They should be set here at the end
        super(SQLQuery, self).__init__(task=task,
                                       logical_name=logical_name
                                       )
        
        self.engine = database.bind
        self.sql = sql
        self.param_mode = SQLQuery.ParamType.bind
        self._first_row = None
        
        # Should be the last call of every init
        self.set_kwattrs(**kwargs) 

    def __repr__(self):
        return f"SQLQuery({self.logical_name or id(self)})"
    
    def __str__(self):
        return repr(self)

    def _raw_rows(self):
        """
        Run the SQL as is with no parameters or substitutions.
        """
        if self.param_mode == SQLQuery.ParamType.bind:
            select_result = self._raw_rows_bind_parameters()
        else:
            select_result = self._raw_rows_format_parameters()
        return select_result
    
    def _obtain_column_names(self):
        # Column_names can be slow to obtain
        # We might even error out if the query requires parameters
        # So just raise an error
        raise NotImplementedError()

    def _raw_rows_bind_parameters(self, **parameters):
        """
        Run the SQL providing optional bind parameters. (:param in the SQL)
        """
        stats = self.get_stats_entry(stats_id=self.default_stats_id)
        stats.timer.start()
        try:
            sql = sqlalchemy.text(self.sql)

            with self.engine.connect() as conn:
                select_result = conn.execute(sql, **parameters)
                self.column_names = list(select_result.keys())
                for row in select_result:
                    yield row
        except TypeError as e:
            raise TypeError(f'Error {e} with SQL {self.sql} and params {parameters} on {self.engine}')

    def _raw_rows_format_parameters(self, *args, **kwargs):
        """
        Uses Python string formatting like {} or {name} to build a SQL string.
        Can be used to dynamically change the structure of the SQL, compared to bind variables which are more limited but faster.
        """
        stats = self.get_stats_entry(stats_id=self.default_stats_id)
        stats.timer.start()
        select = self.sql.format(*args, **kwargs)
        with self.engine.connect() as conn:
            select_result = conn.execute(select)
            self.column_names = list(select_result.keys())
            for row in select_result:
                yield row
