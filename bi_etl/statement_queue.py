"""
Created on Mar 2, 2015

@author: woodd
"""


class StatementQueue(object):
    """
    A queue of pending SQLAlchemyy statements
    """

    def __init__(self):
        """
        Constructor
        """
        self.statements = dict()
        self.statement_values = dict()
        self.row_count = 0
        
    def __len__(self):
        return self.row_count
    
    def get_statement_by_key(self, key):
        return self.statements.get(key)
    
    def add_statement(self, key, stmt):
        self.statements[key] = stmt
    
    def execute(self, connection):
        rows_affected = 0
        if self.row_count > 0:
            for stmtKey in self.statements.keys():
                stmt = self.statements[stmtKey]
                values = self.statement_values[stmtKey]
                result = connection.execute(stmt, values)
                rows_affected = result.rowcount
            self.statements.clear()
            self.row_count = 0
        return rows_affected
    
    def iter_single_statements(self):
        if self.row_count > 0:
            for stmtKey in self.statements.keys():
                stmt = self.statements[stmtKey]
                values = self.statement_values[stmtKey]
                for row in values:
                    yield (stmt, row)
        
    def append_values_by_key(self, key, values):
        values_list = self.statement_values.get(key)
        if values_list is None:
            values_list = list()
            self.statement_values[key] = values_list
        values_list.append(values)
        self.row_count += 1    
