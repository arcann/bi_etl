import unittest

from tests.db_oracle.oracle_docker_db import OracleDockerDB
from tests.db_base_tests.base_test_hst_table import BaseTestHstTable


class TestHstTableOracle(BaseTestHstTable):
    SUPPORTS_DECIMAL = True

    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.db_container = OracleDockerDB()
        except ImportError as e:
            raise unittest.SkipTest(repr(e))


del BaseTestHstTable
