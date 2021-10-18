# -*- coding: utf-8 -*-
"""
Created on Jan 22, 2016

@author: Derek Wood
"""
import json
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus

try:
    import boto3
except ImportError:
    boto3 = None

from sqlalchemy.pool import QueuePool, NullPool

from bi_etl.bi_config_parser import BIConfigParser
from sqlalchemy import create_engine, event
from sqlalchemy import types as sqltypes
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker, Session
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
    _database_pool = dict()

    @staticmethod
    def get_sqlachemy_engine(
            config: BIConfigParser,
            database_name: str,
            usersection: str = None,
            override_port: int = None,
            **kwargs) -> Engine:
        log = logging.getLogger(__name__)

        dialect = config.get(database_name, 'dialect', fallback='oracle')

        if dialect == 'oracle':
            default_dsn = database_name
        else:
            default_dsn = None
        dsn = config.get(database_name, 'dsn', fallback=default_dsn)
        port = config.get(database_name, 'port', fallback=None)

        if not dialect.startswith('sqlite'):
            (userid, password) = config.get_database_connection_tuple(database_name, usersection)
        else:
            userid = None
            password = None

        dbname = config.get(database_name, 'dbname', fallback=None)
        db_options = config.get(database_name, 'db_options', fallback=None)

        if db_options is not None:
            if '\n' in db_options:
                db_options = '&'.join([opt.strip() for opt in db_options.split('\n') if opt.strip() != ''])

        if dbname is not None and '?' in dbname:
            dbname, db_options_legacy = dbname.split('?')
            if db_options is None:
                db_options = db_options_legacy
            else:
                # TODO: Better to check one option at a time for overlap.
                #       Would need to split on & and then split on = to get option names
                if db_options != db_options_legacy:
                    db_options = db_options + '&' + db_options_legacy
                    log.warning(f'Parts of database options specified in both dbname and db_options. ({db_options_legacy}) and ({db_options})')
                else:
                    log.warning(f'Identical database options specified in both dbname and db_options. ({db_options_legacy}) and ({db_options})')

        use_get_cluster_credentials = config.getboolean(database_name, 'use_get_cluster_credentials', fallback=False)
        if use_get_cluster_credentials:
            cluster_id = config.get(database_name, 'rs_cluster_id', fallback=None)
            region_name = config.get(database_name, 'rs_region_name', fallback='us-east-1')
            aws_access_key_id = userid
            rs_db_user_id = config.get(database_name, 'rs_db_user_id', fallback=None)
            if rs_db_user_id is None:
                raise ValueError(f'rs_db_user_id required for db section {database_name}')
            # aws_secret_access_key = keyring.get_password(database_name, 'access_key')
            aws_secret_access_key = password
            duration_seconds = config.getint(database_name, 'duration_seconds', fallback=3600)

            if boto3 is None:
                raise ImportError('boto3 not imported')

            # noinspection PyUnresolvedReferences
            rs = boto3.client(
                'redshift',
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=None,
            )

            credentials = rs.get_cluster_credentials(
                DbUser=rs_db_user_id,
                DbName=dbname,
                DurationSeconds=duration_seconds,
                ClusterIdentifier=cluster_id
            )

            # Overwrite the access key & secret key with the temp DB user id and password
            # Note: These go into the URL string so they need quote_plus for any special chars
            userid = quote_plus(credentials['DbUser'])
            password = quote_plus(credentials['DbPassword'])

        # dialect://user:pass@dsn/dbname
        # mssql+pyodbc://{user}:{password}@{server}:1433/{database_name}?driver=ODBC+Driver+17+for+SQL+Server
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
        if port is not None:
            next_part = ':' + port
            url += next_part
            no_pw_url += next_part
        if override_port is not None:
            next_part = ':' + str(override_port)
            url += next_part
            no_pw_url += next_part
        if dbname is not None:
            next_part = '/' + dbname
            url += next_part
            no_pw_url += next_part
        if db_options is not None:
            next_part = '?' + db_options
            url += next_part
            no_pw_url += next_part

        fast_executemany = config.getboolean(database_name, 'fast_executemany', fallback=None)
        if fast_executemany:
            kwargs['fast_executemany'] = True
            log.info('Using fast_executemany')

        key_word_arguments_list = config.get_list(database_name, 'key_word_arguments')
        for pair in key_word_arguments_list:
            keyword, value = pair.split('=')
            keyword = keyword.strip()
            value = eval(value)  # This will convert int, bool etc to the correct type
            kwargs[keyword] = value

        log.debug('Connecting to {}'.format(no_pw_url))

        create_engine_args_list = config.get_list(database_name, 'create_engine_args', fallback='')
        for arg in create_engine_args_list:
            arg_name, arg_value = arg.split('=')
            arg_name = arg_name.strip()
            arg_value = arg_value.strip()
            try:
                arg_value_int = int(arg_value)
                arg_value = arg_value_int
            except ValueError:
                pass
            kwargs[arg_name] = arg_value

        create_pool_type = config.get(database_name, 'create_pool_type', fallback='QueuePool')

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

        if 'poolclass' in kwargs:
            log.debug(f"poolclass already set to {kwargs['poolclass']} not using config setting of {create_pool_type}")
        if create_pool_type == 'QueuePool':
            kwargs['poolclass'] = QueuePool
        elif create_pool_type == 'NullPool':
            kwargs['poolclass'] = NullPool
        else:
            raise ValueError(f'Unexpected create_pool_type {create_pool_type}')

        if len(kwargs) > 0:
            for keyword, value in kwargs.items():
                log.debug(f'{database_name} using keyword argument {keyword} = {value}')

        # creator=get_new_connection
        engine = create_engine(url, **kwargs)
        if config.getboolean(database_name, 'fast_numeric', fallback=True):
            engine.dialect.colspecs[sqltypes.Numeric] = _FastNumeric
            log.info('Using fast_numeric')

        engine.last_get_cluster_credentials = datetime.now()

        @event.listens_for(engine, 'do_connect', named=True)
        def engine_do_connect(**kw):
            """
            listen for the 'do_connect' event
            """
            # from bi_etl.utility import dict_to_str
            # print(dict_to_str(kw))
            if use_get_cluster_credentials:
                rs_new_credentials_seconds = config.getint(database_name, 'rs_new_credentials_seconds', fallback=duration_seconds/2)
                if datetime.now() - engine.last_get_cluster_credentials > timedelta(seconds=rs_new_credentials_seconds):
                    log.info('Getting new Redshift cluster credentials')
                    new_credentials = rs.get_cluster_credentials(
                        DbUser=rs_db_user_id,
                        DbName=dbname,
                        DurationSeconds=duration_seconds,
                        ClusterIdentifier=cluster_id
                    )
                    # Note: Since we are not building a URL here we don't need/want to use quote_plus
                    kw['cparams']['user'] = new_credentials['DbUser']
                    kw['cparams']['password'] = new_credentials['DbPassword']
                    engine.last_get_cluster_credentials = datetime.now()

            # Return None to allow control to pass to the next event handler and ultimately to allow the dialect to connect normally, given the updated arguments.
            return None

        return engine

    @staticmethod
    def get_sqlachemy_session(
            config: BIConfigParser,
            database_name: str,
            usersection: str = None,
            **kwargs) -> Session:
        log = logging.getLogger(__name__)
        log.debug('Making session for {}, userid = {}'.format(database_name, usersection))
        engine = Connect.get_sqlachemy_engine(config, database_name, usersection)
        # create a configured "Session" class
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        session_class = scoped_session(session_factory)
        session = session_class()

        return session

    @staticmethod
    def get_database_metadata(
            config: BIConfigParser,
            database_name: str,
            user: str = None,
            schema: str = None,
            override_port: int = None,
            **kwargs) -> DatabaseMetadata:
        log = logging.getLogger(__name__)

        pool_key_list = [database_name, user, schema, override_port]
        for entry in kwargs.items():
            pool_key_list.append(entry)
        for entry in config[database_name].items():
            if not isinstance(entry[1], dict):
                pool_key_list.append(entry)
        pool_key = tuple(pool_key_list)

        if pool_key in Connect._database_pool:
            log.info(f"Using existing in-memory metadata for {database_name}")
            return Connect._database_pool[pool_key]
        else:
            engine = Connect.get_sqlachemy_engine(config, database_name, user, override_port=override_port, **kwargs)
            if schema is None and config.has_option(database_name, 'schema'):
                schema = config.get(database_name, 'schema')
                log.info("Using config file schema {}".format(schema))
            if config.has_option(database_name, 'uses_bytes_length_limits'):
                uses_bytes_length_limits = config.getboolean(database_name, 'uses_bytes_length_limits')
            else:
                uses_bytes_length_limits = None
            db = DatabaseMetadata(
                bind=engine,
                schema=schema,
                quote_schema=False,
                database_name=database_name,
                uses_bytes_length_limits=uses_bytes_length_limits,
            )
            Connect._database_pool[pool_key] = db
            return db
