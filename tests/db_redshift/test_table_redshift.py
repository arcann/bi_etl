import unittest

import sqlalchemy
from config_wrangler.config_templates.password_source import PasswordSource
from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer

from bi_etl.bulk_loaders.redshift_s3_csv_loader import RedShiftS3CSVBulk
from bi_etl.components.table import Table
from tests.config_for_tests import EnvironmentSpecificConfigForTests
from tests.db_base_tests.base_test_table import BaseTestTable
from tests.db_redshift.redshift_db import RedshiftDB


class TestTableRedshift(BaseTestTable):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.db_container = RedshiftDB()
        try:
            cls.env_config = EnvironmentSpecificConfigForTests()
        except ValueError as e:
            raise unittest.SkipTest(f"Skip {cls} due to config error {e}")
        except FileNotFoundError as e:
            raise unittest.SkipTest(f"Skip {cls} due to not finding config {e}")

    def setUp(self):
        super().setUp()
        self.test_file_search_folders.append('test_files')

    def _get_table_name(self, partial_name: str) -> str:
        # Redshift table names are case-insensitive.
        # Sqlalchemy way to handle that is to provide names in lower-case
        return super()._get_table_name(partial_name=partial_name).lower()

    def testInsertDuplicate(self):
        raise unittest.SkipTest(f"Skip testInsertDuplicate due to no Redshift support")

    def testRedShiftS3CSVBulk_Insert_DefaultConfig(self):
        tbl_name = self._get_table_name('testBulkInsertAndIterateNoKey')
        bulk_loader = RedShiftS3CSVBulk(self.env_config.s3_bulk)
        self._testBulkInsertAndIterateNoKey(tbl_name, bulk_loader)

    def testRedShiftS3CSVBulk_Insert_Various(self):
        for delimiter in (',', '\t', '|'):
            for header in (True, False):
                for null_value in ('', '-NULL-'):
                    print(f"Testing delimiter '{delimiter}' header {header} null_value '{null_value}'")
                    tbl_name = self._get_table_name(
                        f"testBulkInsert{hash(delimiter)}{header}{hash(null_value)}"
                    )
                    bulk_loader = RedShiftS3CSVBulk(
                        config=self.env_config.s3_bulk,
                        s3_file_delimiter=delimiter,
                        has_header=header,
                        null_value=null_value,
                    )
                    self._testBulkInsertAndIterateNoKey(tbl_name, bulk_loader)

    def testRedShiftS3CSVBulk_Error_Handling_datatype(self):
        tbl_name = self._get_table_name('testRedShiftS3CSVBulkErrorHandlingDT')

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        test_file_path = self.get_test_file_path('bad_csv_bulk.csv')
        bulk_loader = RedShiftS3CSVBulk(self.env_config.s3_bulk, s3_file_delimiter=',')
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:

            with self.assertRaisesRegex(Exception, r"(?i)(integer|digit)"):
                bulk_loader.load_from_files(
                    local_files=[test_file_path],
                    table_object=tbl,
                )

    def testRedShiftS3CSVBulk_Error_Handling_delimiter(self):
        tbl_name = self._get_table_name('testRedShiftS3CSVBulkErrorHandlingDelimiter')

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        test_file_path = self.get_test_file_path('bad_csv_bulk.csv')
        bulk_loader = RedShiftS3CSVBulk(self.env_config.s3_bulk, s3_file_delimiter='|')
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:

            with self.assertRaisesRegex(Exception, r"(?i)(delimiter)") as e:
                bulk_loader.load_from_files(
                    local_files=[test_file_path],
                    table_object=tbl,
                )
            self.assertNotIn(bulk_loader.s3_password, str(e.exception))

    def testRedShiftS3CSVBulk_Error_Handling_Connection(self):
        tbl_name = self._get_table_name('testRedShiftS3CSVBulkErrorHandlingConn')

        temp_db_meta = self._get_mock_db()

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            temp_db_meta,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
        )
        sa_table.create(bind=temp_db_meta.bind)

        self.print_ddl(sa_table)

        test_file_path = self.get_test_file_path('bad_csv_bulk.csv')

        bulk_loader = RedShiftS3CSVBulk(self.env_config.s3_bulk)
        # Note: by breaking s3_user_id the upload will work (uses bulk_loader.bucket),
        #       but the COPY will fail.
        bulk_loader.s3_user_id = 'BAD'
        with Table(self.task,
                   self._get_mock_db(),
                   table_name=tbl_name) as tbl:

            with self.assertRaisesRegex(Exception, r"(?i)(InvalidAccessKeyId)") as e:
                bulk_loader.load_from_files(
                    local_files=[test_file_path],
                    table_object=tbl,
                )
            self.assertNotIn(bulk_loader.s3_password, str(e.exception))

    def testRedShiftS3CSVBulk_Error_Handling_Connection2(self):
        tbl_name = self._get_table_name('testRedShiftS3CSVBulkErrorHandlingConn2')

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        test_file_path = self.get_test_file_path('bad_csv_bulk.csv')

        bulk_loader = RedShiftS3CSVBulk(self.env_config.s3_bulk)
        # Note: by breaking s3_password the upload will work (uses bulk_loader.bucket),
        #       but the COPY will fail.
        bulk_loader.config.raw_password = 'BAD'
        bulk_loader.config.password_source = PasswordSource.CONFIG_FILE
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:

            with self.assertRaisesRegex(Exception, r"(?i)(SignatureDoesNotMatch)") as e:
                bulk_loader.load_from_files(
                    local_files=[test_file_path],
                    table_object=tbl,
                )
            self.assertNotIn(bulk_loader.s3_password, str(e.exception))


del BaseTestTable
