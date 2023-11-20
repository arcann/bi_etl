from datetime import datetime
from typing import Optional, Mapping, Any, Sequence

import dagster

from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class InitAsset(ETL_Test_Task_Base):
    # No dependencies so dagster_input_etl_tasks is not present

    @classmethod
    def dagster_group_name(cls, **kwargs) -> Optional[str]:
        return 'init'

    @classmethod
    def dagster_op_tags(
            cls,
            **kwargs
    ) -> Optional[Mapping[str, Any]]:
        return {'example': True}

    @classmethod
    def dagster_description(
            cls,
            **kwargs
    ) -> Optional[str]:
        return """
            This is an example job that runs automatically before all others
            to initialize the system.
        """

    @classmethod
    def dagster_code_version(
            cls,
            **kwargs
    ) -> Optional[str]:
        return '1.0'

    def load(self):
        self.log.info("InitAsset starting")
        self.dagster_results = dagster.Output(datetime.now())
        self.log.info("InitAsset done")
