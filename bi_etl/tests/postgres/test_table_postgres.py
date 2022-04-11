from bi_etl.tests.postgres.postgres_docker import PostgresTestDB
from bi_etl.tests.test_table import TestTable


class TestTableSourceBasedPostgres(TestTable):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()
