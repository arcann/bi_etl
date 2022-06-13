from tests.db_base_tests.test_table import _TestTable
from tests.db_sqlite.sqlite_db import SqliteDB


class TestTableSqlite(_TestTable):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = SqliteDB()
