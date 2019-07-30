"""
Created on Dec 23, 2015

@author: Derek Wood
"""
from datetime import timedelta
import logging
import operator
import random
import unittest
from unittest.case import SkipTest

from bi_etl.scheduler.scheduler_interface import SchedulerInterface
from bi_etl.scheduler.task import Status

from bi_etl.tests.etl_jobs.etl_task_1 import ETL_Task_1
from bi_etl.tests.etl_jobs.etl_task_d1 import ETL_Task_D1
from bi_etl.tests.etl_jobs.etl_task_d2 import ETL_Task_D2
from bi_etl.tests.etl_jobs.etl_task_d3 import ETL_Task_D3


class IntegrationTestScheduler(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger( "TestScheduler" )
        try:
            ## Note: This test uses the "live" INI file for the current user to get the config for the SchedulerInterface
            self.scheduler = SchedulerInterface(log= self.log)
            if self.scheduler.get_heartbeat_age_timedelta() > timedelta(minutes=2):
                msg = 'Scheduler not running to support TestScheduler'
                print(msg)
                raise SkipTest(msg)
            random.seed()
        except Exception as e: 
            raise SkipTest(repr(e))

    def tearDown(self):
        pass
    
    def _wait_for_finish(self, task_id):
        self.assertEqual(self.scheduler.wait_for_task(task_id), Status.succeeded, 'task {} failed'.format(task_id))
    
    def _check_for_overlap(self, task_1_rec, task_2_rec):
        ## Note: tasks don't record being finished until after it's children finish        
        
        if task_1_rec.started_date > task_2_rec.started_date:
            ## Swap so that task 1 is first
            task_1_rec, task_2_rec = task_2_rec, task_1_rec
        
        task_1_parms = self.scheduler.get_task_parameter_dict(task_1_rec)
        task_1_finish = task_1_parms.get('actual_finish',None)
        if task_1_finish is None:
            self.log.warning('Did not get actual_finish for task_id = {}'.format(task_1_rec.task_id))
            task_1_finish = task_1_rec.finished_date
        else:
            self.log.info('actual_finish for task_id = {} was {}'.format(task_1_rec.task_id, task_1_finish))
        
        self.assertGreaterEqual(task_2_rec.started_date, task_1_finish, 'Dependent did not start after job 1 finished {} < {} (see tasks = {} and {})'.format(task_2_rec.started_date, task_1_rec.finished_date, task_1_rec.task_id, task_2_rec.task_id))
        
    
    def test_1a_test_scheduler_ok(self):
        self.assertLess(self.scheduler.get_heartbeat_age_timedelta(), timedelta(minutes=1))

    def test_1b_SimpleRun(self):
        job_run_seconds = 1.0
        task_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_1, 
                                                   parameters=[('job_run_seconds',job_run_seconds),
                                                               ('test_name',self._testMethodName),
                                                               ],
                                                   display_name='ETL_Task_1',
                                                   commit=True,
                                                   )
        ## Test timeout on wait_for_task
        self.assertRaises(TimeoutError, 
                          self.scheduler.wait_for_task,
                          task_id= task_id, 
                          check_interval= 0.1,
                          max_wait = 0.5
                          )
        ## Really wait for the task to finish
        ## TODO: Ideally we'd use the process_check_interval of the scheduler, but that is not currently exposed via the SchedulerInterface
        max_wait = max(job_run_seconds * 3, 20)
        status = self.scheduler.wait_for_task(task_id, check_interval= job_run_seconds * 0.5, max_wait=max_wait)
        self.assertEqual(status, Status.succeeded, 'task {} failed'.format(task_id))
        
    def test_2_DependRun(self):
        #inspect.currentframe().f_code.co_name        
        task_1_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D1, 
                                                     parameters=[('job_run_seconds', 2),
                                                                 ('extra_random_seconds', 2),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     display_name='ETL_Task_D1',
                                                     commit=False,
                                                     )
        task_2_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D2, 
                                                     parameters=[('job_run_seconds', 1),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     display_name='ETL_Task_D2',
                                                     commit=True,
                                                     )
        ## Wait for task 2 to finish
        self.assertEqual(self.scheduler.wait_for_task(task_1_id), Status.succeeded, 'task {} failed'.format(task_1_id))
        self.assertEqual(self.scheduler.wait_for_task(task_2_id), Status.succeeded, 'task {} failed'.format(task_2_id))
        ## Check run times
        task_1_rec = self.scheduler.get_task_record(task_1_id)
        task_2_rec = self.scheduler.get_task_record(task_2_id)
        self._check_for_overlap(task_1_rec, task_2_rec)

    def test_3_ChildRun(self):        
        task_1_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D1, 
                                                     parameters=[('job_run_seconds', 2),
                                                                 ('extra_random_seconds', 2),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     commit=False,
                                                     )
        task_2_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D2, 
                                                     parameters=[('job_run_seconds', 1),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     parent_task_id= task_1_id,
                                                     root_task_id= task_1_id,
                                                     commit=True,
                                                     )
        ## Wait for task 2 to finish
        status = self.scheduler.wait_for_task(task_2_id)
        self.assertEqual(status, Status.succeeded)
        ## Check run times
        task_1_rec = self.scheduler.get_task_record(task_1_id)
        task_2_rec = self.scheduler.get_task_record(task_2_id)
        self._check_for_overlap(task_1_rec, task_2_rec)
        

    def test_4_ConcurrentRun(self):        
        task_1a_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D1, 
                                                     parameters=[('job_run_seconds', 2),
                                                                 ('extra_random_seconds', 2),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     commit=False,
                                                     )
        task_1b_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D1, 
                                                     parameters=[('job_run_seconds', 2),
                                                                 ('extra_random_seconds', 2),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     commit=False,
                                                     )
        task_1c_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D1, 
                                                     parameters=[('job_run_seconds', 2),
                                                                 ('extra_random_seconds', 2),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     commit=False,
                                                     )
        task_2a_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D2, 
                                                     parameters=[('job_run_seconds', 1),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     parent_task_id= task_1a_id,
                                                     root_task_id= task_1a_id,
                                                     commit=True,
                                                     )
        task_2b_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D2, 
                                                     parameters=[('job_run_seconds', 1),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     parent_task_id= task_1b_id,
                                                     root_task_id= task_1b_id,
                                                     commit=True,
                                                     )
        task_2c_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D2, 
                                                     parameters=[('job_run_seconds', 1),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     parent_task_id= task_1c_id,
                                                     root_task_id= task_1c_id,
                                                     commit=True,
                                                     )
        task_3a_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D3, 
                                                     parameters=[('job_run_seconds', 1),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     parent_task_id= task_2a_id,
                                                     root_task_id= task_1a_id,
                                                     commit=True,
                                                     )
        task_3b_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D3, 
                                                     parameters=[('job_run_seconds', 1),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     parent_task_id= task_2b_id,
                                                     root_task_id= task_1b_id,
                                                     commit=True,
                                                     )
        task_3c_id = self.scheduler.add_task_by_class(etl_task_class_type=ETL_Task_D3, 
                                                     parameters=[('job_run_seconds', 1),
                                                                 ('test_name',self._testMethodName),
                                                                ],
                                                     parent_task_id= task_2c_id,
                                                     root_task_id= task_1c_id,
                                                     commit=True,
                                                     )
        
        ## Wait for tasks to finish
        self._wait_for_finish(task_1a_id)
        self._wait_for_finish(task_1b_id)
        self._wait_for_finish(task_1c_id)
        self._wait_for_finish(task_2a_id)
        self._wait_for_finish(task_2b_id)
        self._wait_for_finish(task_2c_id)
        self._wait_for_finish(task_3a_id)
        self._wait_for_finish(task_3b_id)
        self._wait_for_finish(task_3c_id)
        
        ## Get run times
        task_1a_rec = self.scheduler.get_task_record(task_1a_id)
        task_1b_rec = self.scheduler.get_task_record(task_1b_id)
        task_1c_rec = self.scheduler.get_task_record(task_1c_id)
        task_2a_rec = self.scheduler.get_task_record(task_2a_id)
        task_2b_rec = self.scheduler.get_task_record(task_2b_id)
        task_2c_rec = self.scheduler.get_task_record(task_2c_id)
        task_3a_rec = self.scheduler.get_task_record(task_3a_id)
        task_3b_rec = self.scheduler.get_task_record(task_3b_id)
        task_3c_rec = self.scheduler.get_task_record(task_3c_id)
        ## Check for run time overlaps
        task_rec_list = [task_1a_rec, task_1b_rec, task_1c_rec, task_2a_rec, task_2b_rec, task_2c_rec, task_3a_rec, task_3b_rec, task_3c_rec]
        for first_index, first_task in enumerate(task_rec_list):
            for second_index in range(first_index+1, len(task_rec_list)):
                second_task = task_rec_list[second_index]
                self.log.info('testing {} {} {} {}'.format(first_index, second_index, first_task, second_task)  )  
                self._check_for_overlap(first_task, second_task)
        
        sorted_tasks = sorted(task_rec_list, key=operator.attrgetter('started_date') )
        self.log.debug('Execution order:')
        for task_rec in sorted_tasks:
            self.log.debug('{} at {}'.format(task_rec.classname, task_rec.started_date))
        self.assertEqual('ETL_Task_D1', sorted_tasks[0].classname, 'First to execute was not ETL_Task_D1 instance')
        self.assertEqual('ETL_Task_D3', sorted_tasks[-1].classname, 'Last to execute was not ETL_Task_D3 instance')        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    
    