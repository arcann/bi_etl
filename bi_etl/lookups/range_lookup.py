'''
Created on Feb 27, 2015

@author: woodd
'''
from sortedcontainers.sorteddict import SortedDict

from sqlalchemy.sql.expression import bindparam

from bi_etl.exceptions import BeforeAllExisting, AfterExisting, NoResultFound
from bi_etl.lookups.lookup import Lookup
from bi_etl.utility import dict_to_str
from bi_etl.components.row import Row

__all__ = ['RangeLookup']

class RangeLookup(Lookup):
    def __init__(self, lookup_name, lookup_keys, parent_component, begin_date, end_date, config=None):
        super(RangeLookup, self).__init__(lookup_name= lookup_name, 
                                          lookup_keys= lookup_keys, 
                                          parent_component= parent_component, 
                                          config= config
                                          )
        self.begin_date = begin_date
        self.end_date = end_date
        self._remote_lookup_stmt_no_date = None
        self._len = 0

    def __len__(self):
        return self._len    
    
    def cache_row(self, row, allow_update = True):
        if self.cache_enabled:
            lk_tuple = self.get_hashable_combined_key(row)
            if self.cache is None:
                self.init_cache()                
            versions_collection = self.cache.get(lk_tuple,None)
            effective_date = row[self.begin_date]                                            
                
            if versions_collection is None:
                versions_collection = SortedDict()                
                
            
            if effective_date in versions_collection:
                if not allow_update:
                    self.log.error('Existing duplicate row = {}'.format(repr(versions_collection[effective_date] )))
                    raise ValueError('Key {} + date {} already in cache and allow_update was False'.format(lk_tuple, effective_date))
            else:
                self._len += 1
            
            versions_collection[effective_date] = row
            self.cache[lk_tuple] = versions_collection
            
            ## Capture memory usage snapshots
            if self._row_size is None:   
                self._get_first_row_size(row)
            else:
                self._get_estimate_row_size()
            
    def uncache_row(self, row):
        lk_tuple = self.get_hashable_combined_key(row)
        if self.cache is not None:                
            versions_collection = self.cache.get(lk_tuple,None)
            effective_date = row[self.begin_date]                                            
                
            if versions_collection:                
                ## Look for and remove existing instance that are exactly the same date
                try:
                    del versions_collection[effective_date]
                except (KeyError, ValueError):
                    ## Not found, that's OK
                    pass

    def __iter__(self):
        '''
        The natural keys will come out in any order. However, the versions within a natural key set will come out in ascending order.  
        '''
        if self.cache is not None:
            for versions_collection in self.cache.values():
                for row in versions_collection.values():
                    yield row
    
    #pylint: disable=arguments-differ
    def find_in_cache(self, row, effective_date= None):
        '''
        Find an existing row in the cache effective on the date provided.  
        Can raise ValueError if the cache is not setup.
        Can raise NoResultFound if the key is not in the cache.
        Can raise BeforeAllExisting is the effective date provided is before all existing records.
        '''
        if self.cache is None:
            raise ValueError("Lookup not cached")
        else:
            lk_tuple = self.get_hashable_combined_key(row)
            versions_collection = None
            try:                
                if effective_date is None:
                    effective_date = row[self.begin_date]
                versions_collection = self.cache[lk_tuple]
                if versions_collection:
                    first_effective_index = versions_collection.bisect_right(effective_date)-1
                    if first_effective_index <= -1:
                        raise BeforeAllExisting(versions_collection[versions_collection.iloc[0]], effective_date)
                    first_effective = versions_collection[versions_collection.iloc[first_effective_index]]
                    ## Check that record doesn't end before our date
                    if first_effective[self.end_date] < effective_date:
                        raise AfterExisting(first_effective, effective_date)
                    return first_effective                          
            except KeyError:
                raise NoResultFound()
                
    def _add_remote_stmt_where_clause(self, stmt):
        stmt = super(RangeLookup, self)._add_remote_stmt_where_clause(stmt)
        stmt = stmt.where(bindparam('eff_date') >= self.parent_component.get_column(self.begin_date))
        stmt = stmt.where(bindparam('eff_date') <= self.parent_component.get_column(self.end_date))
        return stmt
    
    def _get_remote_stmt_where_values(self, row, effective_date = None):
        values_dict = super(RangeLookup, self)._get_remote_stmt_where_values(row)
        if effective_date is None:
            effective_date = row[self.begin_date]
        values_dict['eff_date'] = effective_date
        return values_dict
    
    def find_in_remote_table(self, row, effective_date=None):
        '''
        Find a matching row in the lookup based on the lookup index (keys)
        
        Only works if parent_component is based on bi_etl.components.readonlytable
        '''
        
        if self._remote_lookup_stmt is None:
            stmt = self.parent_component.select()           
            stmt = self._add_remote_stmt_where_clause(stmt)
            self._remote_lookup_stmt = stmt.compile()
            ## Build a second statement that does the lookup without dates
            ## Which is what our parent Lookup does so we call that
            stmt_no_date = self.parent_component.select()
            stmt_no_date = super(RangeLookup, self)._add_remote_stmt_where_clause(stmt_no_date)
            stmt_no_date = stmt_no_date.order_by(self.parent_component.get_column(self.begin_date))
            self._remote_lookup_stmt_no_date = stmt_no_date.compile()
        values_dict = self._get_remote_stmt_where_values(row, effective_date)     
        rows = list(self.parent_component.execute(self._remote_lookup_stmt, values_dict))
        if len(rows) == 0:
            ## Use the second statement that does the lookup without dates
            ## Which is what our parent Lookup does so we call that to set values
            values_dict = super(RangeLookup, self)._get_remote_stmt_where_values(row)
            results = self.parent_component.execute(self._remote_lookup_stmt_no_date, values_dict)
            row = results.fetchone()
            if row is None:
                raise NoResultFound()
            else:
                ## If we found a row return the first (why we sorted)
                raise BeforeAllExisting(Row(row), effective_date = row[self.begin_date])
        elif len(rows) == 1:
            return Row(rows[0])
        else:
            msg = 'dict_to_str statement {}\n'.format(self._remote_lookup_stmt)
            msg += 'using keys {}\n'.format(dict_to_str(values_dict))
            msg += 'matched multiple records: \n'
            row_cnt = 0
            for r in rows:
                row_cnt += 1
                if row_cnt >= 10:
                    msg += '...'
                    break
                msg += dict_to_str(self.get_list_of_lookup_column_values(r), depth=2)
                msg += '\n--------------------------\n' 
            raise RuntimeError(msg)   
        
                
                