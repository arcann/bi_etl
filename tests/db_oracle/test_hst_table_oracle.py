from tests.db_oracle.oracle_docker_db import OracleDockerDB
from tests.db_base_tests.base_test_hst_table import BaseTestHstTable


class TestHstTableOracle(BaseTestHstTable):
    SUPPORTS_DECIMAL = True

    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = OracleDockerDB()


del BaseTestHstTable
