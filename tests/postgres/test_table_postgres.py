from tests.postgres.postgres_docker import PostgresTestDB
from tests.test_table import TestTable


class TestTableSourceBasedPostgres(TestTable):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresTestDB()


# don't test TestTable here
del TestTable
