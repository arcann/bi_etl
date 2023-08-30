# https://docs.python.org/3/library/unittest.html#load-tests-protocol
from unittest import TestSuite


def load_tests(loader, standard_tests, pattern):
    suite = TestSuite()
    from tests.db_redshift.test_table_redshift import TestTableRedshift
    # from tests.db_redshift.test_hst_table_redshift import TestHstTableRedshift
    # from tests.db_redshift.test_sql_query_redshift import TestSQLQuerySqliteRedshift
    # from tests.db_redshift.test_hst_table_source_based_redshift import TestHistoryTableSourceBasedRedshift
    for test_class in (
            TestTableRedshift,
            # TestSQLQuerySqliteRedshift,
            # TestHstTableRedshift,
            # TestHistoryTableSourceBasedRedshift
    ):
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
