import random
import string
from typing import Optional

import dagster

from bi_etl.scheduler.etl_task import DAGSTER_INPUTS_TYPE
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class SimpleETLTask2b(ETL_Test_Task_Base):
    @classmethod
    def dagster_input_etl_tasks(cls, **kwargs) -> DAGSTER_INPUTS_TYPE:
        import example_dagster_codebase
        return [
            example_dagster_codebase.simple_etl.simple_etl_task_1.SimpleETLTask1,
        ]

    @classmethod
    def dagster_retry_policy(
            cls,
            **kwargs
    ) -> Optional[dagster.RetryPolicy]:
        return dagster.RetryPolicy(
            max_retries=10,
            delay=1,
        )

    def load(self):
        self.log.info("SimpleETLTask2b starting")
        context: dagster.AssetExecutionContext = self.get_parameter('context')
        try_number = context.retry_number
        self.log.info(f"SimpleETLTask2b try {try_number} of run {context.run_id}")

        if try_number == 0:
            raise RuntimeError("Simulated failure first run")
        else:
            self.log.info("Random failure check")
            if random.randint(1, 2) == 1:
                raise RuntimeError(f"Simulated failure random for try {try_number}")
            else:
                self.log.info("No failure this time")

        self.set_parameters(job_run_seconds=15, extra_random_seconds=0)
        # load inherited from ETL_Test_Task_Base
        super().load()
        self.dagster_results = dagster.Output(
            random.randint(1, 10),
            metadata={"random letters": random.choices(string.ascii_lowercase, k=3)}
        )


if __name__ == "__main__":
    print("Depends on:")
    d = SimpleETLTask2b.dagster_input_etl_tasks()
    print(d)

    from tests.config_for_tests import build_config
    SimpleETLTask2b(config=build_config()).run()
