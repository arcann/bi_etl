# https://docs.python.org/3/library/unittest.html#load-tests-protocol
from unittest import TestSuite


def load_tests(loader, standard_tests, pattern):
    suite = TestSuite()
    from tests.db_sqlite.test_table_sqlite import TestTableSqlite
    from tests.db_sqlite.test_hst_table_sqlite import TestHstTableSqlite
    from tests.db_sqlite.test_sql_query_sqlite import TestSQLQuerySqlite
    from tests.db_sqlite.test_hst_table_source_based_sqlite import TestHistoryTableSourceBasedSqlite
    for test_class in (
            TestTableSqlite,
            TestSQLQuerySqlite,
            TestHstTableSqlite,
            TestHistoryTableSourceBasedSqlite
    ):
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite
