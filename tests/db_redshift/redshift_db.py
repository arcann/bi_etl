import importlib
import subprocess
import sys
import unittest

import sqlalchemy

from tests.config_for_tests import EnvironmentSpecificConfigForTests
from tests.db_sqlite.sqlite_db import SqliteDB


class RedshiftDB(SqliteDB):
    SUPPORTS_DECIMAL = True
    SUPPORTS_TIME = True
    SUPPORTS_INTERVAL = False
    SUPPORTS_BINARY = False  # VARBYTE exists but not in SQLAlchemy
    MAX_NAME_LEN = 63

    def __init__(self):
        super().__init__()
        try:
            self.config = EnvironmentSpecificConfigForTests()
        except Exception as e:
            raise unittest.SkipTest(f"tests_config.ini error {e}")

        try:
            if self.config.test_setup is not None:
                if self.config.test_setup.libraries_to_install is not None:
                    for lib_name in self.config.test_setup.libraries_to_install:
                        package_name = lib_name.replace('-', '_')
                        if '[' in package_name:
                            package_name, _ = package_name.split('[', maxsplit=1)
                        if '=' in package_name:
                            package_name, _ = package_name.split('=', maxsplit=1)
                        try:
                            importlib.import_module(package_name)
                            print(f"libraries_to_install {lib_name} package = {package_name} import OK")
                        except ImportError as e:
                            print(f"libraries_to_install {lib_name} import {package_name} got {e} so installing it")
                            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib_name])

                        # if lib_name == 'sqlalchemy-redshift':
                        #     dialect = 'redshift'

                    if 'redshift' in self.config.redshift_database.dialect:
                        sa_version_parts = [int(x) for x in sqlalchemy.__version__.split('.')]
                        if sa_version_parts[0] >= 2:
                            import sqlalchemy_redshift
                            sa_rs_version_parts = [int(x) for x in sqlalchemy_redshift.__version__.split('.')]
                            # Note: We know 0.8.14 does not support SQLAlchemy 2.0. Only guessing that 0.9 might support it.
                            if sa_rs_version_parts[0] == 0 and sa_version_parts[1] <= 8:
                                raise unittest.SkipTest(
                                    f"Skip {RedshiftDB} since sqlalchemy-redshift {sqlalchemy_redshift.__version__} "
                                    f"does not support sqlalchemy {sqlalchemy.__version__}"
                                )

            if self.config.redshift_database is None:
                raise unittest.SkipTest(f"Skip {RedshiftDB} due to no redshift_database section")
            if self.config.s3_bulk is None:
                raise unittest.SkipTest(f"Skip {RedshiftDB} due to no s3_bulk section")
        except FileNotFoundError as e:
            raise unittest.SkipTest(f"Skip {RedshiftDB} due to not finding config {e}")
        except ImportError as e:
            raise unittest.SkipTest(f"Skip {RedshiftDB} due to not finding required module {e}")

    @property
    def BINARY(self):
        raise NotImplemented("VARBYTE exists but not in SQLAlchemy")

    def get_url(self):
        return self.config.redshift_database.get_uri()

    def shutdown(self):
        pass

    def create_engine(self):
        return self.config.redshift_database.get_engine()
