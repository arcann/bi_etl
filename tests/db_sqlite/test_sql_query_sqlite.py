from tests.db_sqlite.sqlite_db import SqliteDB
from tests.db_base_tests.base_test_sql_query import BaseTestSQLQuery


class TestSQLQuerySqlite(BaseTestSQLQuery):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.db_container = SqliteDB()

    def _sql_query_date_conv(self, dt_val):
        return str(dt_val)


del BaseTestSQLQuery
