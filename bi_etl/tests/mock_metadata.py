from sqlalchemy.sql.schema import DEFAULT_NAMING_CONVENTION


class MockTableMeta(object):
    def __init__(self, keys):
        self.keys = keys


class MockDatabaseMeta(object):
    def __init__(self, tables=None):
        self.keys = []
        self.schema = None
        self.tables = tables or []
        self.naming_convention = DEFAULT_NAMING_CONVENTION
        self._fk_memos = []

    def _add_table(self, name, schema, table):
        pass

    def _remove_table(self, name, schema):
        pass
