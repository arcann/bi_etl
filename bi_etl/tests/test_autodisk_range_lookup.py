"""
Created on Jan 5, 2016

@author: woodd
"""
import unittest
import tempfile
from datetime import datetime

from bi_etl.components.row import Row
from bi_etl.tests._test_base_range_lookup import _TestBaseRangeLookup
from bi_etl.lookups.autodisk_range_lookup import AutoDiskRangeLookup

#pylint: disable=missing-docstring, protected-access

class TestAutodiskRangeLookup(_TestBaseRangeLookup):

    def setUp(self):
        super().setUp()
        self.TestClass = AutoDiskRangeLookup
        self.temp_dir_mgr = tempfile.TemporaryDirectory(dir='e:\\temp')
        self.test_class_args['path'] = self.temp_dir_mgr.name

    def tearDown(self):
        super().tearDown()
        
    def _makerow(self, rowKey):
        source1 = { 
                      self.key1[0]: rowKey,
                      self.begin_date: datetime(2005,8,25,18,23,44),
                      self.end_date: datetime(9999,1,1,0,0,0),
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