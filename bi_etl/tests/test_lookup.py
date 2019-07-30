"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import unittest

from bi_etl.lookups.lookup import Lookup
from bi_etl.tests._test_base_lookup import _TestBase

class TestLookup(_TestBase):

    def setUp(self):
        self.TestClass = Lookup
        super().setUp()

    def tearDown(self):
        super().tearDown()
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test']
    unittest.main()