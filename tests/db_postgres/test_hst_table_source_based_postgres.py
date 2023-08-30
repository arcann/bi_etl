from tests.db_postgres.postgres_docker_db import PostgresDockerDB
from tests.db_base_tests.base_test_hst_table_source_based import BaseTestHistoryTableSourceBased


class TestHistoryTableSourceBasedPostgres(BaseTestHistoryTableSourceBased):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresDockerDB()


del BaseTestHistoryTableSourceBased
