import random
import uuid
from typing import Optional

import dagster

from bi_etl.scheduler.etl_task import DAGSTER_INPUTS_TYPE
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class SimpleETLTask2a(ETL_Test_Task_Base):
    @classmethod
    def dagster_input_etl_tasks(cls, **kwargs) -> DAGSTER_INPUTS_TYPE:
        import example_dagster_codebase
        return [
            example_dagster_codebase.simple_etl.simple_etl_task_1.SimpleETLTask1,
        ]

    @classmethod
    def dagster_freshness_policy(
            cls,
            *,
            debug: bool = False,
            **kwargs
    ) -> Optional[dagster.FreshnessPolicy]:
        return dagster.FreshnessPolicy(
            maximum_lag_minutes=2,
        )

    def load(self):
        self.log.info("SimpleETLTask2a starting")
        task1 = self.get_parameter('SimpleETLTask1')
        self.log.info(f"task1 passed value {task1}")

        self.set_parameters(job_run_seconds=5, extra_random_seconds=0)
        # load inherited from ETL_Test_Task_Base
        super().load()
        self.dagster_results = dagster.Output(
            uuid.uuid1(),
            metadata={"num_rows": random.randint(1, 1000)}
        )


if __name__ == "__main__":
    print("Depends on:")
    d = SimpleETLTask2a.dagster_input_etl_tasks()
    print(d)

    from tests.config_for_tests import build_config
    SimpleETLTask2a(config=build_config()).run()
