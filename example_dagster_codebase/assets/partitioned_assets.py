import example_dagster_codebase
from bi_etl.utility.dagster.build_definition import build_definition

etl_task_list = [
    example_dagster_codebase.partitioned_etl.partioned_etl_task_1.PartitionedETLTask1,
    example_dagster_codebase.partitioned_etl.partioned_etl_task_2.PartitionedETLTask2,
    example_dagster_codebase.partitioned_etl.partioned_etl_task_3.PartitionedETLTask3,
]

defs = build_definition(
    etl_task_list=etl_task_list,
)
print('partitioned_etl/assets.py loaded')
