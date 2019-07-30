import multiprocessing

from bi_etl.components.get_next_key.shared_table_memory import SharedTableMemory


def main():
    pass


if __name__ == '__main__':
    main()


class SharedTableMemoryManager(object):
    def __init__(self, manager):
        self.table_dict = manager.dict()

    def create_shared_table_memory(self, manager: multiprocessing.Manager, table_name: str, chunk_size: int):
        table_name = str(table_name)
        if table_name not in self.table_dict:
            self.table_dict[table_name] = SharedTableMemory(manager, chunk_size=chunk_size)
        return self.table_dict[table_name]

    def get_shared_table_memory(self, table_name):
        return self.table_dict[table_name]
