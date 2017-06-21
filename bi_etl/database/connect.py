# -*- coding: utf-8 -*-
"""
Created on Jan 22, 2016

@author: woodd
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy import types as sqltypes
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from bi_etl.database.database_metadata import DatabaseMetadata


# Custom sqlalchemy dialect colspec to return Numeric values as is.
class _FastNumeric(sqltypes.Numeric):
    def bind_processor(self, dialect):
        return None

    def result_processor(self, dialect, coltype):
        return None


# Q: Why is this a class?
# A: So that we can override the whole thing at once in MockConnect
class Connect(object):
    @staticmethod
    def get_sqlachemy_engine(config, database_name, usersection=None, **kwargs):
        log = logging.getLogger(__name__)

        dialect = config.get(database_name, 'dialect', fallback='oracle')

        if dialect == 'oracle':
            default_dsn = database_name
        else:
            default_dsn = None
        dsn = config.get(database_name, 'dsn', fallback=default_dsn)

        if not dialect.startswith('sqlite'):
            (userid, password) = config.get_database_connection_tuple(database_name, usersection)
        else:
            userid = None
            password = None

        dbname = config.get(database_name, 'dbname', fallback=None)

        # dialect://user:pass@dsn/dbname
        url = '{dialect}://'.format(dialect=dialect)
        if userid is not None:
            url += userid
        no_pw_url = url
        if password is not None:
            url += ':' + password
            no_pw_url += ':****'
        if dsn is not None:
            next_part = '@' + dsn
            url += next_part
            no_pw_url += next_part
        if dbname is not None:
            next_part = '/' + dbname
            url += next_part
            no_pw_url += next_part
        log.debug('Connecting to {}'.format(no_pw_url))

        if dialect == 'oracle':
            if 'arraysize' not in kwargs:
                kwargs['arraysize'] = config.getint(database_name, 'arraysize', fallback=5000)
                log.debug('{} using arraysize={}'.format(database_name, kwargs['arraysize']))

        if 'encoding' not in kwargs:
            encoding = config.get(database_name, 'encoding', fallback=None)
            if encoding:
                kwargs['encoding'] = encoding
        if 'encoding' in kwargs:
            log.debug('{} using encoding={}'.format(database_name, kwargs['encoding']))
        engine = create_engine(url, **kwargs)
        if config.getboolean(database_name, 'fast_numeric', fallback=True):
            engine.dialect.colspecs[sqltypes.Numeric] = _FastNumeric
        return engine

    @staticmethod
    def get_sqlachemy_session(config, database_name, usersection=None):
        log = logging.getLogger(__name__)
        log.debug('Making session for {}, userid = {}'.format(database_name, usersection))
        engine = Connect.get_sqlachemy_engine(config, database_name, usersection)
        # create a configured "Session" class
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        session_class = scoped_session(session_factory)
        session = session_class()

        return session

    @staticmethod
    def get_database_metadata(config, database_name, user=None, schema=None, **kwargs):
        log = logging.getLogger(__name__)
        engine = Connect.get_sqlachemy_engine(config, database_name, user, **kwargs)
        if schema is None and config.has_option(database_name, 'schema'):
            schema = config.get(database_name, 'schema')
            log.info("Using config file schema {}".format(schema))
        return DatabaseMetadata(bind=engine, schema=schema, quote_schema=False)
