"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import os
import tempfile
import unittest

from bi_etl.lookups.disk_range_lookup import DiskRangeLookup
from tests.lookup_tests._test_base_range_lookup import _TestBaseRangeLookup


class TestDiskRangeLookup(_TestBaseRangeLookup):

    def setUp(self):
        super().setUp()
        self.TestClass = DiskRangeLookup
        self.temp_dir_mgr = tempfile.TemporaryDirectory()
        self.test_class_args['path'] = self.temp_dir_mgr.name
        
    def tearDown(self):
        self.temp_dir_mgr.cleanup()
        super().tearDown()
        
    @staticmethod
    def _get_hashable(val_list):
        """
        Overridden here because disk uses shelve which needs str keys
        """
        return str(val_list)
    
    def _post_test_cleanup(self, lookup):
        lookup.clear_cache()
        for file_name in os.listdir(self.temp_dir_mgr.name):
            self.assertIsNone(file_name,
                              f'lookup did not cleanup file {file_name} (unit test tearDown will clean it up)'
                              )


del _TestBaseRangeLookup

    
if __name__ == "__main__":
    unittest.main()
