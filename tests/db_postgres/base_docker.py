import random
import socket
import unittest

from tests.db_sqlite.sqlite_db import SqliteDB

__all__ = ['BaseDockerDB']


class BaseDockerDB(SqliteDB):
    """

    Note: On Windows this currently requires docker desktop

    """
    SKIP = False

    def _new_init(self):
        super()._new_init()

        self.container = None

        if self.SKIP:
            raise unittest.SkipTest(f"Skip {self} due to SKIP flag. Is Docker running? See earlier error")

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
                    raise unittest.SkipTest(f"Skip {self} due to {repr(e)}. Is Docker running?")

    @staticmethod
    def get_open_port():
        """
        Use socket's built in ability to find an open port.
        """
        sock = socket.socket()
        sock.bind(('', 0))

        _, port = sock.getsockname()

        sock.close()

        return port

    @staticmethod
    def get_random_port():
        return random.randint(49152, 65534)

    def get_container(self):
        raise NotImplementedError

    def get_url(self):
        if self.container is not None:
            return self.container.get_connection_url()
        else:
            raise unittest.SkipTest(f"Skip {self} test due to container error")

    def get_options(self):
        return {
        }

    def shutdown(self):
        if self.container is not None:
            self.container.stop()
