from tests.db_base_tests.base_test_sql_query import BaseTestSQLQuery


class TestSQLQuerySqlite(BaseTestSQLQuery):
    def _sql_query_date_conv(self, dt_val):
        return str(dt_val)

del BaseTestSQLQuery
