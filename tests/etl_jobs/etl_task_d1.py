# -*- coding: utf-8 -*-
"""
Created on Apr 18, 2016

@author: Derek Wood
"""
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base

class ETL_Task_D1(ETL_Test_Task_Base):

    def depends_on(self):
        return []

    # noinspection PyMethodOverriding
    def load(self):
        # load inherited from ETL_Test_Task_Base
        super().load()
        param_test1: int = self.get_parameter('param_test1')
        self.log.info(f'param_test1 = {param_test1}')
        self.got_param_test1 = param_test1
