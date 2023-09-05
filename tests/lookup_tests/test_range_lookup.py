"""
Created on Jan 5, 2016

@author: Derek Wood
"""
import unittest

from tests.lookup_tests._test_base_range_lookup import _TestBaseRangeLookup


class TestRangeLookup(_TestBaseRangeLookup):
    # All tests we need here are in _TestBaseRangeLookup
    pass    


del _TestBaseRangeLookup


if __name__ == "__main__":
    unittest.main()
