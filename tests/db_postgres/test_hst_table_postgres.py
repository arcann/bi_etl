from tests.db_postgres.postgres_docker import PostgresTestDB
from tests.db_base_tests.test_hst_table import _TestHstTable


class TestTableSourceBasedPostgres(_TestHstTable):
    SUPPORTS_DECIMAL = True

    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()
