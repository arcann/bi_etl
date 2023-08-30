from tests.db_base_tests.base_test_table import BaseTestTable
from tests.db_oracle.oracle_docker_db import OracleDockerDB


class TestTableOracle(BaseTestTable):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = OracleDockerDB()


del BaseTestTable
