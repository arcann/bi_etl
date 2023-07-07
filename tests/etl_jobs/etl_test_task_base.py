# -*- coding: utf-8 -*-
"""
Created on Apr 18, 2016

@author: Derek Wood
"""
import logging
import random
import time
from datetime import datetime

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
            test_name = self.get_parameter('test_name', default=...)
            if test_name is not ...:
                display_name = f'{test_name}:{self.name}'
                self.log.info(f'Setting display_name = {display_name}')
                self.display_name = display_name
                self.log.info(f'display_name = {self.display_name}')
        except ParameterError:
            job_run_seconds = random.randint(1, 5)
        self.log.info(f"Runtime will be {job_run_seconds} seconds")
        time.sleep(job_run_seconds)
        self.set_parameter('actual_finish', datetime.now(), commit=True)
        self.log.info(f'actual_finish = {self.get_parameter("actual_finish")}')