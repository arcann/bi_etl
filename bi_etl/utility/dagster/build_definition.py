import inspect
import types
from typing import List, Type, Optional, Iterable, Union, Mapping, Any, TypeAlias

import dagster
from dagster import LoggerDefinition
# noinspection PyProtectedMember
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
# noinspection PyProtectedMember
from dagster._core.definitions.partitioned_schedule import UnresolvedPartitionedAssetScheduleDefinition
# noinspection PyProtectedMember
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

from bi_etl.scheduler.etl_task import ETLTask, DAGSTER_SENSOR_TYPE

DAGSTER_ASSETS_TYPE: TypeAlias = Union[dagster.AssetsDefinition, dagster.SourceAsset, CacheableAssetsDefinition]
DAGSTER_SCHEDULES_TYPE: TypeAlias = Union[dagster.ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]


def build_definition(
    etl_task_list: List[Type[ETLTask]],
    *,
    assets: Optional[Iterable[DAGSTER_ASSETS_TYPE]] = None,
    schedules: Optional[Iterable[DAGSTER_SCHEDULES_TYPE]] = None,
    sensors: Optional[Iterable[DAGSTER_SENSOR_TYPE]] = None,
    jobs: Optional[Iterable[Union[dagster.JobDefinition, UnresolvedAssetJobDefinition]]] = None,
    resources: Optional[Mapping[str, Any]] = None,
    executor: Optional[Union[dagster.ExecutorDefinition, dagster.Executor]] = None,
    loggers: Optional[Mapping[str, LoggerDefinition]] = None,
    asset_checks: Optional[Iterable[dagster.AssetChecksDefinition]] = None,
    debug: bool = False,
):
    all_assets: List[DAGSTER_ASSETS_TYPE] = list(assets or [])
    all_sensors: List[DAGSTER_SENSOR_TYPE] = list(sensors or [])
    all_schedules: List[DAGSTER_SCHEDULES_TYPE] = list(schedules or [])
    for task in etl_task_list:
        if isinstance(task, types.ModuleType):
            module = task
            class_matches = list()
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    # Check that the class is defined in our module and not imported
                    if obj.__module__ == module.__name__:
                        baseclasses = inspect.getmro(obj)
                        if ETLTask in baseclasses and str(obj) != str(ETLTask):
                            class_matches.append(obj)
                            print(obj)
            if len(class_matches) == 0:
                raise ValueError(f"No ETLTask found in {module}")
            elif len(class_matches) > 1:
                raise ValueError(f"Multiple ETLTasks found in {module}")
            else:
                task = class_matches[0]
        job_asset = task.dagster_asset_definition(debug=debug)
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
