'''
Created on Apr 13, 2015

@author: woodd
'''

import unittest
from datetime import datetime
from bi_etl.statistics import Statistics
import time


class Test(unittest.TestCase):
    _multiprocess_can_split_ = True

    def test_nested_stats(self):
        s = Statistics()
        s['Val1'] = 1
        s['Val2'] = Statistics()
        s['Val2']['Release'] = datetime(1997,12,13)
        s['Val2']['Version'] = 1.5
        s['Val3'] = 1 
        
        statsStr = Statistics.format_statistics(s)
        self.assertIn('1\n', statsStr)
        self.assertIn('1.500\n', statsStr)
        self.assertIn('1997-12-13', statsStr)
        version = Statistics.finditem(s, 'Version')
        self.assertAlmostEqual(version, 1.5, 2)
        val3 = Statistics.finditem(s, 'Val3')
        self.assertEqual(val3, 1)

    def test_stats_in_list(self):        
        s1 = Statistics()
        s1['Val1'] = 1
        s1['Val2'] = Statistics()
        s1['Val2']['Release'] = datetime(1997,12,13)
        s1['Val2']['Version'] = 1.5
        s1['Val3'] = 1
        s2 = Statistics()
        s2.timer.start()
        time.sleep(0.2)
        s2.timer.stop()
        lst = [s1, s2]
        
        statsStr = Statistics.format_statistics(lst)
        self.assertIn('1\n', statsStr)
        self.assertIn('1.500\n', statsStr)
        self.assertIn('1997-12-13', statsStr)
        version = Statistics.finditem(lst, 'Version')
        self.assertAlmostEqual(version, 1.5, 2)
        val3 = Statistics.finditem(lst, 'Val3')
        self.assertEqual(val3, 1)
        self.assertGreaterEqual(s2['seconds elapsed'], 0.1)
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_list']
    unittest.main()