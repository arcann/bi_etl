from tests.postgres.postgres_docker import PostgresTestDB
from tests.test_hst_table import TestHstTable


class TestTableSourceBasedPostgres(TestHstTable):
    SUPPORTS_DECIMAL = True

    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()
