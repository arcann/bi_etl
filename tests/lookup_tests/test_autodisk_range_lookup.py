"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import tempfile
import unittest
from datetime import datetime

from bi_etl.exceptions import NoResultFound, AfterExisting, BeforeAllExisting
from bi_etl.lookups.autodisk_range_lookup import AutoDiskRangeLookup
from tests.lookup_tests._test_base_range_lookup import _TestBaseRangeLookup
# pylint: disable=missing-docstring, protected-access
from tests.dummy_etl_component import DummyETLComponent


class TestAutodiskRangeLookup(_TestBaseRangeLookup):
    def setUp(self):
        super().setUp()
        self.TestClass = AutoDiskRangeLookup
        self.temp_dir_mgr = tempfile.TemporaryDirectory()
        self.test_class_args['path'] = self.temp_dir_mgr.name
        self.parent_component = DummyETLComponent()

    def tearDown(self):
        super().tearDown()
        self.temp_dir_mgr.cleanup()

    def _make_row(self,
                  row_key,
                  begin_date = datetime(2005, 8, 25, 18, 23, 44),
                  end_date = datetime(9999, 1, 1, 0, 0, 0)
                  ):
        source1 = {
            self.key1[0]:    row_key,
            self.begin_date: begin_date,
            self.end_date:   end_date,
            'strval': f'All good caches work perfectly {row_key}',
            'floatval':      1000000.15111 + row_key,
            'intval':        12345678900000 + row_key,
            'datetimeval':   datetime(2005, 8, row_key % 25 + 1, row_key % 24, 23, 44)
        }
        return self.parent_component.Row(source1)

    def testMemoryLimit(self):
        lookup = self.TestClass('Test', self.key1, parent_component=self.parent_component1, **self.test_class_args)

    def testMemoryLimit2(self):
        lookup = self.TestClass('Test',
                                self.key1,
                                parent_component=self.parent_component,
                                **self.test_class_args)
        rows_before_move = 100
        rows_after_move = 1000
        lookup.ram_check_row_interval = rows_before_move + 1
        row_key = 0
        row_list = list()
        dates = [(datetime(2000, 1, 1, 0, 0, 0), datetime(2000, 12, 31, 23, 59, 59)),
                 (datetime(2001, 1, 1, 0, 0, 0), datetime(2001, 12, 31, 23, 59, 59)),
                 (datetime(2002, 1, 1, 0, 0, 0), datetime(2002, 12, 31, 23, 59, 59)),
                 (datetime(2003, 1, 1, 0, 0, 0), datetime(2003, 12, 31, 23, 59, 59)),
              ]
        for _ in range(rows_before_move):
            row_key += 1
            for begin_date, end_date in dates:
                new_row = self._make_row(row_key, begin_date, end_date)
                row_list.append(new_row)
                lookup.cache_row(new_row)
        lookup.ram_check_row_interval = 1000
        lookup.max_process_ram_usage_mb = 1
        for _ in range(rows_after_move):
            row_key += 1
            for begin_date, end_date in dates:
                new_row = self._make_row(row_key, begin_date, end_date)
                row_list.append(new_row)
                lookup.cache_row(new_row)

        for row in row_list:
            found_row = lookup.find_in_cache(row)
            self.assertEqual(found_row, row)

        self.assertEqual(len(lookup), len(dates) * (rows_before_move + rows_after_move))

        self.assertGreaterEqual(lookup.get_disk_size(), 1000, 'Disk usage not reported correctly')

        new_row = self._make_row(1, datetime(2010, 1, 1, 0, 0, 0), datetime(2011, 12, 31, 23, 59, 59))
        self.assertRaises(AfterExisting, lookup.find_in_cache, new_row)

        new_row = self._make_row(1, datetime(1900, 1, 1, 0, 0, 0), datetime(2011, 12, 31, 23, 59, 59))
        self.assertRaises(BeforeAllExisting, lookup.find_in_cache, new_row)

        new_row = self._make_row(-1, datetime(2001, 1, 1, 0, 0, 0), datetime(2011, 12, 31, 23, 59, 59))
        self.assertRaises(NoResultFound, lookup.find_in_cache, new_row)

        self._post_test_cleanup(lookup)


del _TestBaseRangeLookup


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test']
    unittest.main()
