from bi_etl.tests.postgres.postgres_docker import PostgresTestDB
from bi_etl.tests.test_hst_table_source_based import TestHistoryTableSourceBased


class TestHistoryTableSourceBasedPostgres(TestHistoryTableSourceBased):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()
