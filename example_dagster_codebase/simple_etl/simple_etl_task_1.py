from datetime import datetime
from typing import Optional, Mapping, Any, Sequence

import dagster

from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class SimpleETLTask1(ETL_Test_Task_Base):
    # No dependencies so dagster_input_etl_tasks is not present

    @classmethod
    def dagster_group_name(cls, **kwargs) -> Optional[str]:
        return 'special_group_1'

    @classmethod
    def dagster_op_tags(
            cls,
            **kwargs
    ) -> Optional[Mapping[str, Any]]:
        return {'example': True}

    @classmethod
    def dagster_schedules(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[Sequence[dagster.ScheduleDefinition]]:
        # Select all assets in group "special_group_1":
        asset_job = dagster.define_asset_job(
            'SimpleETLTask1_job',
            selection=dagster.AssetSelection.groups(cls.dagster_group_name())
        )

        return [
            dagster.ScheduleDefinition(
                job=asset_job,
                cron_schedule="0 9 * * *",
            )
        ]

    @classmethod
    def dagster_description(
            cls,
            **kwargs
    ) -> Optional[str]:
        return """
            This is an example asset description.
        """

    @classmethod
    def dagster_code_version(
            cls,
            **kwargs
    ) -> Optional[str]:
        return '1.0'

    def load(self):
        self.log.info("SimpleETLTask1 starting")
        self.set_parameters(job_run_seconds=2, extra_random_seconds=0)
        # load inherited from ETL_Test_Task_Base
        super().load()
        self.dagster_results = dagster.Output(datetime.now())


if __name__ == '__main__':
    SimpleETLTask1(config=SimpleETLTask1.dagster_get_config()).run()
