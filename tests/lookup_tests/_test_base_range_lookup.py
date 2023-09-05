"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import unittest
from datetime import datetime

from bi_etl.exceptions import AfterExisting
from bi_etl.exceptions import BeforeAllExisting
from bi_etl.exceptions import NoResultFound
from bi_etl.lookups.range_lookup import RangeLookup
from tests.dummy_etl_component import DummyETLComponent
from tests.lookup_tests._test_base_lookup import _TestBaseLookup


class _TestBaseRangeLookup(_TestBaseLookup):
    def setUp(self):
        self.TestClass = RangeLookup
        self.begin_date = 'beg_date'
        self.end_date = 'end_date'
        self.test_class_args = {'begin_date': self.begin_date,
                                'end_date':   self.end_date,
                                }
        super().setUp()

        self.source1[self.begin_date] = datetime(2005, 8, 25, 18, 23, 44)
        self.source1[self.end_date] = datetime(9999, 1, 1, 0, 0, 0)
        self.parent_component1 = DummyETLComponent(primary_key=self.key1)
        self.row1 = self.parent_component1.Row(self.source1)

        self.source3[self.begin_date] = datetime(2005, 8, 25, 18, 23, 44)
        self.source3[self.end_date] = datetime(9999, 1, 1, 0, 0, 0)
        self.parent_component3 = DummyETLComponent(primary_key=self.key3)
        self.row3 = self.parent_component3.Row(self.source3)

    def test_cache_and_find_1(self):
        lookup = self._get_key1_lookup()
        lookup.cache_row(self.row1)
        # By default it should allow an update
        lookup.cache_row(self.row1)

        # Test doesn't allow update
        self.assertRaises(ValueError, lookup.cache_row, row=self.row1, allow_update=False)

        # Add another row to test lookup range
        test_earlier_row = self.row1.clone()
        test_earlier_row[self.begin_date] = datetime(2002, 1, 1, 0, 0, 0)
        test_earlier_row[self.end_date] = datetime(2005, 8, 25, 18, 23, 43)
        lookup.cache_row(test_earlier_row)

        # Test lookups
        search_row1 = self.parent_component1.Row(
            {self.key1_1:     1,
             self.begin_date: datetime(2006, 1, 1, 0, 0, 0)
             })
        self.assertEqual(lookup.find_in_cache(search_row1), self.row1)

        # Test lookup of earlier row
        search_row1 = self.parent_component1.Row(
            {self.key1_1:     1,
             self.begin_date: datetime(2003, 1, 1, 0, 0, 0)
             })
        self.assertEqual(lookup.find_in_cache(search_row1), test_earlier_row)

        # Test lookup fail
        search_row2 = self.parent_component1.Row(
            {self.key1_1:     99,
             self.begin_date: datetime(2006, 1, 1, 0, 0, 0)
             })
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=search_row2)

        # Test lookup fail - too early
        search_row2 = self.parent_component1.Row(
            {self.key1_1:     1,
             self.begin_date: datetime(2000, 1, 1, 0, 0, 0)
             })
        self.assertRaises(BeforeAllExisting, lookup.find_in_cache, row=search_row2)

        # Test lookup fail - too late
        search_row2 = self.parent_component1.Row(
            {self.key1_1:     1,
             self.begin_date: datetime(9999, 12, 31, 0, 0, 0)
             })
        self.assertRaises(AfterExisting, lookup.find_in_cache, row=search_row2)

        self._post_test_cleanup(lookup)

    def test_cache_and_find_3(self):
        lookup = self._get_key3_lookup()
        lookup.cache_row(self.row3)

        # By default it should allow an update
        lookup.cache_row(self.row3)

        # Test doesn't allow update
        self.assertRaises(ValueError, lookup.cache_row, row=self.row3, allow_update=False)
        expected_keys = self.row3.subset(keep_only=self.key3)

        # Add another row to test lookup range
        test_earlier_row = self.row3.clone()
        test_earlier_row[self.begin_date] = datetime(2002, 1, 1, 0, 0, 0)
        test_earlier_row[self.end_date] = datetime(2005, 8, 25, 18, 23, 43)
        lookup.cache_row(test_earlier_row)

        # Test lookups
        expected_keys[self.begin_date] = datetime(2006, 1, 1, 00, 00, 00)
        self.assertEqual(lookup.find_in_cache(expected_keys), self.row3)

        # Test lookup of earlier row
        expected_keys[self.begin_date] = datetime(2003, 1, 1, 00, 00, 00)
        self.assertEqual(lookup.find_in_cache(expected_keys), test_earlier_row)

        # Test lookup fail
        not_expected_keys = expected_keys.clone()
        not_expected_keys[self.key3_1] = 99
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=not_expected_keys)

        # Test lookup fail 2nd col
        not_expected_keys = expected_keys.clone()
        not_expected_keys[self.key3_2] = 'XY'
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=not_expected_keys)

        # Test lookup fail 3rd col
        not_expected_keys = expected_keys.clone()
        not_expected_keys[self.key3_2] = datetime(2014, 12, 25, 9, 15, 20)
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=not_expected_keys)

        # Test lookup fail 3rd col
        not_expected_keys = expected_keys.clone()
        not_expected_keys[self.key3_2] = datetime(2014, 12, 25, 9, 15, 20)
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=not_expected_keys)

        self._post_test_cleanup(lookup)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test']
    unittest.main()
