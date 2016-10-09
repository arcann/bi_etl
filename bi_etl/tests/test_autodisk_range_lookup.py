"""
Created on Jan 5, 2016

@author: woodd
"""
import unittest
import tempfile
from datetime import datetime

from bi_etl.components.row.row import Row
from bi_etl.tests._test_base_range_lookup import _TestBaseRangeLookup
from bi_etl.lookups.autodisk_range_lookup import AutoDiskRangeLookup


# pylint: disable=missing-docstring, protected-access


class TestAutodiskRangeLookup(_TestBaseRangeLookup):
    def setUp(self):
        super().setUp()
        self.TestClass = AutoDiskRangeLookup
        self.temp_dir_mgr = tempfile.TemporaryDirectory()
        self.test_class_args['path'] = self.temp_dir_mgr.name

    def tearDown(self):
        super().tearDown()

    def _make_row(self, row_key):
        source1 = {
            self.key1[0]:    row_key,
            self.begin_date: datetime(2005, 8, 25, 18, 23, 44),
            self.end_date:   datetime(9999, 1, 1, 0, 0, 0),
            'strval':        'All good caches work perfectly {}'.format(row_key),
            'floatval':      1000000.15111 + row_key,
            'intval':        12345678900000 + row_key,
            'datetimeval':   datetime(2005, 8, row_key % 25 + 1, row_key % 24, 23, 44)
        }
        return self.parent_component1.Row(source1)

    def testMemoryLimit(self):
        lookup = self.TestClass('Test', self.key1, parent_component=self.parent_component1, **self.test_class_args)
        rows_before_move = 100
        rows_after_move = 1000
        lookup.ram_check_row_interval = rows_before_move + 1
        row_key = 0
        for _ in range(rows_before_move):
            row_key += 1
            new_row = self._make_row(row_key)
            lookup.cache_row(new_row)
        lookup.ram_check_row_interval = 1000
        lookup.max_process_ram_usage_mb = 1
        for _ in range(rows_after_move):
            row_key += 1
            new_row = self._make_row(row_key)
            lookup.cache_row(new_row)
        self.assertGreaterEqual(lookup.get_disk_size(), 1000, 'Disk usage not reported correctly')

        self._post_test_cleanup(lookup)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test']
    unittest.main()
