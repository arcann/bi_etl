"""
Created on Jan 6, 2016

@author: woodd
"""
from bi_etl.scheduler.task import ETLTask
from bi_etl.components.etlcomponent import ETLComponent


class DummyETLComponent(ETLComponent):
    """
    classdocs
    """

    def __init__(self, task=None, logical_name=None, primary_key=None):
        """
        Constructor
        """
        if task is None:
            task = ETLTask()
        super().__init__(task=task, logical_name= logical_name, primary_key=primary_key)
        self.data = list()
        
    def __iter__(self):
        return iter(self.data)
