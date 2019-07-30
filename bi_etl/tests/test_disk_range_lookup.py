"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import unittest

from bi_etl.lookups.disk_range_lookup import DiskRangeLookup
import tempfile

from bi_etl.tests._test_base_range_lookup import _TestBaseRangeLookup
import os

class TestDiskRangeLookup(_TestBaseRangeLookup):

    def setUp(self):
        super().setUp()
        self.TestClass = DiskRangeLookup
        self.temp_dir_mgr = tempfile.TemporaryDirectory()
        self.test_class_args['path'] = self.temp_dir_mgr.name
        
    def tearDown(self):
        super().tearDown()        
        self.temp_dir_mgr.cleanup()
        
    @staticmethod
    def _get_hashable(val_list):
        """
        Overridden here because disk uses shelve which needs str keys
        """
        return str(val_list)
    
    def _post_test_cleanup(self, lookup):
        lookup.clear_cache()
        for file_name in os.listdir(self.temp_dir_mgr.name):
            self.assertIsNone(file_name, 'lookup did not cleanup file {} (unit test tearDown will clean it up)'.format(file_name))

    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test']
    unittest.main()