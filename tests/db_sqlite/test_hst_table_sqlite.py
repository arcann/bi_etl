from tests.db_sqlite.sqlite_db import SqliteDB
from tests.db_base_tests.base_test_hst_table import BaseTestHstTable


class TestHstTableSqlite(BaseTestHstTable):
    SUPPORTS_DECIMAL = False

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.db_container = SqliteDB()

    def test_sql_upsert_nosrgt_del(self):
        super().test_sql_upsert_nosrgt_del()


del BaseTestHstTable
