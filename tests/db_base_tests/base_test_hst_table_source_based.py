"""
Created on Jan 27, 2016
"""
from unittest import TestSuite

from bi_etl.components.hst_table_source_based import HistoryTableSourceBased
from tests.db_base_tests.base_test_hst_table import BaseTestHstTable, BeginDateSource


def load_tests(loader, standard_tests, pattern):
    # Filter out all
    suite = TestSuite()
    return suite


class BaseTestHistoryTableSourceBased(BaseTestHstTable):
    TABLE_PREFIX = 'hstsrc_'
    TEST_COMPONENT = HistoryTableSourceBased

    # inherit tests from BaseTestHstTable and BaseTestDatabase

    def setUp(self):
        super().setUp()
        self.test_file_search_folders.append('test_hstsrc_table_data')

    def _testInsertAndUpsert(
            self,
            load_cache: bool,
            tbl_name: str,
            use_type1: bool,
            use_type2: bool,
            check_for_deletes: bool,
            begin_date_source: BeginDateSource = None,
    ):
        # Only IN_ROW is supported for HistoryTableSourceBased
        if begin_date_source is None:
            begin_date_source = BeginDateSource.IN_ROW
        if begin_date_source != BeginDateSource.IN_ROW:
            self.log.warning(f"Only IN_ROW is supported for HistoryTableSourceBased. Got {begin_date_source}")

        super()._testInsertAndUpsert(
            load_cache=load_cache,
            tbl_name=tbl_name,
            use_type1=use_type1,
            use_type2=use_type2,
            check_for_deletes=check_for_deletes,
            begin_date_source=BeginDateSource.IN_ROW,
        )

    def _testInsertAndSQLUpsert(
            self,
            tbl_name: str,
            use_type1: bool,
            use_type2: bool,
            check_for_deletes: bool,
    ):
        raise self.skipTest("Not ready yet")
