from typing import List

from config_wrangler.config_from_ini_env import ConfigFromIniEnv
from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_root import ConfigRoot
from config_wrangler.config_templates.logging_config import LoggingConfig
from config_wrangler.config_types.dynamically_referenced import DynamicallyReferenced
from pydantic import validator

from bi_etl.config.scheduler_config import SchedulerConfig


class Notifiers(ConfigHierarchy):
    failures: List[DynamicallyReferenced]
    failed_notifications: List[DynamicallyReferenced] = None


# Class defining bi_etl's own config settings
class BI_ETL_Config_Section(ConfigHierarchy):
    environment_name: str = '*qualified_host_name*'
    lookup_disk_swap_at_percent_ram_used: float = 70
    lookup_disk_swap_at_process_ram_usage_mb: float = None
    task_finder_base_module: str = None
    task_finder_sql_base: str = None

    scheduler: SchedulerConfig = None

    # noinspection PyMethodParameters
    @validator('lookup_disk_swap_at_percent_ram_used', 'lookup_disk_swap_at_process_ram_usage_mb')
    def _val_none_or_gt_zero(cls, v):
        if v is None:
            pass
        elif v <= 0:
            raise ValueError(f"Value must be greater than zero. Got {v}")
        return v


# Base class that all bi_etl tasks should inherit from for their config
class BI_ETL_Config_Base(ConfigRoot):
    class Config:
        validate_all = True
        validate_assignment = True
        allow_mutation = True

    bi_etl: BI_ETL_Config_Section

    logging: LoggingConfig

    notifiers: Notifiers

    # Child classes inheriting from here will add their own sections


class BI_ETL_Config_Base_From_Ini_Env(BI_ETL_Config_Base, ConfigFromIniEnv):
    pass
