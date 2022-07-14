from tests.db_base_tests.test_sql_query import _TestSQLQuery
from tests.db_sqlite.sqlite_db import SqliteDB


class TestSQLQuerySqlite(_TestSQLQuery):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = SqliteDB()

    def _sql_query_date_conv(self, dt_val):
        return str(dt_val)


