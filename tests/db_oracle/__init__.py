# https://docs.python.org/3/library/unittest.html#load-tests-protocol
from unittest import TestSuite


def load_tests(loader, standard_tests, pattern):
    suite = TestSuite()
    from tests.db_oracle.test_table_oracle import TestTableOracle
    from tests.db_oracle.test_hst_table_oracle import TestHstTableOracle
    from tests.db_oracle.test_sql_query_oracle import TestSQLQueryOracle
    from tests.db_oracle.test_hst_table_source_based_oracle import TestHistoryTableSourceBasedOracle
    for test_class in (
            TestTableOracle,
            TestSQLQueryOracle,
            TestHstTableOracle,
            TestHistoryTableSourceBasedOracle
    ):
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
