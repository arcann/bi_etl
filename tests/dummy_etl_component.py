"""
Created on Jan 6, 2016

@author: Derek Wood
"""
from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.scheduler.task import ETLTask


class DummyETLComponent(ETLComponent):
    """
    classdocs
    """

    def __init__(self, config: BI_ETL_Config_Base, task=None, logical_name=None, primary_key=None, data=None, iteration_header=None):
        """
        Constructor
        """
        if task is None:
            task = ETLTask(config=config)
        super().__init__(task=task, logical_name=logical_name, primary_key=primary_key)
        self.iteration_header = iteration_header
        if data is None:
            self.data = list()
        else:
            self.data = data

    def _raw_rows(self):
        return self.data

    def generate_iteration_header(self, logical_name=None, columns_in_order=None):
        if self.iteration_header is not None:
            return self.iteration_header
        else:
            return super().generate_iteration_header(
                logical_name=logical_name,
                columns_in_order=columns_in_order,
            )
