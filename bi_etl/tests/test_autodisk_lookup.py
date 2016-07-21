'''
Created on Jan 5, 2016

@author: woodd
'''
import unittest

from bi_etl.tests._test_base_lookup import _TestBase
from bi_etl.lookups.autodisk_lookup import AutoDiskLookup
import tempfile
from datetime import datetime
from bi_etl.components.row import Row

#pylint: disable=missing-docstring, protected-access

class TestAutodiskLookup(_TestBase):

    def setUp(self):
        self.TestClass = AutoDiskLookup
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_class_args = {'path': self.temp_dir.name}
        super().setUp()

    def tearDown(self):
        super().tearDown()
        
    def _makerow(self, rowKey):
        source1 = { 
                      self.key1[0]: rowKey,
                      'strval': 'All good caches work perfectly {}'.format(rowKey),
                      'floatval': 1000000.15111 + rowKey,
                      'intval': 12345678900000 + rowKey,
                      'datetimeval': datetime(2005,8,rowKey%25+1,rowKey%24,23,44)
                  }
        return Row(source1, primary_key=self.key1)
        
    def testMemoryLimit(self):        
        lookup = self.TestClass('Test',self.key1, parent_component=self.parent_component, **self.test_class_args)
        rows_before_move = 100
        rows_after_move = 1000
        lookup.ram_check_row_interval = rows_before_move+1
        rowKey = 0
        for _ in range(rows_before_move):
            rowKey += 1
            newRow = self._makerow(rowKey)
            lookup.cache_row(newRow)
        lookup.ram_check_row_interval = 1000
        lookup.max_process_ram_usage_mb = 1
        for _ in range(rows_after_move):
            rowKey += 1
            newRow = self._makerow(rowKey)            
            lookup.cache_row(newRow)
        self.assertGreaterEqual(lookup.get_disk_size(), 1000, 'Disk usage not reported correctly')
        
        self._post_test_cleanup(lookup)
    
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test']
    unittest.main()