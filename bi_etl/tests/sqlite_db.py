import os

import sqlalchemy


class SqliteDB(object):

    def __init__(self):
        self.temp_file = f"unit_tests_sqlite.db"

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
