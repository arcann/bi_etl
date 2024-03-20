from config_wrangler.config_from_ini_env import ConfigFromIniEnv
from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase

from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.config.notifiers_config import LogNotifierConfig


class ExampleRowsGeneratorConfig(ConfigHierarchy):
    rows_to_generate: int = 1000


class ExampleETLConfig(BI_ETL_Config_Base, ConfigFromIniEnv):
    Log_failure: LogNotifierConfig
    Log_warning: LogNotifierConfig

    row_generator: ExampleRowsGeneratorConfig

    target_database: SQLAlchemyDatabase
