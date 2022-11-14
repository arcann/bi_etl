"""
Created on Mar 2, 2015

@author: Derek Wood
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Mapping, Tuple

import sqlalchemy

from bi_etl.components.row.row import Row


class StatementQueue(object):
    """
    A queue of pending SQLAlchemyy statements
    """

    def __init__(self, execute_with_binds=True):
        """
        Constructor
        """
        self.statements: Dict[Any, sqlalchemy.sql.base.Executable] = dict()
        self.statement_values: Dict[Any, List[Mapping]] = dict()
        self.row_count: int = 0
        self.execute_with_binds: bool = execute_with_binds
        self.row_limit: int = 1000
        # Batch size = 	65,536 * Network Packet Size
        # Network Packet Size is the size of the tabular data stream (TDS) packets used to communicate between
        # applications and the relational Database Engine. The default packet size is 4 KB, and is controlled by the
        # network packet size configuration option.
        # We set the size soft limit as below this because
        # 1) It's a soft limit, we might go higher
        # 2) It doesn't count the INSERT INTO clause part (e.g. INSERT INTO perf_test (c1,c2,dt,i1,f1,d1) VALUES )
        self.size_soft_limit = 60000 * 4096
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
    def __len__(self):
        return self.row_count
    
    def get_statement_by_key(self, key):
        return self.statements.get(key)
    
    def add_statement(self, key, stmt):
        self.statements[key] = stmt

    @staticmethod
    def encapsulate_value(value) -> str:
        # Encapsulate the input for SQL use (add ' etc)
        if isinstance(value, str):
            return "'" + value.replace("'", "''") + "'"
        # Note we need to check datetime before date because a date passes both isinstance
        elif isinstance(value, datetime):
            if value.microsecond == 0:
                return "'" + value.isoformat() + "'"
            else:
                return f"'{value:%Y-%m-%d %H:%M:%S}.{int(value.microsecond / 1000)}{value:%z}'"
        elif isinstance(value, date):
            return "'" + value.isoformat() + "'"
        elif value is None:
            return 'Null'
        else:
            return str(value)

    @staticmethod
    def encapsulate_row_value_list(value_list: list) -> str:
        return ','.join([StatementQueue.encapsulate_value(v) for v in value_list])

    def values_str_list(self, rows, row_limit: int = None, size_soft_limit: int = None):
        if row_limit is None:
            row_limit = self.row_limit
        if size_soft_limit is None:
            size_soft_limit = self.size_soft_limit
        values_str_list = []
        values_str = []
        line_counter = 0
        size = 0
        for i in rows:
            limit_reached = False
            if line_counter >= row_limit:
                limit_reached = True
                self.log.debug(f'insert stmt row limit {row_limit:,} reached')
            elif size_soft_limit is not None and size > size_soft_limit:
                limit_reached = True
                self.log.debug(f'insert stmt size limit {size_soft_limit:,} reached or exceeded with {size:,} for {line_counter:,} lines')
            if limit_reached:
                values_str_list.append(",".join(values_str))
                values_str = []
                line_counter = 0
                size = 0
            row_str = "(" + StatementQueue.encapsulate_row_value_list(i) + ")"
            values_str.append(row_str)
            size += len(row_str) + 1  # One extra for comma separator
            line_counter += 1
        # Add the final list
        values_str_list.append(",".join(values_str))
        return values_str_list

    def execute(self, connection) -> int:
        rows_affected = 0
        if self.row_count > 0:
            for stmtKey in self.statements.keys():
                stmt = self.statements[stmtKey]
                values = self.statement_values[stmtKey]
                if len(values) > 0:
                    if self.execute_with_binds:
                        result = connection.execute(stmt, values)
                        if result.rowcount == -1:
                            rows_affected += len(values)
                        else:
                            rows_affected += result.rowcount
                    else:
                        # cursor = connection.engine.raw_connection().cursor()
                        # for values_str in self.values_str_list(values):
                        #     cursor.execute(stmt.format(values=values_str))
                        #     rows_affected += cursor.rowcount
                        for values_str in self.values_str_list(values):
                            # Treat stmt as a string
                            # noinspection PyUnresolvedReferences
                            result = connection.execute(stmt.format(values=values_str))
                            if result.rowcount == -1:
                                rows_affected += len(values)
                            else:
                                rows_affected += result.rowcount
                self.statement_values[stmtKey].clear()
            self.row_count = 0
        return rows_affected
    
    def iter_single_statements(self) -> Tuple[sqlalchemy.sql.base.Executable, Row]:
        if self.row_count > 0:
            for stmtKey in self.statements.keys():
                stmt = self.statements[stmtKey]
                values = self.statement_values[stmtKey]
                for row in values:
                    yield stmt, row

    def execute_singly(self, connection) -> int:
        rows_affected = 0
        for row_num, (stmt, row) in enumerate(self.iter_single_statements()):
            try:
                if self.execute_with_binds:
                    result = connection.execute(stmt, row)
                    rows_affected += result.rowcount
                else:
                    # cursor = connection.engine.raw_connection().cursor()
                    # for values_str in StatementQueue.values_str_list(row, limit=1):
                    #     cursor.execute(stmt.format(values=values_str))
                    #     rows_affected += cursor.rowcount
                    for values_str in self.values_str_list(rows=[row], row_limit=1):
                        result = connection.execute(stmt.format(values=values_str))
                        rows_affected += result.rowcount
            except Exception as e:
                try:
                    vals = row.str_formatted()
                except AttributeError:
                    vals = row
                msg = f"Error {e} with row {row_num} stmt {stmt} stmt_values {vals}"
                self.log.error(msg)
                try:
                    orig = e.orig
                except AttributeError:
                    orig = None
                raise sqlalchemy.exc.StatementError(msg, str(stmt), vals, orig)
        return rows_affected
        
    def append_values_by_key(self, key, values):
        values_list = self.statement_values.get(key)
        if values_list is None:
            values_list = list()
            self.statement_values[key] = values_list
        values_list.append(values)
        self.row_count += 1    
