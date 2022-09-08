from tests.db_base_tests.base_test_hst_table import BaseTestHstTable


class TestHstTableSqlite(BaseTestHstTable):
    SUPPORTS_DECIMAL = False

del BaseTestHstTable
