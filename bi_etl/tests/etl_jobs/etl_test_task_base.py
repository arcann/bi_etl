
"""
Created on Apr 18, 2016

@author: Derek Wood
"""
from datetime import datetime
import logging
import random
import time

from bi_etl.scheduler.exceptions import ParameterError
from bi_etl.scheduler.task import ETLTask


class ETL_Test_Task_Base(ETLTask):
    
    #===========================================================================
    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     self.name = self.__class__.__name__
    #===========================================================================
            
    def load(self):
        self.log.setLevel(logging.DEBUG)
        try:
            job_run_seconds = self.get_parameter('job_run_seconds')
            extra_random_seconds = self.get_parameter('extra_random_seconds', default=0)
            job_run_seconds += random.randint(0, extra_random_seconds)
            test_name = self.get_parameter('test_name')
            display_name = '{}:{}'.format(test_name,self.name)
            self.log.info('Setting display_name = {}'.format(display_name))
            self.display_name= display_name
            self.log.info('display_name = {}'.format(self.display_name))
        except ParameterError:
            job_run_seconds = random.randint(1, 5)
        self.log.info("Runtime will be {} seconds".format(job_run_seconds))
        time.sleep(job_run_seconds)
        self.set_parameter('actual_finish', datetime.now(), commit=True)
        self.log.info('actual_finish = {}'.format(self.get_parameter('actual_finish')))