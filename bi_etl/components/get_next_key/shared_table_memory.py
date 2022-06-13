from bi_etl.components.get_next_key.base_table_memory import BaseTableMemory


class SharedTableMemory(BaseTableMemory):
    def __init__(self, manager, chunk_size: int):
        # Table will need to be set on local process before use
        super().__init__(table=None)
        self.chunk_size = chunk_size
        self.lock = manager.Lock()
        self.current_key_values = manager.dict()
        # These need to be None on init because init is done on main process
        self._local_current_keys = None
        self._local_max_allocated_keys = None
        self.log.debug(f"SharedTableMemory chunk_size= {chunk_size}")

    def get_key_from_shared(self, column: str) -> int:
        column_obj = self.table.get_column(column)
        column = column_obj.name
        with self.lock:
            current_max = self.current_key_values.get(column)
            if current_max is None:
                next_key = self.get_next_from_database(column_obj)
            else:
                next_key = current_max + 1
            local_max_allocated = next_key + self.chunk_size
            self.current_key_values[column] = local_max_allocated
            self._local_max_allocated_keys[column] = local_max_allocated
        return next_key

    def get_next_key(self, column: str) -> int:
        column_obj = self.table.get_column(column)
        column = column_obj.name
        if self._local_current_keys is None:
            self._local_current_keys = dict()
            self._local_max_allocated_keys = dict()
        current_max = self._local_current_keys.get(column)
        if current_max is None:
            next_key = self.get_key_from_shared(column)
        else:
            local_max_allocated = self._local_max_allocated_keys.get(column)
            if current_max >= local_max_allocated:
                # defer to parent to get max
                next_key = self.get_key_from_shared(column)
            else:
                next_key = current_max + 1
        self._local_current_keys[column] = next_key
        return next_key
