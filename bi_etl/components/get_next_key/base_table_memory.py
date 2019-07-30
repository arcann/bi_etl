import logging

from sqlalchemy import Column


class BaseTableMemory(object):
    def __init__(self, table):
        self.table = table
        self.log = logging.getLogger(f"{self.__class__.__name__}.{table}")

    def get_next_from_database(self, column_obj: Column) -> int:
        current_max = self.table.max(column_obj)
        # In case the database call returns None
        if current_max is None:
            next_key = 0
        else:
            # Make sure max is an integer
            next_key = int(current_max)
        # Check for negative (special values) set max to 0
        if next_key <= 0:
            next_key = 1
            msg = "(and not negative value)"
        else:
            msg = ''
            next_key = current_max + 1
        self.log.info(f"Initialize sequence for {column_obj} with value {next_key} {msg}")
        return next_key
