import importlib
import subprocess
import sys
import unittest

from bulk_loaders.redshift_s3_csv_loader import RedShiftS3CSVBulk
from config_for_tests import EnvironmentSpecificConfigForTests
from db_redshift.redshift_db import RedshiftDB
from tests.db_base_tests.base_test_table import BaseTestTable


class TestTableRedshift(BaseTestTable):
    env_config: EnvironmentSpecificConfigForTests

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        try:
            cls.env_config = EnvironmentSpecificConfigForTests()
            if cls.env_config.test_setup is not None:
                if cls.env_config.test_setup.libraries_to_install is not None:
                    for lib_name in cls.env_config.test_setup.libraries_to_install:
                        package_name = lib_name.replace('-', '_')
                        try:
                            importlib.import_module(package_name)
                        except ImportError as e:
                            print(f"{lib_name} import {package_name} got {e} so installing it")
                            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib_name])

            if cls.env_config.redshift_database is None:
                raise unittest.SkipTest(f"Skip {cls} due to no redshift_database section")
            if cls.env_config.s3_bulk is None:
                raise unittest.SkipTest(f"Skip {cls} due to no s3_bulk section")
            # For this test class db_container will be instance level
            cls.db_container = RedshiftDB(cls.env_config.redshift_database)
        except FileNotFoundError as e:
            raise unittest.SkipTest(f"Skip {cls} due to not finding config {e}")
        except ImportError as e:
            raise unittest.SkipTest(f"Skip {cls} due to not finding required module {e}")

    def setUp(self):
        super().setUp()

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
