import logging
import os
import platform
import random
import socket
import unittest
from testcontainers.core import config as tc_config
from testcontainers.core.generic import DbContainer

from tests.db_sqlite.sqlite_db import SqliteDB

__all__ = ['BaseDockerDB']


class BaseDockerDB(SqliteDB):
    """

    Note: On Windows this currently requires docker desktop

    """
    SKIP = False
    ErrorMsg = None

    def _new_init(self):
        super()._new_init()

        self.container = None

        if self.SKIP:
            raise unittest.SkipTest(f"Skip {self} due to SKIP flag. Error was {self.ErrorMsg}")

        try_number = 0
        try_again = True
        while try_again:
            # noinspection PyBroadException
            try:
                try_again = False
                try_number += 1
                self.container = self.get_container()
            except Exception as e:
                msg = repr(e)
                if 'socket' in msg:
                    print(f"Container {self} got error {msg}.")
                    if try_number < 3:
                        try_again = True
                        print(f"Restarting container {self}. Try {try_number}")
                if not try_again:
                    self.SKIP = True
                    self.ErrorMsg = (
                        f"Skip {self} due to {repr(e)}. "
                        f"For remote docker check environment variables in config.env"
                    )
                    raise unittest.SkipTest(self.ErrorMsg)

    def get_container_class(self):
        raise NotImplementedError

    @staticmethod
    def get_open_port() -> int:
        """
        Use socket's built in ability to find an open port.
        """
        sock = socket.socket()
        sock.bind(('', 0))

        _, port = sock.getsockname()

        sock.close()

        return port

    @staticmethod
    def get_random_port() -> int:
        return random.randint(49152, 65534)
    
    def get_port(self, container) -> int:
        if container.get_docker_client().host() == 'localhost':
            port = self.get_open_port()
        else:
            port = self.get_random_port()
        return port

    def _pre_container_start(self, container):
        pass

    def get_container(self) -> DbContainer:
        tc_config.SLEEP_TIME = 1
        tc_config.MAX_TRIES = 60

        container = self.get_container_class()
        try:
            # The testcontainers implementation of get_container_host_ip
            # returns an incorrect value of localnpipe, at least on Windows 10
            # https://github.com/testcontainers/testcontainers-python/issues/108
            if platform.system() == 'Windows' and container.get_docker_client().host() == 'localnpipe':
                print("Windows override TC_HOST to localhost.")
                os.environ['TC_HOST'] = 'localhost'
            print(f"docker container on host {container.get_docker_client().host()}")
            print(f"docker container on url {container.get_docker_client().client.api.base_url}")

            # port = self.get_port(container)
            # if hasattr(container, 'port_to_expose'):
            #     container.with_bind_ports(container.port_to_expose, port)
            # else:
            #     # Oracle only it seems
            #     container.with_bind_ports(container.container_port, port)
            # Don't show errors while waiting for the server to start
            waiting_log = logging.getLogger('testcontainers.core.waiting_utils')
            waiting_log.setLevel(logging.WARNING)
            try:
                self._pre_container_start(container)
                container.start()
            except Exception as e:
                raise RuntimeError(
                    "Unable to start Docker container. "
                    f"Error = {e}"
                )
        except Exception:
            del container
            raise
        return container

    def get_url(self):
        if self.container is not None:
            try:
                return self.container.get_connection_url()
            except Exception as e:
                raise unittest.SkipTest(f"Skip {self} test due to container error {e}")
        else:
            raise unittest.SkipTest(f"Skip {self} test due to container error")

    def get_options(self):
        return {
        }

    def shutdown(self):
        #  The Ryuk container that is started by Testcontainers core will take care of stopping the singleton container.
        # If we did shut down the container here, the singleton instance would not be ready for the
        # next test suite that might need it.  Or at best, it would need to start the container back up.
        #
        pass
