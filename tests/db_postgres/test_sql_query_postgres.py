from tests.db_base_tests.test_sql_query import _TestSQLQuery
from tests.db_postgres.postgres_docker import PostgresTestDB


class TestSQLQuerySqlitePostgres(_TestSQLQuery):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()
