from datetime import datetime, date

from tests.db_base_tests.base_test_sql_query import BaseTestSQLQuery
from tests.db_oracle.oracle_docker_db import OracleDockerDB


class TestSQLQueryOracle(BaseTestSQLQuery):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_container = OracleDockerDB()

    def _sql_query_date_conv(self, dt_val: datetime):
        if isinstance(dt_val, date):
            return datetime(
                year=dt_val.year,
                month=dt_val.month,
                day=dt_val.day,
            )
        else:
            return dt_val


del BaseTestSQLQuery
