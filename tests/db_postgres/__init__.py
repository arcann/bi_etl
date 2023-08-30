# https://docs.python.org/3/library/unittest.html#load-tests-protocol
from unittest import TestSuite


def load_tests(loader, standard_tests, pattern):
    suite = TestSuite()
    from tests.db_postgres.test_table_postgres import TestTablePostgres
    from tests.db_postgres.test_hst_table_postgres import TestHstTablePostgres
    from tests.db_postgres.test_sql_query_postgres import TestSQLQueryPostgres
    from tests.db_postgres.test_hst_table_source_based_postgres import TestHistoryTableSourceBasedPostgres
    for test_class in (
            TestTablePostgres,
            TestSQLQueryPostgres,
            TestHstTablePostgres,
            TestHistoryTableSourceBasedPostgres
    ):
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
