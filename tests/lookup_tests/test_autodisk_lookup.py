"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import tempfile
import unittest
from datetime import datetime

from bi_etl.lookups.autodisk_lookup import AutoDiskLookup
from tests.lookup_tests._test_base_lookup import _TestBaseLookup


# pylint: disable=missing-docstring, protected-access


class TestAutodiskLookup(_TestBaseLookup):
    def setUp(self):
        self.TestClass = AutoDiskLookup
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_class_args = {'path': self.temp_dir.name}
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.temp_dir.cleanup()

    def _makerow(self, row_key):
        source1 = {
            self.key1[0]:  row_key,
            'strval': f'All good caches work perfectly {row_key}',
            'floatval':    1000000.15111 + row_key,
            'intval':      12345678900000 + row_key,
            'datetimeval': datetime(2005, 8, row_key % 25 + 1, row_key % 24, 23, 44)
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
            new_row = self._makerow(row_key)
            lookup.cache_row(new_row)
        lookup.ram_check_row_interval = 1000
        lookup.max_process_ram_usage_mb = 1
        for _ in range(rows_after_move):
            row_key += 1
            new_row = self._makerow(row_key)
            lookup.cache_row(new_row)
        self.assertGreaterEqual(lookup.get_disk_size(), 1000, 'Disk usage not reported correctly')

        self.assertEqual(len(lookup), rows_before_move + rows_after_move)

        self._post_test_cleanup(lookup)


del _TestBaseLookup


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test']
    unittest.main()
