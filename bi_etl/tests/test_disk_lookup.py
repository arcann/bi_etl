"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import unittest

from bi_etl.tests._test_base_lookup import _TestBase
from bi_etl.lookups.disk_lookup import DiskLookup
import tempfile
import os


class TestDiskLookup(_TestBase):

    def setUp(self):
        self.TestClass = DiskLookup
        self.temp_dir_mgr = tempfile.TemporaryDirectory()
        self.test_class_args = {'path': self.temp_dir_mgr.name}
        super().setUp()

    def tearDown(self):
        super().tearDown()
        try:
            self.temp_dir_mgr.cleanup()
        except Exception:
            pass

    def _post_test_cleanup(self, lookup):
        lookup.clear_cache()
        for file_name in os.listdir(self.temp_dir_mgr.name):
            self.assertIsNone(file_name, 'lookup did not cleanup file {} (unit test tearDown will clean it up)'.format(file_name))

    @staticmethod
    def _get_hashable(val_list):
        """
        Overridden here because disk uses shelve which needs str keys
        """
        return str(val_list)
    
    def test_disk_usage(self):
        lookup = self._get_key1_lookup()
        for cnt in range(1, 10000):
            new_row = self.row1.clone()
            new_row[self.key1_1] = cnt
            lookup.cache_row(new_row)
        self.assertGreaterEqual(lookup.get_disk_size(), 10000)
        
        self._post_test_cleanup(lookup)
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test']
    unittest.main()