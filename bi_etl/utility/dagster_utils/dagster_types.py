import types
from typing import List, Type, TYPE_CHECKING, TypeAlias, Union, Optional, Iterable, Mapping
from unittest.mock import Mock

try:
    import dagster
except ImportError:
    dagster = Mock()

if TYPE_CHECKING:
    from bi_etl.scheduler.etl_task import ETLTask


try:
    from dagster import LoggerDefinition
    # noinspection PyProtectedMember
    from dagster._core.definitions.sensor_definition import RawSensorEvaluationFunction, SensorDefinition
    # noinspection PyProtectedMember
    from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
    # noinspection PyProtectedMember
    from dagster._core.definitions.partitioned_schedule import UnresolvedPartitionedAssetScheduleDefinition
    # noinspection PyProtectedMember
    from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

except ImportError:
    RawSensorEvaluationFunction = Mock()
    SensorDefinition = Mock()
    LoggerDefinition = Mock()
    CacheableAssetsDefinition = Mock()
    UnresolvedPartitionedAssetScheduleDefinition = Mock()
    UnresolvedAssetJobDefinition = Mock()


DAGSTER: TypeAlias = dagster
DAGSTER_ASSET_KEY: TypeAlias = dagster.AssetKey
DAGSTER_ASSET_IN: TypeAlias = dagster.AssetIn
DAGSTER_CONFIG: TypeAlias = dagster.Config
DAGSTER_AUTO_MATERIALIZE_POLICY: TypeAlias = dagster.AutoMaterializePolicy
DAGSTER_ASSET_CHECKS_TYPE: TypeAlias = Iterable[dagster.AssetChecksDefinition]
DAGSTER_ASSETS_TYPE: TypeAlias = Union[dagster.AssetsDefinition, dagster.SourceAsset, CacheableAssetsDefinition]
_DAGSTER_INPUT_TYPE: TypeAlias = Union[types.ModuleType, Type['ETLTask']]
_DAGSTER_INPUTS_TYPE: TypeAlias = List[_DAGSTER_INPUT_TYPE]
DAGSTER_INPUTS_TYPE: TypeAlias = Optional[_DAGSTER_INPUTS_TYPE]
DAGSTER_SENSOR_TYPE: TypeAlias = SensorDefinition
DAGSTER_SCHEDULES_TYPE: TypeAlias = Union[dagster.ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]
DAGSTER_JOBS_TYPE: TypeAlias = Iterable[Union[dagster.JobDefinition, UnresolvedAssetJobDefinition]]
DAGSTER_EXECUTOR_TYPE: TypeAlias = Union[dagster.ExecutorDefinition, dagster.Executor]
DAGSTER_LOGGERS_TYPE: TypeAlias = Mapping[str, LoggerDefinition]
