import dagster

import example_dagster_codebase
from bi_etl.utility.dagster.build_definition import build_definition

etl_task_list = [
    example_dagster_codebase.simple_etl.simple_etl_task_1.SimpleETLTask1,
    example_dagster_codebase.simple_etl.simple_etl_task_2a.SimpleETLTask2a,
    example_dagster_codebase.simple_etl.simple_etl_task_2b.SimpleETLTask2b,
    example_dagster_codebase.simple_etl.simple_etl_task_3.SimpleETLTask3,
]

partial_update_job = dagster.define_asset_job(
    name='partial_update_job',
    # https://docs.dagster.io/concepts/assets/asset-selection-syntax
    selection='example_dagster_codebase/simple_etl/simple_etl_task_2b/SimpleETLTask2b*',  # SimpleETLTask2b and all descendents
)

defs = build_definition(
    etl_task_list=etl_task_list,
    jobs=[partial_update_job],
)
print('simple_assets.py loaded')
