#===============================================================================
# """
# Created on May 15, 2015
# 
# @author: Derek Wood
# 
# THIS LOOKUP IS NOT USABLE YET.
# 
# For many data types the values get mangled when stored in sqlite3 and thus will 
# appear to be different from the source values (in Table.upsert) when no real difference exists.
# 
# Needs format unit tests!  
# 
# """
# 
# import os
# import sqlite3
# from sqlalchemy import create_engine
# from sqlalchemy.ext.compiler import compiles
# from sqlalchemy.sql.expression import bindparam
# import sqlalchemy.dialects.oracle.base
# 
# from bi_etl.lookups.lookup import Lookup
# from bi_etl.components.row.row import Row
# from bi_etl.components.table import Table
# from bi_etl.scheduler.task import Database
# from bi_etl.exceptions import NoResultFound
#         
# __all__ = ['SQLLiteLookup']
# 
# 
# ## Fix conversion of Oracle data types to sqlite data types
# @compiles(sqlalchemy.dialects.oracle.base.NUMBER, 'sqlite')
# def compile_NUMBER(element, compiler, **kw):
#     """ Handles mysql NUMBER datatype as Decimal in sqlite.  """
#     return compiler.visit_DECIMAL(element, **kw)
# 
# @compiles(sqlalchemy.dialects.oracle.DATE, 'sqlite')  # @UndefinedVariable
# def compile_DATETIME(element, compiler, **kw):
#     """ Handles mysql NUMBER datatype as Decimal in sqlite.  """
#     return compiler.visit_DATETIME(element, **kw)
# 
# class SQLLiteLookup(Lookup):
#     def __init__(self, lookup_name, lookup_keys, parent_component, path= None):
#         """
#         Optional parameter path where the lookup files should be persisted to disk
#         """
#         super(SQLLiteLookup, self).__init__(lookup_name, lookup_keys, parent_component)
#         self._set_path(path)
#         self.table = None 
#         self.database = None    
#         self._lookup_stmt = None 
#         self._delete_stmt = None
#         self.row_count = 0
#         
#     def getconn(self, connectionRecord=None):
#         c = sqlite3.connect(self.cache_file_path)
#         c.text_factory=str
#         self.log.debug("Connection path = {}".format(self.cache_file_path))
#         return c
#         
#     def _set_path(self, path):
#         if path is not None:
#             self.path = path
#         else:
#             self.path = self.parent_component.task.config.get('Cache','path', fallback='')
# 
#     
#             
#     def _init_cache(self):
#         self.file_name_root = 'lookup_{}_{}'.format(self.lookup_name, os.getpid())
#         self.cache_file_path = os.path.join(self.path, self.file_name_root)
#         self.log.debug("Creating cache in {}".format(self.cache_file_path))
#         con_url = 'sqlite://'
#         self.engine = create_engine(con_url, echo=False, creator=self.getconn, connect_args={'self':self})
#         self.connection = self.engine.connect()
#         self.connection.connection.text_factory = str
#         self.database = Database(bind=self.connection)
#         self.parent_component.task.add_database(self.database)
#         self.table = None
# 
#     def cache_row(self, row, allow_update = False):
#         ## We make the table where since with the current lookup API it's the first time we have a row structure
#         if self.table is None:
#             if self.database is None:
#                 self._init_cache()            
#             sa_table = sqlalchemy.sql.schema.Table('lookupTable', self.database)  # @UndefinedVariable
#             for column in row.parent.columns:
#                 new_col = column.copy()
#                 sa_table.append_column(new_col)
#             sa_table.create()
#             ## TODO: Add a feature to bi_etl.components.table.Table to allow it to create the table based on the template like above
#             self.table = Table(self.parent_component.task,
#                                self.database,
#                                'lookupTable',
#                                #batch_size=1,
#                                )
#         if allow_update:
#             self.table.upsert(row)
#         else:
#             self.table.insert(row)
#         self.row_count += 1
#         
#     def commit(self):
#         self.table.commit()
#         
#     
#         
#     def find_where(self, key_names= None, key_values= None, limit= None):
#         if key_names is None:
#             filter_dict = None
#         else:
#             filter_dict = dict(list(zip(key_names, key_values)))
#            
#         for row in self.table.where(filter_dict):
#             yield Row(row)
#     
#     def __iter__(self):
#         """
#         The rows will come out in any order.
#         """
#         if self.table is not None:
#             return iter(self.table)
#             
#     def __len__(self):
#         return self.row_count
# 
#     def clear_cache(self):
#         pass
#         if self.table is not None:
#             #self.table.truncate(parent_stats=self.stats)
#             self.table = None
#             self.connection.close()
#             self.engine.dispose()
#             self.database = None
#             for file_name in os.listdir(self.path):
#                 if file_name.startswith(self.file_name_root):
#                     os.remove(os.path.join(self.path, file_name))                
#         self.row_count = 0
#         
#     def _add_stmt_where_clause(self, stmt):
#         col_num = 1
#         for key_col in self.lookup_keys:
#             stmt = stmt.where(self.table.get_column(key_col) == bindparam('k{}'.format(col_num)))
#             col_num += 1
#         return stmt
#         
#     def _get_stmt_where_values(self, row):
#         values_dict = dict()
#         col_num = 1
#         for key_val in self.get_list_of_lookup_column_values(row):
#             values_dict['k{}'.format(col_num)] = key_val
#             col_num += 1
#         return values_dict           
# 
#     def uncache_row(self, row):
#         if self.table is not None:
#             if self._delete_stmt is None:
#                 stmt = self.table.delete()           
#                 stmt = self._add_stmt_where_clause(stmt)
#                 self._delete_stmt = stmt.compile()      
#             values_dict = self.s_get_stmt_where_values(row)     
#             result = self.table.execute(self._delete_stmt, values_dict)
#             self.row_count -= result.rowcount
#     
#     def find_in_cache(self, row):
#         """Find a matching row in the lookup based on the lookup index (keys)"""
#         if self.table is None:
#             raise ValueError("Lookup {} not cached".format(self.lookup_name))
#         else:
#             if self._lookup_stmt is None:
#                 stmt = self.table.select()           
#                 stmt = self._add_stmt_where_clause(stmt)
#                 self._lookup_stmt = stmt.compile()      
#             values_dict = self.s_get_stmt_where_values(row)     
#             rows = list(self.table.execute(self._lookup_stmt, values_dict))
#             if len(rows) == 0:
#                 raise NoResultFound()
#             elif len(rows) == 1:
#                 return Row(rows[0])
#             else:
#                 raise RuntimeError("find_in_cache {} matched multiple records {}".format(row, rows))
#===============================================================================