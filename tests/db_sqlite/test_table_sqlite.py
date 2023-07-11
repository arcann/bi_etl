from tests.db_sqlite.sqlite_db import SqliteDB
from tests.db_base_tests.base_test_table import BaseTestTable


class TestTableSqlite(BaseTestTable):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.db_container = SqliteDB()


del BaseTestTable
