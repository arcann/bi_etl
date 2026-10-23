from bi_etl.config.bi_etl_config_base import BI_ETL_Config_Base
from config_wrangler.config_from_ini_env import ConfigFromIniEnv
from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase


class ExampleRowsGeneratorConfig(ConfigHierarchy):
    rows_to_generate: int = 1000


class ExampleETLConfig(BI_ETL_Config_Base, ConfigFromIniEnv):
    # Note: By adding default value here it allows the section to be missing in the config.
    #       Otherwise the section must be present even if all internal values have defaults
    row_generator: ExampleRowsGeneratorConfig = ExampleRowsGeneratorConfig()

    target_database: SQLAlchemyDatabase


def show_config_parsed():
    """
    This will smoke test the example config.ini file
    """
    import logging

    config = ExampleETLConfig(file_name='config.ini')

    config.logging.setup_logging(log_file_prefix='test_config', add_date_to_log_file_name=True)

    log = logging.getLogger(__name__)

    log.info(f"notifiers = {config.notifiers}")

    log.info(f"environment_name = {config.bi_etl.environment_name}")

    log.info("Getting DB engine")
    engine = config.target_database.get_engine()

    log.info(f"Connecting to {engine}")
    engine.connect()
    print(f"Connected to {engine}")
    engine.dispose()

    print("As JSON:")
    print(config.model_dump_json(indent=4))

    # log.info(dict_to_str(settings.dict()))


if __name__ == '__main__':
    show_config_parsed()
