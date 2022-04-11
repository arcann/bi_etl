from bi_etl.tests.postgres.postgres_docker import PostgresTestDB
from bi_etl.tests.test_hst_table import TestHstTable


class TestTableSourceBasedPostgres(TestHstTable):
    SUPPORTS_DECIMAL = True

    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()
