import os
from typing import Optional

import sqlalchemy
from sqlalchemy import TEXT, LargeBinary


class SqliteDB(object):
    SUPPORTS_DECIMAL = False
    SUPPORTS_TIME = True
    SUPPORTS_INTERVAL = False
    SUPPORTS_BOOLEAN = True
    SUPPORTS_BINARY = True
    DATE_AS_DATETIME = False
    MAX_NAME_LEN = 128

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print(f"Creating the {cls} instance")
            self = super().__new__(cls)
            cls._instance = self
            self._new_init(*args, **kwargs)

        else:
            print("Existing singleton used")
        return cls._instance

    def _new_init(self, *args, **kwargs):
        self.instance_count = 0
        self.temp_file = f"unit_tests_sqlite.db"
        self.container = None

    def __init__(self):
        self.instance_count += 1
        print(f"init {self.__class__} now {self.instance_count} instance refs")

    def __del__(self):
        self.instance_count -= 1
        print(f"del {self.__class__} now {self.instance_count} instance refs")

    # noinspection PyPep8Naming
    @property
    def TEXT(self):
        return TEXT

    # noinspection PyPep8Naming
    @property
    def BINARY(self):
        return LargeBinary

    # noinspection PyPep8Naming
    def NUMERIC(
            self,
            precision: Optional[int] = None,
            scale: Optional[int] = None,
    ):
        return sqlalchemy.sql.sqltypes.NUMERIC(precision, scale)

    def get_url(self):
        # return f'sqlite://'
        # Using an actual file helps with debugging
        return f"sqlite:///{self.temp_file}"

    def get_options(self):
        return {}

    def shutdown(self):
        if os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except PermissionError:
                # Ignore errors that we can't remove the file if another session has it open
                pass

    def create_engine(self):
        return sqlalchemy.create_engine(
            self.get_url(),
            **self.get_options()
        )
