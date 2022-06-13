from tests.db_postgres.postgres_docker import PostgresTestDB
from tests.db_base_tests.test_table import _TestTable


class TestTablePostgres(_TestTable):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()
