"""
Created on Jan 5, 2016

@author: woodd
"""
import unittest
import logging
import sys
from datetime import datetime, date

from bi_etl.components.row import Row
from bi_etl.exceptions import NoResultFound
from bi_etl.tests.dummy_etl_component import DummyETLComponent
from bi_etl.lookups.lookup import Lookup

#pylint: disable=missing-docstring, protected-access


class _TestBase(unittest.TestCase):
    """
    Abstract base class for tests common to all Lookup classes
    """

    def setUp(self):
        self.parent_component = DummyETLComponent()
        self.key1_1 = 'key1'
        self.key1 = [self.key1_1]
        self.source1 = { 
                      self.key1_1: 1,
                      'strval': 'All good caches work perfectly',
                      'floatval': 11231.15111,
                      'intval': 1234567890,
                      'datetimeval': datetime(2005,8,25,18,23,44)
                      }
        self.row1 = Row(self.source1, primary_key=self.key1)
        
        self.key3_1 = 'key1'
        self.key3_2 = 'key2'
        self.key3_3 = 'key3'
        self.key3 = [self.key3_1,self.key3_2,self.key3_3]
        self.source3 = { 
                      self.key3_1: 1,
                      self.key3_2: 'ABC',
                      self.key3_3: datetime(2015,12,25,9,15,20),
                      'floatval1': sys.float_info.max,
                      'floatval2': sys.float_info.min,
                      'floatinf': float("inf"),
                      'intval1': sys.maxsize,
                      'intval2': -sys.maxsize,
                      'intval3': sys.maxsize*10, ## test long
                      'dateval': date(2014,4,1)
                      }
        self.row3 = Row(self.source3, primary_key=self.key3)
        
        # Only set TestClass and test_class_args if parent hasn't set them yet
        if not hasattr(self,'TestClass'):
            self.TestClass = Lookup
        if not hasattr(self,'test_class_args'):
            self.test_class_args = dict()
            
    def tearDown(self):
        self.parent_component.close()

    def _post_test_cleanup(self, lookup):
        lookup.clear_cache()
        
    @staticmethod
    def _get_hashable(val_list):
        return tuple(val_list)        
        
    ### Tests for single int key

    def _get_key1_lookup(self):
        lookup = self.TestClass('Test',self.key1, parent_component=self.parent_component, **self.test_class_args)
        lookup.init_cache()
        lookup._set_log_level(logging.DEBUG)
        return lookup

    def testBeforeInit_1(self):
        lookup = self.TestClass('Test',self.key1, parent_component=self.parent_component, **self.test_class_args)
        self.assertRaises(ValueError, lookup.find_in_cache, row=self.row1)
        self._post_test_cleanup(lookup)
        
    def test_get_list_of_lookup_column_values_1(self):
        lookup = self._get_key1_lookup()
        expectedList = [ self.source1[self.key1_1] ]
        self.assertEqual(lookup.get_list_of_lookup_column_values(self.row1), expectedList)
        self._post_test_cleanup(lookup)
        
    def test_cache_and_find_1(self):
        lookup = self._get_key1_lookup()
        lookup.cache_row(self.row1)
        
        ## Test that by default it should allow an update
        lookup.cache_row(self.row1)
        
        ## Test doesn't allow update
        self.assertRaises(ValueError, lookup.cache_row, row=self.row1, allow_update=False)
        
        ## Test lookups
        search_row1 = Row({ self.key1_1: 1,  })
        self.assertEqual(lookup.find_in_cache(search_row1), self.row1)
        
        ## Test lookup fail
        search_row2 = Row({ self.key1_1: 2,  })
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=search_row2)

        self._post_test_cleanup(lookup)
        
    def test_len_1(self):
        lookup = self._get_key1_lookup()
        for cnt in range(1, 100):
            newRow = self.row1.clone()
            newRow[self.key1_1] = cnt            
            lookup.cache_row(newRow)
            self.assertEqual(len(lookup), cnt, 'Lookup len does not match rows added')
            lookup.cache_row(newRow)
            self.assertEqual(len(lookup), cnt, 'Lookup len does not match rows added - after duplicate add')
        ## test iter
        found_dict = dict()
        for row in lookup:
            found_dict[row[self.key1_1]] = 1
        for cnt in range(1, 100):
            self.assertIn(cnt, found_dict, 'Iter did not return key {}'.format(cnt))
            self._post_test_cleanup(lookup)
        
    ###### Tests for key of len 3

    def _get_key3_lookup(self):
        lookup = self.TestClass('Test',self.key3, parent_component=self.parent_component, **self.test_class_args)
        lookup.init_cache()
        lookup._set_log_level(logging.DEBUG)
        return lookup
        
    def test_get_list_of_lookup_column_values_3(self):
        lookup = self._get_key3_lookup()
    
        expectedList = [ self.source3[key] for key in self.key3]
        self.assertEqual(lookup.get_list_of_lookup_column_values(self.row3), expectedList)
        self._post_test_cleanup(lookup)
                 
    def test_cache_and_find_3(self):
        lookup = self._get_key3_lookup()
        lookup.cache_row(self.row3)
        
        ## By default it should allow an update
        lookup.cache_row(self.row3)
        
        ## Test doesn't allow update
        self.assertRaises(ValueError, lookup.cache_row, row=self.row3, allow_update=False)
        expectedKeys = self.row3.subset(keep_only=self.key3)
        
        ## Test lookups
        self.assertEqual(lookup.find_in_cache(expectedKeys), self.row3)
        
        ## Test lookup fail
        notExpectedKeys = expectedKeys.clone()
        notExpectedKeys[self.key3_1]=99
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=notExpectedKeys)
        
        ## Test lookup fail 2nd col
        notExpectedKeys = expectedKeys.clone()
        notExpectedKeys[self.key3_2]='XY'
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=notExpectedKeys)
        
        ## Test lookup fail 3rd col
        notExpectedKeys = expectedKeys.clone()
        notExpectedKeys[self.key3_2]=datetime(2014,12,25,9,15,20)
        self.assertRaises(NoResultFound, lookup.find_in_cache, row=notExpectedKeys)

        self._post_test_cleanup(lookup)
        
    def test_len_3(self):
        lookup = self._get_key3_lookup()
        for cnt in range(1, 300):
            newRow = self.row3.clone()
            newRow[self.key3_1] = cnt            
            lookup.cache_row(newRow)
            self.assertEqual(len(lookup), cnt, 'Lookup len does not match rows added')
            lookup.cache_row(newRow)
            self.assertEqual(len(lookup), cnt, 'Lookup len does not match rows added - after duplicate add')
        ## test iter
        found_dict = dict()
        for row in lookup:
            found_dict[row[self.key3_1]] = 3
        for cnt in range(1, 300):
            self.assertIn(cnt, found_dict, 'Iter did not return key {}'.format(cnt))
        self._post_test_cleanup(lookup)
