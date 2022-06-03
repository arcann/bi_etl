from tests.postgres.postgres_docker import PostgresTestDB
from tests.test_hst_table_source_based import TestHistoryTableSourceBased


class TestHistoryTableSourceBasedPostgres(TestHistoryTableSourceBased):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()


# don't test TestHistoryTableSourceBased here
del TestHistoryTableSourceBased
