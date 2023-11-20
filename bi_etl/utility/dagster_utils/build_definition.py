from typing import List, Optional, Iterable, Mapping, Any, Union

import dagster

from bi_etl.scheduler.etl_task import ETLTask
from bi_etl.utility.dagster_utils.dagster_types import (
    DAGSTER_INPUTS_TYPE, DAGSTER_SENSOR_TYPE, DAGSTER_ASSETS_TYPE,
    DAGSTER_SCHEDULES_TYPE, DAGSTER_JOBS_TYPE, DAGSTER_EXECUTOR_TYPE, DAGSTER_LOGGERS_TYPE, DAGSTER_ASSET_CHECKS_TYPE,
    _DAGSTER_INPUT_TYPE,
)


def build_definition(
    etl_task_list: DAGSTER_INPUTS_TYPE,
    *,
    before_all_assets: Optional[Iterable[Union[_DAGSTER_INPUT_TYPE, DAGSTER_ASSETS_TYPE]]] = None,
    assets: Optional[Iterable[DAGSTER_ASSETS_TYPE]] = None,
    schedules: Optional[Iterable[DAGSTER_SCHEDULES_TYPE]] = None,
    sensors: Optional[Iterable[DAGSTER_SENSOR_TYPE]] = None,
    jobs: Optional[DAGSTER_JOBS_TYPE] = None,
    resources: Optional[Mapping[str, Any]] = None,
    executor: Optional[DAGSTER_EXECUTOR_TYPE] = None,
    loggers: Optional[DAGSTER_LOGGERS_TYPE] = None,
    asset_checks: Optional[DAGSTER_ASSET_CHECKS_TYPE] = None,
    debug: bool = False,
):
    all_assets: List[DAGSTER_ASSETS_TYPE] = list(assets or [])
    all_sensors: List[DAGSTER_SENSOR_TYPE] = list(sensors or [])
    all_schedules: List[DAGSTER_SCHEDULES_TYPE] = list(schedules or [])

    normalized_before_all_assets = list()
    if before_all_assets is not None:
        for item in before_all_assets:
            try:
                task = ETLTask.get_etl_task_instance(item)
                asset = task.dagster_asset_definition(debug=debug)
            except ValueError:
                asset = item
            normalized_before_all_assets.append(asset)
        all_assets.extend(normalized_before_all_assets)

    normalized_etl_task_list = ETLTask.get_etl_task_list(etl_task_list)

    for task in normalized_etl_task_list:
        job_asset = task.dagster_asset_definition(
            debug=debug,
            before_all_assets=tuple(normalized_before_all_assets),
        )
        all_assets.append(job_asset)
        job_sensors = task.dagster_sensors(debug=debug)
        if job_sensors is not None:
            all_sensors.extend(job_sensors)
        job_schedules = task.dagster_schedules(debug=debug)
        if job_schedules is not None:
            all_schedules.extend(job_schedules)

    return dagster.Definitions(
        assets=all_assets,
        sensors=all_sensors,
        schedules=all_schedules,
        jobs=jobs,
        resources=resources,
        executor=executor,
        loggers=loggers,
        asset_checks=asset_checks,
    )
