import logging
import os
import platform
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from urllib import request
from urllib.error import HTTPError

from sqlalchemy import VARCHAR
from testcontainers.core import config as tc_config
from testcontainers.core.generic import DbContainer
from testcontainers.oracle import OracleDbContainer

from tests.db_postgres.base_docker import BaseDockerDB

__all__ = ['OracleDockerDB']


class OracleDockerDB(BaseDockerDB):
    """

    Note: On Windows this currently requires docker desktop

    """
    SUPPORTS_DECIMAL = True
    SUPPORTS_TIME = False
    SUPPORTS_BOOLEAN = False
    MAX_NAME_LEN = 30

    @property
    def TEXT(self):
        return VARCHAR(4000)

    def _get_driver(self):
        import cx_Oracle
        # noinspection PyBroadException
        try:
            cx_Oracle.init_oracle_client()
            print("Existing system oracle client used")
        except cx_Oracle.ProgrammingError:
            # Oracle Client library has already been initialized
            pass
        except Exception:
            print("No existing system oracle client found. Will use temp client.")
            if platform.system() == 'Windows':
                sys1 = 'nt'
                sys2 = 'windows'
            else:
                sys1 = 'linux'
                sys2 = 'linux'

            version = '21.6.0.0.0'

            client_url = '/'.join([
                "https://download.oracle.com",
                "otn_software",
                sys1,
                "instantclient",
                version.replace('.', ''),
                f"instantclient-basic-{sys2}.x64-{version}dbru.zip"
            ])
            # https://download.oracle.com/otn_software/nt/instantclient/216000/instantclient-basic-windows.x64-21.6.0.0.0dbru.zip
            # instantclient-basiclite-windows.x64-21.6.0.0.0dbru.zip

            temp_dir = Path(gettempdir())
            client_root = temp_dir / 'instantclient'

            # oci.dll seems to be the primary driver, so we use that file as the one to check
            # that we don't just have an empty instantclient folder.
            oci_dll = client_root / 'oci.dll'
            if not oci_dll.is_file():
                print(f"Downloading Oracle instant client for {sys2} version {version} to {client_root}")
                zip_file = NamedTemporaryFile(delete=False).name
                try:
                    request.urlretrieve(client_url, zip_file)
                except HTTPError as e:
                    raise ValueError(f"{e} on url {client_url}")

                # Unzip client
                with zipfile.ZipFile(zip_file, "r") as zip_ref:
                    zip_ref.extractall(client_root)
                os.remove(zip_file)

            # noinspection PyTypeChecker
            client_dirs = [
                str(d) for d in os.listdir(client_root)
                if (client_root / d).is_dir() and d[:13] == 'instantclient'
            ]
            if len(client_dirs) != 1:
                raise ValueError(f"{client_root} does not contain an instantclient* dir")
            client_path = client_root / client_dirs[0]

            if str(client_root) not in os.environ['PATH']:
                print(f"Adding {client_path} to PATH")
                os.environ['PATH'] += os.pathsep + str(client_path)
            else:
                print(f"{client_path} already in PATH")

        try:
            cx_Oracle.init_oracle_client()
        except cx_Oracle.ProgrammingError:
            # Oracle Client library has already been initialized
            pass

    def get_container_class(self, image="wnameless/oracle-xe-11g-r2:latest"):
        return OracleDbContainer(image=image)

    def get_container(self) -> DbContainer:
        self._get_driver()
        container = super().get_container()
        return container

    def get_options(self):
        return {
        }
