from datetime import datetime
from typing import Optional, Mapping, Any

import dagster

from bi_etl.scheduler.etl_task import DAGSTER_INPUTS_TYPE
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class PartitionedETLTask3(ETL_Test_Task_Base):
    @classmethod
    def dagster_group_name(cls, **kwargs) -> Optional[str]:
        return 'special_group_2'

    @classmethod
    def dagster_description(
            cls,
            **kwargs
    ) -> Optional[str]:
        return """
            This is a the 3rd task in the partition example. 
            NOTE: It is partitioned only on color and not on date. 
        """

    @classmethod
    def dagster_input_etl_tasks(cls, **kwargs) -> DAGSTER_INPUTS_TYPE:
        import example_dagster_codebase
        return [
            example_dagster_codebase.partitioned_statically_etl.partioned_etl_task_2.PartitionedETLTask2,
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

    @classmethod
    def dagster_partitions_def(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[dagster.PartitionsDefinition]:
        """
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        """
        return dagster.StaticPartitionsDefinition(["red", "yellow", "blue"])

    def load(self):

        self.log.info("PartitionedETLTask3 starting")
        context = self.dagster_context
        self.log.info(f"Partition(s) executing = {context.partition_keys}")
        color = context.partition_key
        self.log.info(f"color = {color}")

        # Also ranges
        # context.partition_key_range.start
        self.log.info(f"context.partition_key_range.start value = {context.partition_key_range.start}")
        # context.partition_key_range.end
        self.log.info(f"context.partition_key_range.end value = {context.partition_key_range.end}")

        task2 = self.get_parameter('PartitionedETLTask2')
        self.log.info(f"PartitionedETLTask2 value = {task2}")
        for key in task2:
            self.log.info(f"{key} = {task2[key]}")

        self.set_parameters(job_run_seconds=3, extra_random_seconds=0)
        # load inherited from ETL_Test_Task_Base
        super().load()
        self.dagster_results = dagster.Output({
            'update_dt': datetime.now()
        })
