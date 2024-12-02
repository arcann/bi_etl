"""
Created on Apr 13, 2015

@author: Derek Wood
"""

import time
import unittest
from datetime import datetime

from bi_etl.statistics import Statistics


class TestStatistics(unittest.TestCase):
    _multiprocess_can_split_ = True

    def test_nested_stats(self):
        s = Statistics('root')
        s['Val1'] = 1
        s['Val2'] = Statistics('Val2 id to be dropped')
        s['Val2']['Release'] = datetime(1997, 12, 13)
        s['Val2']['Version'] = 1.5
        s['Val3'] = 1 
        
        stats_str = Statistics.format_statistics(s)
        self.assertIn('1\n', stats_str)
        self.assertIn('1.500\n', stats_str)
        self.assertIn('1997-12-13', stats_str)
        version = Statistics.find_item(s, 'Version')
        self.assertAlmostEqual(version, 1.5, 2)
        val3 = Statistics.find_item(s, 'Val3')
        self.assertEqual(val3, 1)

    def test_nested_stats2(self):
        s = Statistics('root')
        s['Val1'] = 1
        s_val2 = Statistics('Val2', parent=s)
        s_val2['Release'] = datetime(1997, 12, 13)
        s_val2['Version'] = 1.5
        s['Val3'] = 1

        stats_str = Statistics.format_statistics(s)
        self.assertIn('1\n', stats_str)
        self.assertIn('1.500\n', stats_str)
        self.assertIn('1997-12-13', stats_str)
        version = Statistics.find_item(s, 'Version')
        self.assertAlmostEqual(version, 1.5, 2)
        val3 = Statistics.find_item(s, 'Val3')
        self.assertEqual(val3, 1)

    def test_stats_in_list(self):
        s1 = Statistics('root')
        s1['Val1'] = 1
        s_val2 = Statistics('Val2', parent=s1)
        s_val2['Release'] = datetime(1997, 12, 13)
        s_val2['Version'] = 1.5
        s1['Val3'] = 1

        s2 = Statistics('second')
        s2.timer.start()
        time.sleep(0.2)
        s2.timer.stop()

        lst = [s1, s2]
        
        stats_str = Statistics.format_statistics(lst)
        self.assertIn('1\n', stats_str)
        self.assertIn('1.500\n', stats_str)
        self.assertIn('1997-12-13', stats_str)
        version = Statistics.find_item(lst, 'Version')
        self.assertAlmostEqual(version, 1.5, 2)
        val3 = Statistics.find_item(lst, 'Val3')
        self.assertEqual(val3, 1)
        self.assertGreaterEqual(s2['seconds elapsed'], 0.1)

    def test_context_block(self):
        with Statistics('tenth') as s:
            time.sleep(0.1)
        time.sleep(0.1)
        self.assertAlmostEqual(s.timer.seconds_elapsed, 0.1, 1)
        self.assertAlmostEqual(s.seconds_elapsed, 0.1, 1)
        self.assertAlmostEqual(s['seconds elapsed'], 0.1, 1)


if __name__ == "__main__":
    unittest.main()
