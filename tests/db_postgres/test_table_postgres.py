from bi_etl.bulk_loaders.postgresql_bulk_load_config import PostgreSQLBulkLoaderConfig
from bi_etl.bulk_loaders.postgresql_copy import PostgreSQLCopy
from tests.db_base_tests.base_test_table import BaseTestTable
from tests.db_postgres.postgres_docker_db import PostgresDockerDB


class TestTablePostgres(BaseTestTable):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.db_container = PostgresDockerDB()

    def testBulkInsert_DefaultConfig(self):
        tbl_name = self._get_table_name('testBulkInsertAndIterateNoKey')
        bulk_config = PostgreSQLBulkLoaderConfig()
        bulk_loader = PostgreSQLCopy(config=bulk_config)
        self._testBulkInsertAndIterateNoKey(tbl_name, bulk_loader)

    def testBulkInsertVarious(self):
        for delimiter in (',', '\t', '|'):
            for header in (True, False):
                for null in ('', '-NULL-'):
                    print(f"Testing delimiter '{delimiter}' header {header} null '{null}'")
                    tbl_name = self._get_table_name(
                        f"testBulkInsert{hash(delimiter)}{header}{hash(null)}"
                    )
                    bulk_config = PostgreSQLBulkLoaderConfig(
                        delimiter=delimiter,
                        header=header,
                        null=null,
                    )
                    bulk_loader = PostgreSQLCopy(config=bulk_config)
                    self._testBulkInsertAndIterateNoKey(tbl_name, bulk_loader)


del BaseTestTable
