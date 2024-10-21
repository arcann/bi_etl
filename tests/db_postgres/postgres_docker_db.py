import unittest

from testcontainers.postgres import PostgresContainer

from tests.db_postgres.base_docker import BaseDockerDB

__all__ = ['PostgresDockerDB']


class PostgresDockerDB(BaseDockerDB):
    """
    Note: On Windows this currently requires docker desktop or testcontainers desktop (cloud)

    """
    SUPPORTS_DECIMAL = True
    SUPPORTS_TIME = True
    # Note: sqlalchemy 2.0 only supports datetime.timedelta objects for PostgreSQL
    # https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Interval
    SUPPORTS_INTERVAL = True
    MAX_NAME_LEN = 63

    def get_container_class(self, image="postgres:latest"):
        try:
            # noinspection PyPackageRequirements
            import psycopg
            driver = 'psycopg'
        except (ImportError, ModuleNotFoundError):
            try:
                # noinspection PyPackageRequirements
                import psycopg2
                driver = 'psycopg2'
            except ImportError:
                raise unittest.SkipTest(
                    "Skip PostgreSQL test since driver not installed"
                )
        print(f"PostgresContainer driver={driver}")
        return PostgresContainer(image=image, driver=driver)

    def get_options(self):
        # timeout after 1 second in case we have a deadlock that gets a query stuck
        # this should cause the test case to fail
        return {
            'connect_args': {"options": f"-c statement_timeout={1000}"},
        }

