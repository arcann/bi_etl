
"""
Created on Jan 22, 2016

@author: Derek Wood
"""
from unittest.mock import Mock

from bi_etl.database.connect import Connect


class MockConnect(Connect):    
    engines_created = dict()
    session_created = dict()
    database_metadata_created = dict()
    
    @staticmethod
    def _return_or_make(collection, database_name):
        if database_name in collection:
            return collection[database_name]
        else:
            engine = Mock()
            collection[database_name] = engine
            return engine
    
    @staticmethod
    def get_sqlachemy_engine(config, database_name, usersection=None, **kwargs):
        return MockConnect._return_or_make(MockConnect.engines_created, database_name)
    
    @staticmethod
    def get_sqlachemy_session(config, database_name, usersection = None):
        return MockConnect._return_or_make(MockConnect.session_created, database_name)     
    
    @staticmethod
    def get_database_metadata(config, database_name, user = None, schema = None, **kwargs):
        return MockConnect._return_or_make(MockConnect.database_metadata_created, database_name)        
