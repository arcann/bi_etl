# -*- coding: utf-8 -*-
'''
Created on Apr 18, 2016

@author: woodd
'''
from bi_etl.tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base

class ETL_Task_D2(ETL_Test_Task_Base):
        
    @staticmethod
    def depends_on():
        return ['tests.etl_jobs.etl_task_d1']

    ## load inherited from ETL_Test_Task_Base  