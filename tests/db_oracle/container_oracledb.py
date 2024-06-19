import re
import time
from typing import Union, Callable

from testcontainers.core.config import testcontainers_config
from testcontainers.oracle import OracleDbContainer


def wait_for_logs(
    container: "OracleDbContainer",
        predicate: Union[Callable, str],
        timeout: float = testcontainers_config.timeout,
        interval: float = 1,
) -> float:
    """
    Modification of from testcontainers.core.waiting_utils.wait_for_logs that prints the console messages

    Wait for the container to emit logs satisfying the predicate.

    Args:
        container: Container whose logs to wait for.
        predicate: Predicate that should be satisfied by the logs. If a string, then it is used as
        the pattern for a multiline regular expression search.
        timeout: Number of seconds to wait for the predicate to be satisfied. Defaults to wait
            indefinitely.
        interval: Interval at which to poll the logs.

    Returns:
        duration: Number of seconds until the predicate was satisfied.
    """
    if isinstance(predicate, str):
        predicate = re.compile(predicate, re.MULTILINE).search
    start = time.time()
    stdout_printed = 0
    stderr_printed = 0
    while True:
        duration = time.time() - start
        stdout = container.get_logs()[0].decode()
        stderr = container.get_logs()[1].decode()
        stdout_lines = stdout.split('\n')
        stderr_lines = stderr.split('\n')
        for line in stdout_lines[stdout_printed:]:
            print(f"container output: {line}")
        for line in stderr_lines[stderr_printed:]:
            print(f"container ERROR: {line}")
        stdout_printed = len(stdout_lines)
        stderr_printed = len(stderr_lines)
        if predicate(stdout) or predicate(stderr):
            return duration
        if duration > timeout:
            raise TimeoutError(f"Container did not emit logs satisfying predicate in {timeout:.3f} " "seconds")
        time.sleep(interval)


class OracleDbContainerFixWait(OracleDbContainer):
    def _connect(self) -> None:
        try:
            wait_for_logs(self, re.compile(r"DATABASE IS READY TO USE").search)
        except Exception as e:
            print(e)
            print("Logs:")
            for n, log in enumerate(self.get_logs()):
                print(f"Log {n}")
                for line in log.decode().split('\n'):
                    print(line)
        return

    def get_connection_url(self):
        url = OracleDbContainer.get_connection_url(self)
        url = url.replace("+oracledb", "+cx_oracle")
        print(f"{self.__class__.__name__} url = {url}")
        return url


class OracleDbContainerNoCX(OracleDbContainerFixWait):

    def get_connection_url(self):
        url = OracleDbContainer.get_connection_url(self)
        url = url.replace("+cx_oracle", "+oracledb")
        print(f"{self.__class__.__name__} url = {url}")
        return url
