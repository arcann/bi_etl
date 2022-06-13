"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import unittest

from bi_etl.lookups.lookup import Lookup
from tests._test_base_lookup import _TestBaseLookup


class TestLookup(_TestBaseLookup):

    def setUp(self):
        self.TestClass = Lookup
        super().setUp()

    def tearDown(self):
        super().tearDown()

    # All tests we need here are in _TestBaseLookup
        
