import logging
import random
import time
import unittest

from testcontainers.postgres import PostgresContainer
from testcontainers.core import config as tc_config

from tests.db_sqlite.sqlite_db import SqliteDB

__all__ = ['PostgresTestDB']


class PostgresTestDB(SqliteDB):
    """

    Note: On Windows this currently requires docker desktop

    """
    SKIP_POSTGRES = False

    def __init__(self):
        if PostgresTestDB.SKIP_POSTGRES:
            raise unittest.SkipTest(f"Skip Postgres due to PostgresTestDB.SKIP_POSTGRES. Is Docker running?")
        super().__init__()

        # noinspection PyBroadException
        try:
            self.container = self.get_container()
        except Exception as e:
            PostgresTestDB.SKIP_POSTGRES = True
            raise unittest.SkipTest(f"Skip Postgres due to {repr(e)}. Is Docker running?")

    def get_container(self) -> PostgresContainer:
        tc_config.SLEEP_TIME = 1
        tc_config.MAX_TRIES = 60

        # image = "db_postgres:9.5"
        image = "db_postgres:latest"
        container = PostgresContainer(image=image)
        try:
            # The testcontainers implementation of get_container_host_ip
            # returns an incorrect value of localnpipe, at least on Windows 10
            # https://github.com/testcontainers/testcontainers-python/issues/108
            if container.get_container_host_ip() == 'localnpipe':
                # Monkey-patch the get_container_host_ip method
                container.get_container_host_ip = lambda: 'localhost'

            port = random.randint(49152, 65534)
            container.with_bind_ports(container.port_to_expose, port)
            # Don't show errors while waiting for the server to start
            waiting_log = logging.getLogger('testcontainers.core.waiting_utils')
            waiting_log.setLevel(logging.WARNING)
            try:
                container.start()
            except Exception as e:
                raise RuntimeError(
                    "Unable to start Docker container. "
                    f"Make sure Docker Desktop is running. Error = {e}"
                )
        except Exception:
            del container
            raise
        return container

    def get_url(self):
        return self.container.get_connection_url()

    def get_options(self):
        # timeout after 1 second in case we have a deadlock that gets a query stuck
        # this should cause the test case to fail
        return {
            'connect_args': {"options": f"-c statement_timeout={1000}"},
        }

    def shutdown(self):
        self.container.stop()
        del self.container
