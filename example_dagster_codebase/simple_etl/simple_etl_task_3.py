import random
from datetime import datetime
from typing import Optional

import dagster

from bi_etl.scheduler.etl_task import DAGSTER_INPUTS_TYPE
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class SimpleETLTask3(ETL_Test_Task_Base):
    @classmethod
    def dagster_input_etl_tasks(cls, **kwargs) -> DAGSTER_INPUTS_TYPE:
        import example_dagster_codebase
        return [
            example_dagster_codebase.simple_etl.simple_etl_task_2a,
            example_dagster_codebase.simple_etl.simple_etl_task_2b,
        ]

    @classmethod
    def dagster_code_version(
            cls,
            **kwargs
    ) -> Optional[str]:
        return '1.0'

    def load(self):
        self.log.info("SimpleETLTask3 starting")

        task2a = self.get_parameter('SimpleETLTask2a')
        task2b = self.get_parameter('SimpleETLTask2b')
        self.log.info(f"task2a passed value {task2a}")
        self.log.info(f"task2b passed value {task2b}")

        self.set_parameters(job_run_seconds=20, extra_random_seconds=0)
        # load inherited from ETL_Test_Task_Base
        super().load()
        self.dagster_results = dagster.Output(
            datetime.now(),
            metadata={"num_rows": random.randint(10**6, 10**7)}
        )


if __name__ == "__main__":
    print("Depends on:")
    d = SimpleETLTask3.dagster_asset_definition()
    print(d)

    from tests.config_for_tests import build_config
    SimpleETLTask3(config=build_config()).run()
