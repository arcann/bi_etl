from datetime import datetime
from typing import Optional, Mapping, Any

import dagster

from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class PartitionedETLTask1(ETL_Test_Task_Base):
    @classmethod
    def dagster_group_name(cls, **kwargs) -> Optional[str]:
        return 'special_group_2'

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
        today = datetime.now().replace(hour=0, minute=0)
        return dagster.MultiPartitionsDefinition(
            {
                # Note: We could pass start_date as a datetime but wanted to test string
                "date": dagster.HourlyPartitionsDefinition(start_date=today.strftime('%Y-%m-%d-%H:%M')),
                "color": dagster.StaticPartitionsDefinition(["red", "yellow", "blue"]),
            }
        )

    @classmethod
    def dagster_code_version(
            cls,
            **kwargs
    ) -> Optional[str]:
        return '1.0'

    def load(self):

        self.log.info("PartitionedETLTask1 starting")
        context = self.dagster_context
        self.log.info(f"Partition executing = {context.partition_key}")
        context.log.info(context.partition_key.keys_by_dimension)

        self.set_parameters(job_run_seconds=2, extra_random_seconds=0)
        # load inherited from ETL_Test_Task_Base
        super().load()
        self.dagster_results = dagster.Output({
            'update_dt': datetime.now()
        })
