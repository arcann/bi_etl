from tests.db_sqlite.sqlite_db import SqliteDB
from tests.db_base_tests.base_test_hst_table_source_based import BaseTestHistoryTableSourceBased


class TestHistoryTableSourceBasedSqlite(BaseTestHistoryTableSourceBased):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.db_container = SqliteDB()


del BaseTestHistoryTableSourceBased
