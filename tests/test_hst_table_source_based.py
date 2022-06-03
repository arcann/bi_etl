"""
Created on Jan 27, 2016
"""
import unittest

from bi_etl.components.hst_table_source_based import HistoryTableSourceBased
from tests.test_hst_table import TestHstTable, BeginDateSource


class TestHistoryTableSourceBased(TestHstTable):
    TABLE_PREFIX = 'hstsrc_'
    TEST_COMPONENT = HistoryTableSourceBased
    TEST_DATA_PATH = 'test_hstsrc_table_data'

    # inherit tests from TestHstTable and _TestBaseDatabase

    def _testInsertAndUpsert(
            self,
            load_cache: bool,
            tbl_name: str,
            use_type1: bool,
            use_type2: bool,
            check_for_deletes: bool,
            begin_date_source: BeginDateSource = BeginDateSource.SYSTEM_TIME,
    ):

        super()._testInsertAndUpsert(
            load_cache=load_cache,
            tbl_name=tbl_name,
            use_type1=use_type1,
            use_type2=use_type2,
            check_for_deletes=check_for_deletes,
            # Only IN_ROW is supported for HistoryTableSourceBased
            # TODO: This will lead to running the same test twice,
            #       but we are not yet ready to change the default to IN_ROW
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


# Don't test TestHstTable here
del TestHstTable

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
