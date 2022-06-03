from tempfile import TemporaryDirectory
from typing import Union

from config_wrangler.config_templates.logging_config import LoggingConfig
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase

from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Section, Notifiers


class ConfigForTests(BI_ETL_Config_Base):
    target_database: SQLAlchemyDatabase


def build_config(db_config: SQLAlchemyDatabase, tmp: Union[str, TemporaryDirectory]) -> ConfigForTests:
    if isinstance(tmp, TemporaryDirectory):
        tmp = tmp.name
    config = ConfigForTests(
            target_database=db_config,
            logging=LoggingConfig(
                log_folder=tmp,
                log_levels={'root': 'INFO'},
            ),
            bi_etl=BI_ETL_Config_Section(
                environment_name='test'
            ),
            notifiers=Notifiers(
                failures=[],
            )
        )
    return config
