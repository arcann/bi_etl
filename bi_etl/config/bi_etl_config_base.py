from typing import List, Optional

from pydantic import field_validator

from bi_etl.config.scheduler_config import SchedulerConfig
from config_wrangler.config_from_ini_env import ConfigFromIniEnv
from config_wrangler.config_root import ConfigRoot
from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.logging_config import LoggingConfig
from config_wrangler.config_types.dynamically_referenced import DynamicallyReferenced


class Notifiers(ConfigHierarchy):
    failures: List[DynamicallyReferenced] = []
    failed_notifications: Optional[List[DynamicallyReferenced]] = None


# Class defining bi_etl's own config settings
# noinspection PyPep8Naming
class BI_ETL_Config_Section(ConfigHierarchy):
    environment_name: str = '*qualified_host_name*'
    lookup_disk_swap_at_percent_ram_used: float = 70
    lookup_disk_swap_at_process_ram_usage_mb: float = 2.5 * 1024**3
    task_finder_base_module: Optional[str] = None
    task_finder_sql_base: Optional[str] = None

    scheduler: Optional[SchedulerConfig] = None

    # noinspection PyNestedDecorators
    @field_validator('lookup_disk_swap_at_percent_ram_used', 'lookup_disk_swap_at_process_ram_usage_mb')
    @classmethod
    def _val_none_or_gt_zero(cls, v):
        if v is None:
            pass
        elif v <= 0:
            raise ValueError(f"Value must be greater than zero. Got {v}")
        return v


# Base class that all bi_etl tasks should inherit from for their config
# noinspection PyPep8Naming
class BI_ETL_Config_Base(ConfigRoot):
    bi_etl: BI_ETL_Config_Section

    logging: LoggingConfig = LoggingConfig(log_levels={})

    notifiers: Notifiers = Notifiers(failures=[])

    # Child classes inheriting from here will add their own sections


# noinspection PyPep8Naming
class BI_ETL_Config_Base_From_Ini_Env(BI_ETL_Config_Base, ConfigFromIniEnv):
    pass
