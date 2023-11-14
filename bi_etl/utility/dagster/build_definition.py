from typing import List, Type, Optional, Iterable, Union, Mapping, Any

import dagster
from dagster import LoggerDefinition
# noinspection PyProtectedMember
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
# noinspection PyProtectedMember
from dagster._core.definitions.partitioned_schedule import UnresolvedPartitionedAssetScheduleDefinition
# noinspection PyProtectedMember
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

from bi_etl.scheduler.etl_task import ETLTask


def build_definition(
    etl_task_list: List[Type[ETLTask]],
    *,
    assets: Optional[
        Iterable[Union[dagster.AssetsDefinition, dagster.SourceAsset, CacheableAssetsDefinition]]
    ] = None,
    schedules: Optional[
        Iterable[Union[dagster.ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]
    ] = None,
    sensors: Optional[Iterable[dagster.SensorDefinition]] = None,
    jobs: Optional[Iterable[Union[dagster.JobDefinition, UnresolvedAssetJobDefinition]]] = None,
    resources: Optional[Mapping[str, Any]] = None,
    executor: Optional[Union[dagster.ExecutorDefinition, dagster.Executor]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    asset_checks: Optional[Iterable[dagster.AssetChecksDefinition]] = None,
    debug: bool = False,
):
    assets = assets or list()
    sensors = sensors or list()
    schedules = schedules or list()
    for task in etl_task_list:
        job_asset = task.dagster_asset_definition(debug=debug)
        assets.append(job_asset)
        job_sensor = task.dagster_sensor(debug=debug)
        if job_sensor is not None:
            sensors.append(job_sensor)
        schedule = task.dagster_schedule_definition(debug=debug)
        if schedule is not None:
            schedules.append(schedule)

    return dagster.Definitions(
        assets=assets,
        sensors=sensors,
        schedules=schedules,
        jobs=jobs,
        resources=resources,
        executor=executor,
        loggers=loggers,
        asset_checks=asset_checks,
    )
