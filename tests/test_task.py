"""
Created on Apr 18, 2016

@author: Derek Wood
"""
import logging
import unittest

from tests.config_for_tests import build_config
from tests.etl_jobs.etl_task_d1 import ETL_Task_D1
from tests.etl_jobs.etl_task_d2 import ETL_Task_D2
from tests.etl_jobs.etl_task_d3 import ETL_Task_D3


class TestTask(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger("TestTask")
        self.config = build_config()
        self.config.bi_etl.task_finder_base_module = 'tests.etl_jobs'
        self.config.logging.setup_logging()
        self.log.setLevel(logging.DEBUG)        

    def tearDown(self):
        pass

    @unittest.skip
    def test_normalized_dependents_set(self):
        d1 = ETL_Task_D1(config=self.config)
        d1_deps = d1.normalized_dependents_set
        self.log.info('d1_deps = {}'.format(d1_deps))        
        self.assertEqual(d1_deps, set(), 'd1 dependencies not as expected')
        
        d2 = ETL_Task_D2(config=self.config)
        d2_deps = d2.normalized_dependents_set
        self.log.info('d2_deps = {}'.format(d2_deps))        
        self.assertEqual(d2_deps, {d1.name}, 'd2 dependencies not as expected')
        
        d3 = ETL_Task_D3(config=self.config)
        d3_deps = d3.normalized_dependents_set
        self.log.info('d3_deps = {}'.format(d3_deps))
        self.assertEqual(d3_deps, {d2.name}, 'd3 dependencies not as expected')


if __name__ == "__main__":
    unittest.main()
