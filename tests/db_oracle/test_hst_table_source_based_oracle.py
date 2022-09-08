from tests.db_base_tests.base_test_hst_table_source_based import BaseTestHistoryTableSourceBased
from tests.db_oracle.oracle_docker_db import OracleDockerDB


class TestHistoryTableSourceBasedOracle(BaseTestHistoryTableSourceBased):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = OracleDockerDB()

