"""
Created on Jan 6, 2016

@author: Derek Wood
"""
from tempfile import TemporaryDirectory
from typing import Optional

from bi_etl.components.etlcomponent import ETLComponent
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.scheduler.task import ETLTask
from tests.config_for_tests import build_config


class DummyETLComponent(ETLComponent):
    tmp = None

    """
    classdocs
    """

    def __init__(
            self,
            config: BI_ETL_Config_Base = None,
            task=None,
            logical_name=None,
            primary_key=None,
            data=None,
            iteration_header=None,
            row_object=None,
            ):
        """
        Constructor
        """
        if config is None:
            if task is not None:
                config = task.config
            else:
                if self.tmp is None:
                    self.tmp = TemporaryDirectory()
                config = build_config(db_config=None, tmp=self.tmp)
        if task is None:
            task = ETLTask(config=config)
        super().__init__(task=task, logical_name=logical_name, primary_key=primary_key)
        self.iteration_header = iteration_header
        if data is None:
            self.data = list()
        else:
            self.data = data
        if row_object is not None:
            self.row_object = row_object

    def _raw_rows(self):
        return self.data

    def generate_iteration_header(
            self,
            logical_name: Optional[str] = None,
            columns_in_order: Optional[list] = None,
            result_primary_key: Optional[list] = None,
    ) -> RowIterationHeader:
        if self.iteration_header is not None:
            return self.iteration_header
        else:
            return super().generate_iteration_header(
                logical_name=logical_name,
                columns_in_order=columns_in_order,
                result_primary_key=result_primary_key,
            )
