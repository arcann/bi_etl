import sqlalchemy
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, TEXT
from sqlalchemy.sql.sqltypes import NUMERIC
from sqlalchemy.sql.sqltypes import REAL

from bi_etl.bulk_loaders.postgresql_bulk_load_config import PostgreSQLBulkLoaderConfig
from bi_etl.bulk_loaders.postgresql_copy import PostgreSQLCopy
from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.table import Table
from tests.db_base_tests.base_test_table import BaseTestTable
from tests.db_postgres.postgres_docker_db import PostgresDockerDB


class TestTablePostgres(BaseTestTable):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = PostgresDockerDB()

    @staticmethod
    def _generate_bulk_test_row(
            i: int,
            tbl: Table,
            iteration_header: RowIterationHeader
    ) -> Row:
        row = tbl.Row(iteration_header=iteration_header)
        row['col1'] = i
        row['col2'] = f'this is row {i}'
        row['col3'] = i / 1000.0
        row['col4'] = i / 100000000.0
        if i % 2 == 0:
            row['col5'] = f'this is row {i}'
        else:
            row['col5'] = None
        return row

    def _testBulkInsertAndIterateNoKey(self, tbl_name: str, bulk_config: PostgreSQLBulkLoaderConfig):
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._text_datatype()),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', TEXT),
        )
        sa_table.create()

        rows_to_insert = 10
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            bulk_loader = PostgreSQLCopy(config=bulk_config)
            tbl.set_bulk_loader(bulk_loader)
            iteration_header = RowIterationHeader()
            for i in range(rows_to_insert):
                row = TestTablePostgres._generate_bulk_test_row(
                    i,
                    tbl,
                    iteration_header
                )

                tbl.insert_row(row)

            tbl.bulk_load_from_cache()

            # Validate data
            rows_dict = dict()
            for row in tbl:
                print(row.values())
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), rows_to_insert)

            for i in range(rows_to_insert):
                expected_row = TestTablePostgres._generate_bulk_test_row(
                    i,
                    tbl,
                    iteration_header
                )
                row = rows_dict[i]
                self._compare_rows(
                    expected_row=expected_row,
                    actual_row=row,
                )

    def testBulkInsert_DefaultConfig(self):
        tbl_name = self._get_table_name('testBulkInsertAndIterateNoKey')
        bulk_config = PostgreSQLBulkLoaderConfig(
        )
        self._testBulkInsertAndIterateNoKey(tbl_name, bulk_config)

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
                    self._testBulkInsertAndIterateNoKey(tbl_name, bulk_config)
