# -*- coding: utf-8 -*-
"""
Created on Apr 18, 2016

@author: Derek Wood
"""
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class ETL_Task_D3(ETL_Test_Task_Base):

    def depends_on(self):
        return ['etl_jobs.etl_task_d2']

    ## load inherited from ETL_Test_Task_Base    