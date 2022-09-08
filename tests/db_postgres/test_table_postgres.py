from tests.db_postgres.postgres_docker_db import PostgresDockerDB
from tests.db_base_tests.base_test_table import BaseTestTable


class TestTablePostgres(BaseTestTable):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresDockerDB()
