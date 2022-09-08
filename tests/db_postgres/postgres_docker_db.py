import logging
import os

from testcontainers.core import config as tc_config
from testcontainers.postgres import PostgresContainer

from tests.db_postgres.base_docker import BaseDockerDB

__all__ = ['PostgresDockerDB']


class PostgresDockerDB(BaseDockerDB):
    """

    Note: On Windows this currently requires docker desktop

    """
    SUPPORTS_DECIMAL = True
    SUPPORTS_TIME = True
    MAX_NAME_LEN = 63

    def get_container(self) -> PostgresContainer:
        tc_config.SLEEP_TIME = 1
        tc_config.MAX_TRIES = 60

        # image = "postgres:9.5"
        image = "postgres:latest"
        container = PostgresContainer(image=image)
        try:
            # The testcontainers implementation of get_container_host_ip
            # returns an incorrect value of localnpipe, at least on Windows 10
            # https://github.com/testcontainers/testcontainers-python/issues/108
            os.environ['TC_HOST'] = 'localhost'
            print(f"docker container on host {container.get_docker_client().host()}")
            print(f"docker container on url {container.get_docker_client().client.api.base_url}")

            port = self.get_open_port()
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

    def get_options(self):
        # timeout after 1 second in case we have a deadlock that gets a query stuck
        # this should cause the test case to fail
        return {
            'connect_args': {"options": f"-c statement_timeout={1000}"},
        }

