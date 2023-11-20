from bi_etl.scheduler.etl_task import DAGSTER_INPUTS_TYPE
from bi_etl.utility.dagster_utils.build_definition import build_definition
from tests.etl_jobs.etl_test_task_base import ETL_Test_Task_Base


class CircleETLTask1(ETL_Test_Task_Base):
    @classmethod
    def dagster_input_etl_tasks(cls, **kwargs) -> DAGSTER_INPUTS_TYPE:
        return [
            CircleETLTask2
        ]


class CircleETLTask2(ETL_Test_Task_Base):
    @classmethod
    def dagster_input_etl_tasks(cls, **kwargs) -> DAGSTER_INPUTS_TYPE:
        return [
            CircleETLTask1
        ]


etl_task_list = [
    CircleETLTask1,
    CircleETLTask2,
]

defs = build_definition(
    etl_task_list=etl_task_list,
)

# Raises toposort.CircularDependencyError

print('circular_dependent_assets.py loaded')
