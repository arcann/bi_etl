from tests.db_base_tests.test_hst_table import _TestHstTable


class TestTableSourceBasedSqlite(_TestHstTable):
    SUPPORTS_DECIMAL = False
