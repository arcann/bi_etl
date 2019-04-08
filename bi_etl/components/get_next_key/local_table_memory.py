from bi_etl.components.get_next_key.base_table_memory import BaseTableMemory


class LocalTableMemory(BaseTableMemory):
    def __init__(self, table):
        super().__init__(table=table)
        self.current_key_values = dict()

    def get_next_key(self, column: str) -> int:
        column_obj = self.table.get_column(column)
        column = column_obj.name
        current_max = self.current_key_values.get(column)
        if current_max is None:
            next_key = self.get_next_from_database(column_obj)
        else:
            next_key = current_max + 1
        self.current_key_values[column] = next_key
        return next_key
