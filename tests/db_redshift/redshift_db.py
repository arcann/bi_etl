from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase

from tests.db_sqlite.sqlite_db import SqliteDB


class RedshiftDB(SqliteDB):
    SUPPORTS_DECIMAL = True
    SUPPORTS_TIME = True
    SUPPORTS_INTERVAL = False
    SUPPORTS_BINARY = False  # VARBYTE exists but not in SQLAlchemy
    MAX_NAME_LEN = 63

    def __init__(self, config: SQLAlchemyDatabase):
        super().__init__()
        self.config = config

    @property
    def BINARY(self):
        raise NotImplemented("VARBYTE exists but not in SQLAlchemy")

    def get_url(self):
        return self.config.get_uri()

    def shutdown(self):
        pass

    def create_engine(self):
        return self.config.get_engine()
