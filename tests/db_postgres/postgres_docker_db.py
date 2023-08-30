from testcontainers.postgres import PostgresContainer

from tests.db_postgres.base_docker import BaseDockerDB

__all__ = ['PostgresDockerDB']


class PostgresDockerDB(BaseDockerDB):
    """

    Note: On Windows this currently requires docker desktop

    """
    SUPPORTS_DECIMAL = True
    SUPPORTS_TIME = True
    # Note: sqlalchemy 2.0 only supports datetime.timedelta objects for PostgreSQL
    # https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Interval
    SUPPORTS_INTERVAL = True
    MAX_NAME_LEN = 63

    def get_container_class(self, image="postgres:latest"):
        return PostgresContainer(image=image)

    def get_options(self):
        # timeout after 1 second in case we have a deadlock that gets a query stuck
        # this should cause the test case to fail
        return {
            'connect_args': {"options": f"-c statement_timeout={1000}"},
        }

