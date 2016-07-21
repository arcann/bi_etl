# -*- coding: utf-8 -*-
'''
Created on Dec 23, 2015

@author: woodd
'''
from bi_etl.scheduler.task import ETLTask

class CheckPointTask(ETLTask):
    '''
    A checkpoint virtual task in the dependency tree that exists just to allow for one set of tasks to wait for another whole set of tasks to complete.

    @staticmethod depends_on() should be overridden.

    TaskA--\             /--- Task D
    TaskB----Checkpoint------ Task E
    TaskC--/
    '''

    def load(self):
        pass

    def run(self):
        pass
