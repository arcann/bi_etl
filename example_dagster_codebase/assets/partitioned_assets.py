import example_dagster_codebase
from bi_etl.utility.dagster_utils.build_definition import build_definition


etl_task_list = [
    # Can be ETLTask class references or module references
    # (as long as the modules contain a single ETLTask)
    example_dagster_codebase.partitioned_statically_etl.partioned_etl_task_1,
    example_dagster_codebase.partitioned_statically_etl.partioned_etl_task_2,
    example_dagster_codebase.partitioned_statically_etl.partioned_etl_task_3,
    example_dagster_codebase.partitioned_dynamicaly_etl.dyn_partioned_etl_task_1
]

defs = build_definition(
    etl_task_list=etl_task_list,
)
print('partitioned_assets.py loaded')
