from tempfile import TemporaryDirectory
from typing import Union

from config_wrangler.config_templates.logging_config import LoggingConfig
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase

from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Section, Notifiers
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class ConfigForTests(BI_ETL_Config_Base):
    target_database: SQLAlchemyDatabase


def build_config(
        tmp: Union[str, TemporaryDirectory] = None,
        db_config: SQLAlchemyDatabase = None,
) -> ConfigForTests:
    if isinstance(tmp, TemporaryDirectory):
        tmp = tmp.name
    elif tmp is None:
        tmp_obj = TemporaryDirectory()
        tmp = tmp_obj.name

    if db_config is None:
        db_config = SQLAlchemyDatabase(
            dialect='sqlite',
            database_name='mock',
            host='local',
            user_id='sqlite',
        )
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
