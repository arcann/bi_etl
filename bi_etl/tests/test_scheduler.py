
"""
Created on Apr 18, 2016

@author: Derek Wood
"""
"""
Created on Dec 23, 2015

@author: Derek Wood
"""
import logging
import unittest

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.scheduler.scheduler_interface import SchedulerInterface


class IntegrationTestScheduler(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger( "TestScheduler" )
        self.config = BIConfigParser()
        self.config['Scheduler'] = dict()
        self.config['Scheduler']['base_module'] = 'bi_etl.tests.etl_jobs'
        self.config['loggers'] = dict()
        self.config['loggers']['root'] = 'DEBUG'
        self.config.setup_logging()
        self.log.setLevel(logging.DEBUG)
        self.scheduler = SchedulerInterface(log= self.log, config= self.config)

    def tearDown(self):
        pass
    
    def test_find_etl_classes_1(self):
        self.scheduler.scan_etl_classes()
        results = set(self.scheduler.find_etl_classes('etl_task_d*'))
        expected_results = {'bi_etl.tests.etl_jobs.etl_task_d1.ETL_Task_D1',
                            'bi_etl.tests.etl_jobs.etl_task_d2.ETL_Task_D2',
                            'bi_etl.tests.etl_jobs.etl_task_d3.ETL_Task_D3'}
        self.assertEqual(results, expected_results, 'etl_task_d search did not return expected results')
        
    def test_find_etl_classes_2(self):
        results = set(self.scheduler.find_etl_classes('bi_etl.scheduler.scheduler_etl_jobs.etl_task_status_cd.ETL_Task_Status_CD'))
        expected_results = {'bi_etl.scheduler.scheduler_etl_jobs.etl_task_status_cd.ETL_Task_Status_CD'}
        self.assertEqual(results, expected_results, 'etl_task_d search did not return expected results')
        
    def test_find_etl_classes_3(self):
        results = set(self.scheduler.find_etl_classes('etl_task_status_cd.ETL_Task_Status_CD'))
        expected_results = {'bi_etl.scheduler.scheduler_etl_jobs.etl_task_status_cd.ETL_Task_Status_CD'}
        self.assertEqual(results, expected_results, 'etl_task_d search did not return expected results')
        
    def test_find_etl_classes_4(self):
        results = set(self.scheduler.find_etl_classes('etl_task_status_cd'))
        expected_results = {'bi_etl.scheduler.scheduler_etl_jobs.etl_task_status_cd.ETL_Task_Status_CD'}
        self.assertEqual(results, expected_results, 'etl_task_d search did not return expected results')
        
    def test_find_etl_classes_5(self):
        results = set(self.scheduler.find_etl_classes('ETL_Task_Status_CD'))
        expected_results = {'bi_etl.scheduler.scheduler_etl_jobs.etl_task_status_cd.ETL_Task_Status_CD'}
        self.assertEqual(results, expected_results, 'etl_task_d search did not return expected results')
        
    def test_find_etl_class_instance_1(self):
        class_found = self.scheduler.find_etl_class_instance('etl_task_status_cd')        
        expected_instance_name = 'bi_etl.scheduler.scheduler_etl_jobs.etl_task_status_cd.ETL_Task_Status_CD'
        self.assertEqual(class_found().name, expected_instance_name, 'etl_task_d search did not return expected results')
        
    def test_find_etl_class_instance_2(self):
        class_found = self.scheduler.find_etl_class_instance('ETL_Task_Status_CD')        
        expected_instance_name = 'bi_etl.scheduler.scheduler_etl_jobs.etl_task_status_cd.ETL_Task_Status_CD'
        self.assertEqual(class_found().name, expected_instance_name, 'etl_task_d search did not return expected results')

if __name__ == "__main__":    
    unittest.main()