from tests.db_base_tests.base_test_sql_query import BaseTestSQLQuery
from tests.db_postgres.postgres_docker_db import PostgresDockerDB


class TestSQLQueryPostgres(BaseTestSQLQuery):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresDockerDB()

del BaseTestSQLQuery
