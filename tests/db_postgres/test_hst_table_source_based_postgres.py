from tests.db_postgres.postgres_docker import PostgresTestDB
from tests.db_base_tests.test_hst_table_source_based import _TestHistoryTableSourceBased


class TestHistoryTableSourceBasedPostgres(_TestHistoryTableSourceBased):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()

