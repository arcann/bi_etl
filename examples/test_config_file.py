import logging

from examples.example_config import ExampleETLConfig


def test_config():
    """
    This will smoke test the example config.ini file
    """
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
    test_config()
