"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import logging
import sys
import unittest
from datetime import datetime, date

from bi_etl.exceptions import NoResultFound
from bi_etl.lookups.lookup import Lookup
from tests.config_for_tests import build_config
from tests.dummy_etl_component import DummyETLComponent


# pylint: disable=missing-docstring, protected-access
class _TestBaseLookup(unittest.TestCase):
    """
    Abstract base class for tests common to all Lookup classes
    """

    def setUp(self):

        self.config = build_config()

        self.key1_1 = 'key1'
        self.key1 = [self.key1_1]
        self.parent_component1 = DummyETLComponent(primary_key=self.key1)

        self.source1 = {
            self.key1_1: 1,
            'strval': 'All good caches work perfectly',
            'floatval': 11231.15111,
            'intval': 1234567890,
            'datetimeval': datetime(2005, 8, 25, 18, 23, 44)
        }
        self.parent_component1.column_names = list(self.source1.keys())
        self.row1 = self.parent_component1.Row(data=self.source1)

        self.key3_1 = 'key1'
        self.key3_2 = 'key2'
        self.key3_3 = 'key3'
        self.key3 = [self.key3_1, self.key3_2, self.key3_3]
        self.source3 = {
            self.key3_1: 1,
            self.key3_2: 'ABC',
            self.key3_3: datetime(2015, 12, 25, 9, 15, 20),
            'floatval1': sys.float_info.max,
            'floatval2': sys.float_info.min,
            'floatinf': float("inf"),
            'intval1': sys.maxsize,
            'intval2': -sys.maxsize,
            'intval3': sys.maxsize * 10,  # test long
            'dateval': date(2014, 4, 1)
        }
        self.parent_component3 = DummyETLComponent(primary_key=self.key3)
        self.parent_component3.column_names = self.source3.keys()
        self.row3 = self.parent_component3.Row(self.source3)

        # Only set TestClass and test_class_args if parent hasn't set them yet
        if not hasattr(self, 'TestClass'):
            self.TestClass = Lookup
        if not hasattr(self, 'test_class_args'):
            self.test_class_args = dict()

    def tearDown(self):
        self.parent_component1.close()

    def _post_test_cleanup(self, lookup):
        lookup.clear_cache()

    @staticmethod
    def _get_hashable(val_list):
        return tuple(val_list)

        # Tests for single int key

    def _get_key1_lookup(self):
        lookup = self.TestClass(
            'Test',
            self.key1,
            parent_component=self.parent_component1,
            config=self.config,
            **self.test_class_args
        )
        lookup.init_cache()
        lookup._set_log_level(logging.DEBUG)
        return lookup

    def test_get_list_of_lookup_column_values_1(self):
        lookup = self._get_key1_lookup()
        expected_list = [self.source1[self.key1_1]]
        self.assertEqual(lookup.get_list_of_lookup_column_values(self.row1), expected_list)
        self._post_test_cleanup(lookup)

    def test_cache_and_find_1(self):
        lookup = self._get_key1_lookup()
        lookup.cache_row(self.row1)

        # Test that by default it should allow an update
        lookup.cache_row(self.row1)

        # Test doesn't allow update
        self.assertRaises(ValueError, lookup.cache_row, row=self.row1, allow_update=False)

        # Test lookups
        search_row1 = self.parent_component1.Row({self.key1_1: 1})
        match_row = lookup.find_in_cache(search_row1)
        diffs = self.row1.compare_to(match_row)
        self.assertEqual(diffs, [], f'Diffs {diffs} found in matched row')

        # Test lookup fail
        search_row2 = self.parent_component1.Row({self.key1_1: 2})
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=search_row2)

        self._post_test_cleanup(lookup)

    def test_len_1(self):
        lookup = self._get_key1_lookup()
        for cnt in range(1, 100):
            new_row = self.row1.clone()
            new_row[self.key1_1] = cnt
            lookup.cache_row(new_row)
            self.assertEqual(len(lookup), cnt, 'Lookup len does not match rows added')
            lookup.cache_row(new_row)
            self.assertEqual(len(lookup), cnt, 'Lookup len does not match rows added - after duplicate add')
        # test iter
        found_dict = dict()
        for row in lookup:
            found_dict[row[self.key1_1]] = 1
        for cnt in range(1, 100):
            self.assertIn(cnt, found_dict, f'Iter did not return key {cnt}')
            self._post_test_cleanup(lookup)

    # ------- Tests for key of len 3

    def _get_key3_lookup(self):
        lookup = self.TestClass(
            'Test',
            self.key3,
            parent_component=self.parent_component1,
            **self.test_class_args
            )
        lookup.init_cache()
        lookup._set_log_level(logging.DEBUG)
        return lookup

    def test_get_list_of_lookup_column_values_3(self):
        lookup = self._get_key3_lookup()

        expected_list = [self.source3[key] for key in self.key3]
        self.assertEqual(lookup.get_list_of_lookup_column_values(self.row3), expected_list)
        self._post_test_cleanup(lookup)

    def test_cache_and_find_3(self):
        lookup = self._get_key3_lookup()
        lookup.cache_row(self.row3)

        # By default it should allow an update
        lookup.cache_row(self.row3)

        # Test doesn't allow update
        self.assertRaises(ValueError, lookup.cache_row, row=self.row3, allow_update=False)
        expected_keys = self.row3.subset(keep_only=self.key3)

        # Test lookups
        self.assertEqual(lookup.find_in_cache(expected_keys), self.row3)

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

        self._post_test_cleanup(lookup)

    def test_len_3(self):
        lookup = self._get_key3_lookup()
        for cnt in range(1, 300):
            new_row = self.row3.clone()
            new_row[self.key3_1] = cnt
            lookup.cache_row(new_row)
            self.assertEqual(len(lookup), cnt, 'Lookup len does not match rows added')
            lookup.cache_row(new_row)
            self.assertEqual(len(lookup), cnt, 'Lookup len does not match rows added - after duplicate add')
        # test iter
        found_dict = dict()
        for row in lookup:
            found_dict[row[self.key3_1]] = 3
        for cnt in range(1, 300):
            self.assertIn(cnt, found_dict, f'Iter did not return key {cnt}')
        self._post_test_cleanup(lookup)
