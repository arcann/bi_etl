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
# Needs formal unit tests!
#    
# """
# from sqlalchemy.sql.expression import bindparam
# 
# from bi_etl.components.row.row import Row
# from bi_etl.lookups.sqlite_lookup import SQLLiteLookup
# from bi_etl.exceptions import NoResultFound
#         
# __all__ = ['SQLLiteRangeLookup']
# 
# class SQLLiteRangeLookup(SQLLiteLookup):
#     def __init__(self, lookup_name, lookup_keys, parent_component, begin_date, end_date, path= None):
#         """
#         Optional parameter path where the lookup files should be persisted to disk
#         """
#         super(SQLLiteRangeLookup, self).__init__(lookup_name, lookup_keys, parent_component, path)
#         self.begin_date = begin_date
#         self.end_date = end_date
#         self._lookup_stmt = None
#         
#     def _add_stmt_where_clause(self, stmt):
#         col_num = 1
#         for key_col in self.lookup_keys:
#             stmt = stmt.where(self.table.get_column(key_col) == bindparam('k{}'.format(col_num)))
#             col_num += 1
#         stmt = stmt.where(bindparam('eff_date') >= self.table.get_column(self.begin_date))
#         stmt = stmt.where(bindparam('eff_date') <= self.table.get_column(self.end_date))
#         return stmt
#         
#     def _get_stmt_where_values(self, row, effective_date = None):
#         values_dict = dict()
#         col_num = 1
#         for key_val in self.get_list_of_lookup_column_values(row):
#             values_dict['k{}'.format(col_num)] = key_val
#             col_num += 1       
#         if effective_date is None:
#             effective_date = row[self.begin_date]
#         values_dict['eff_date'] = effective_date
#         return values_dict
#     
#     def uncache_row(self, row):
#         if self.table is not None:
#             if self._delete_stmt is None:
#                 stmt = self.table.table.delete()           
#                 stmt = self._add_stmt_where_clause(stmt)
#                 self._delete_stmt = stmt.compile()      
#             values_dict = self.s_get_stmt_where_values(row)     
#             result = self.table.execute(self._delete_stmt, values_dict)
#             self.row_count -= result.rowcount
#         
#     def find_in_cache(self, row, effective_date= None):
#         """Find a matching row in the lookup based on the lookup index (keys)"""
#         if self.table is None:
#             raise ValueError("Lookup {} not cached".format(self.lookup_name))
#         else:
#             if self._lookup_stmt is None:
#                 stmt = self.table.select()           
#                 stmt = self._add_stmt_where_clause(stmt) 
#                 self._lookup_stmt = stmt.compile()      
#             
#             values_dict = self._get_stmt_where_values(row, effective_date)
#             rows = list(self.table.execute(self._lookup_stmt, values_dict))            
#             if len(rows) == 0:
#                 raise NoResultFound()
#             elif len(rows) == 1:
#                 return Row(rows[0])
#             else:
#                 raise RuntimeError("find_in_cache {} matched multiple records {}".format(row, rows))
#===============================================================================