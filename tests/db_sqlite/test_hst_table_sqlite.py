from db_sqlite.sqlite_db import SqliteDB
from tests.db_base_tests.base_test_hst_table import BaseTestHstTable


class TestHstTableSqlite(BaseTestHstTable):
    SUPPORTS_DECIMAL = False

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.db_container = SqliteDB()


del BaseTestHstTable
