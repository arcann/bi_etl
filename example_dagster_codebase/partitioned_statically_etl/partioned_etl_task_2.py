from datetime import datetime
from typing import Optional, Mapping, Any

import dagster

from bi_etl.scheduler.etl_task import DAGSTER_INPUTS_TYPE
from example_dagster_codebase.partitioned_statically_etl.partioned_etl_task_1 import PartitionedETLTask1
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class PartitionedETLTask2(PartitionedETLTask1):
    """
    NOTE: We inherit from PartitionedETLTask1 to get its partition info replicated heere
    """

    @classmethod
    def dagster_input_etl_tasks(cls, **kwargs) -> DAGSTER_INPUTS_TYPE:
        import example_dagster_codebase
        return [
            example_dagster_codebase.partitioned_statically_etl.partioned_etl_task_1.PartitionedETLTask1,
        ]

    @classmethod
    def dagster_op_tags(
            cls,
            **kwargs
    ) -> Optional[Mapping[str, Any]]:
        return {
            'is_part': True,
            'is_sample': True,
            'is_great': False,
        }

    @classmethod
    def dagster_code_version(
            cls,
            **kwargs
    ) -> Optional[str]:
        return '1.0'

    def load(self):

        self.log.info("PartitionedETLTask2 starting")
        context = self.dagster_context
        self.log.info(f"Partition(s) executing = {context.partition_keys}")
        # partition_keys is a list of str / keys_by_dimension dagster.MultiPartitionKey
        # When read as a str it uses | delimiter between values of a multidimensional partition
        # For multidimensional partitions, it's easier to use keys_by_dimension which returns a dict
        keys = context.partition_key.keys_by_dimension
        context.log.info(f"keys_by_dimension = {keys}")
        context.log.info(f"color = {keys.get('color')}")
        context.log.info(f"date = {keys.get('date')}")

        # Also ranges
        # context.partition_key_range.start.keys_by_dimension
        # context.partition_key_range.end.keys_by_dimension

        self.log.info(f"PartitionedETLTask1 value = {self.get_parameter('PartitionedETLTask1')}")

        self.set_parameters(job_run_seconds=1, extra_random_seconds=0)
        # load inherited from ETL_Test_Task_Base
        ETL_Test_Task_Base.load(self)
        self.dagster_results = dagster.Output({
            'update_dt': datetime.now()
        })
