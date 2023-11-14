"""
Created on Apr 18, 2016

@author: Derek Wood
"""
import logging
import unittest

from tests.config_for_tests import build_config
from tests.etl_jobs.etl_task_d1 import ETL_Task_D1
from tests.etl_jobs.etl_task_d2 import ETL_Task_D2


class TestTask(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger("TestTask")
        self.config = build_config()
        self.config.bi_etl.task_finder_base_module = 'tests.etl_jobs'
        self.config.logging.setup_logging()
        self.log.setLevel(logging.DEBUG)        

    def tearDown(self):
        pass

    def test_param_passing_1a(self):
        d1 = ETL_Task_D1(config=self.config)
        d1.set_parameter('param_test1', 112233)
        d1.set_parameter('job_run_seconds', 0)
        d1.run()
        try:
            self.assertEqual(d1.got_param_test1, 112233)
        except AttributeError:
            raise RuntimeError("ETL_Task_D1 run did not set got_param_test1")

    def test_param_passing_1b(self):
        d1 = ETL_Task_D1(config=self.config)
        d1.set_parameters(param_test1=111222)
        d1.set_parameter('job_run_seconds', 0)
        d1.run()
        try:
            self.assertEqual(d1.got_param_test1, 111222)
        except AttributeError:
            raise RuntimeError("ETL_Task_D1 run did not set got_param_test1")

    def test_param_passing_2(self):
        d2 = ETL_Task_D2(config=self.config, param_test1=123)
        d2.set_parameter('job_run_seconds', 0)
        d2.run()
        try:
            self.assertEqual(d2.got_param_test1, 123)
        except AttributeError:
            raise RuntimeError("ETL_Task_D2 run did not set got_param_test1")


if __name__ == "__main__":
    unittest.main()
