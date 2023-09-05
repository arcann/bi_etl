import os
import platform
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from typing import Optional
from urllib import request
from urllib.error import HTTPError

import sqlalchemy
from sqlalchemy import VARCHAR
from testcontainers.core.generic import DbContainer
from testcontainers.oracle import OracleDbContainer

from tests.db_oracle.container_oracledb import OracleDbContainerNoCX
from tests.db_postgres.base_docker import BaseDockerDB

__all__ = ['OracleDockerDB']


class OracleDockerDB(BaseDockerDB):
    """

    Note: On Windows this currently requires docker desktop

    """
    SUPPORTS_DECIMAL = True
    SUPPORTS_TIME = False
    SUPPORTS_BOOLEAN = False
    DATE_AS_DATETIME = True
    MAX_NAME_LEN = 30
    MODE = 'cx_Oracle'

    @property
    def TEXT(self):
        return VARCHAR(4000)

    def NUMERIC(
            self,
            precision: Optional[int] = None,
            scale: Optional[int] = None,
    ):
        # noinspection PyUnresolvedReferences
        return sqlalchemy.dialects.oracle.NUMBER(
            precision, scale,
            asdecimal=True,
        )

    def _get_driver(self):
        try:
            import oracledb
            print("oracledb found")
            if sqlalchemy.__version__ > '2':
                self.MODE = "oracledb"
            else:
                print(f"oracledb requires sqlalchemy 2+. Found {sqlalchemy.__version__}")
                raise ImportError(f"sqlalchemy version error")
        except ImportError:
            import cx_Oracle
            print("cx_Oracle found")
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
                    zip_file_tmp = None
                    try:
                        zip_file_tmp = NamedTemporaryFile(delete=False)
                        zip_file = zip_file_tmp.name
                        try:
                            request.urlretrieve(client_url, zip_file)
                        except HTTPError as e:
                            raise ValueError(f"{e} on url {client_url}")

                        # Unzip client
                        with zipfile.ZipFile(zip_file, "r") as zip_ref:
                            zip_ref.extractall(client_root)
                    finally:
                        if zip_file_tmp is not None:
                            zip_file_tmp.close()
                            if os.path.exists(zip_file_tmp.name):
                                os.remove(zip_file_tmp.name)

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
        if self.MODE == 'oracledb':
            return OracleDbContainerNoCX(image=image)
        else:
            return OracleDbContainer(image=image)

    def get_container(self) -> DbContainer:
        self._get_driver()

        container = super().get_container()
        return container

    def get_options(self):
        return {
        }
