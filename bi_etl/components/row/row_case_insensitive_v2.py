# -*- coding: utf-8 -*-
'''
Created on Sep 17, 2014

@author: woodd
'''
import warnings
from decimal import Decimal
from operator import attrgetter

from sqlalchemy.sql.schema import Column


from bi_etl.utility import dict_to_str
from bi_etl.components.row.column_difference import ColumnDifference
from bi_etl.components.row.row_status import RowStatus
from bi_etl.components.row.cached_frozenset import get_cached_frozen_set


__all__ = ['RowCaseInsensitive']

#### For performance with the Column and str to lowercase str conversion we keep a cache of converted values
## The dict lookup tests as twice as fast as just the lower function
        
__name_map_db = dict()

def _get_name(input_name):
    if input_name in __name_map_db:
        return __name_map_db[input_name]
    else:
        ## If the input_name is an SA Column use it's name. In Python 2.7 to 3.4, isinstance is a lot faster than try-except or hasattr (which does a try)
        if isinstance(input_name,str):
            outname = input_name.lower()
        elif isinstance(input_name, Column):
            outname = input_name.name.lower()            
        else:
            raise ValueError("Row column name must be str, unicode, or Column. Got {}".format(type(input_name)))            
        __name_map_db[input_name] = outname
        return outname
    
def _get_name_Column_opt(input_name):
    if input_name in __name_map_db:
        return __name_map_db[input_name]
    else:
        ## If the input_name is an SA Column use it's name. In Python 2.7 to 3.4, isinstance is a lot faster than try-except or hasattr (which does a try)
        if isinstance(input_name, Column):
            outname = input_name.name.lower()            
        elif isinstance(input_name,str):
            outname = input_name.lower()            
        else:
            raise ValueError("Row column name must be str, unicode, or Column. Got {}".format(type(input_name)))            
        __name_map_db[input_name] = outname
        return outname

class RowCaseInsensitive(dict):
    '''
    Replacement for core SQL Alchemy, CSV or other dictionary based rows.
    Handles converting column names (keys) between upper and lower case.
    Handles column names (keys) that are SQL Alchemy column objects.
    Keeps order of the columns (see columns_in_order) 
    '''
    NUMERIC_TYPES = [int, float, Decimal]
    
    def __init__(self, data=None, parent = None, name= None, primary_key = None, status= None):
        ## We don't want to store the parent. It messed with the garbage collection when we did
        ## However, we need some attributes from it.
        super().__init__()                
        self._name = name
        self.status = status
        self.primary_key = primary_key
        self._get_info_from_parent(parent)
        
        ## Initialize as empty
        self._columns_in_order = list()        
        #self._cached_column_set = None
        #self._cached_positioned_column_set = None
        
        ## Populate our data                
        self.update(data)
        
    def _get_info_from_parent(self, parent):
        ## Try to get primary_key from our parent if we have one there
        if self.primary_key is None and parent is not None:
            self.primary_key = parent.primary_key
        if self._name is None and parent is not None:
            try:
                self._name = parent.logical_name
            except AttributeError:
                pass    
    def __reduce__(self):
        status_value = None
        if self.status is not None:
            status_value = self.status.value         
        return (self.__class__,
                #A tuple of arguments for the callable object.
                (),  
                ## State to be passed to setstate
                {'n': self._name, 
                 's': status_value, 
                 'p': self.primary_key,
                 'c': self._columns_in_order,
                 'i':list(self.items()),                                
                }, 
                
               )  

    #pylint: disable=attribute-defined-outside-init
    def __setstate__(self, idict):
        self.__dict__ = idict
        self._name = idict['n'] 
        if idict['s'] is not None:
            self.status = RowStatus(idict['s'])
        else:
            self.status = None
        self.primary_key = idict['p']
        self._columns_in_order = idict['c']
        
        ## Restore column values
        for (key, value) in idict['i']:
            super().__setitem__(key, value)
            
        ## Initialize caches
        #self._cached_column_set = None
        #self._cached_positioned_column_set = None                   
    
    def update(self, *args, **kwds):
        for source_data in args:
            if source_data is None:
                continue
            try:
                ## Check for dict like row
                ##sqlalchemy.engine.RowProxy doesn't have iter, but does have iterkeys
                try:
                    iterator = iter(source_data.keys())
                except AttributeError:
                    iterator = source_data
                
                first_col = True
                for k in iterator:
                    if first_col:
                        needs_column_check = isinstance(k, Column)                        
                        is_tuple = isinstance(k, tuple)
                        first_col = False
                        
                    #print "{} needs_column_check={}".format(self.name, needs_column_check)
                    #print "{} is Column={}".format(self.name, isinstance(k, Column))
                    if is_tuple:
                        key_name = _get_name(k[0])                        
                        self[key_name] = k[1]
                    else:                           
                        if needs_column_check:
                            key_name = _get_name_Column_opt(k)
                        else:
                            key_name = _get_name(k)
                                
                        self[key_name] = source_data[k]
                    
            except AttributeError as e1:
                #traceback.print_exc()
                ## Check for SQLAlchemy ORM row object
                #pylint: disable=protected-access 
                try:
                    attrs = source_data._sa_instance_state.attrs  ## sqlalchemy.util._collections.ImmutableProperties
                    for a in attrs: ##instance of sqlalchemy.orm.state.AttributeState
                        self._raw_setitem(a.key, getattr(source_data, a.key))
                except AttributeError as e2:  ## Not iterable                    
                    raise ValueError("Row couldn't get set with {args}. First Error {e1}.  Error when assuming SQLAlchemy ORM row object {e2})".format(e1=e1, e2=e2,args=args)  )
        for key_name, key_value in kwds.items():
            key_name = _get_name(key_name)
            self[key_name] = key_value
    
    def _get_name_value_pair(self, key, raise_on_not_exist= True):
        keyName = _get_name(key)
        
        try:
            return (keyName, super().__getitem__(keyName))
        except KeyError:
            ## If we get here, everything failed
            if raise_on_not_exist:
                raise KeyError("{} has no item {} it does have {}".format(self.name, key, self.columns_in_order()))
            else:
                return (None, None)
    
    def get_column_name(self, key, raise_on_not_exist= True):
        return self._get_name_value_pair(key, raise_on_not_exist)[0]
    
    @property
    def primary_key(self):
        try:
            if self._primary_key is not None and len(self._primary_key) > 0:
                ## Check if primary_key is list of Column objects and needs to be turned into a list of str name values
                ## We do this here and not on setter since program might never call getter
                if isinstance(self._primary_key[0],Column):
                    self._primary_key = list(map(attrgetter('name'), self._primary_key))
                return self._primary_key
            else:
                return None
        except AttributeError:
            return None

    @primary_key.setter
    def primary_key(self, value):
        if value != None:
            if isinstance(value, str):
                value = [value]
            assert hasattr(value, '__iter__'), "Row primary_key must be iterable or string"
            self._primary_key = value
        else:
            self._primary_key = None
    
    @property
    def name(self):
        if self._name is not None:
            return self._name
        else:
            return dict_to_str(self)

    def __repr__(self):
        return 'Row(name={},status={},primary_key={},\n{}'.format(self._name, self.status, self.primary_key, dict_to_str(self))
    
    def __str__(self):
        if self._name is not None or self.primary_key is not None:
            if self.primary_key is not None:
                try:             
                    key_values = list(self.subset(keep_only=self.primary_key).values())
                except KeyError as e:
                    key_values = list(str(e))   
                return "{name} key_values={keys} status={s}".format(name=self.name, 
                                                                    keys=key_values,
                                                                    s=self.status                                                     
                                                                    )
            else:
                cv = list()
                for k in self.columns_in_order()[:5]:
                    cv.append(self[k])
                return "{name} cols[:5]={cv} status={s}".format(name=self.name, 
                                                                cv=cv,
                                                                s=self.status                                                     
                                                                )
        else:
            return dict_to_str(self)
    
    def __raw_contains(self, key):
        return super().__contains__(key)
    
    def __contains__(self, key):
        keyName = _get_name(key)                
        return super().__contains__(keyName)
        
    def __getitem__(self, key):
        return self._get_name_value_pair(key, raise_on_not_exist= True)[1]       

    def _raw_setitem(self, key, value):
        if self.__raw_contains(key):
            super().__setitem__(key, value)
        else:
            #self._cached_column_set = None
            #self._cached_positioned_column_set = None        
            super().__setitem__(key, value)        
            self._columns_in_order.append(key) 
    
    def __setitem__(self, key, value):
        keyName = _get_name(key)
        self._raw_setitem(keyName, value)
            
    def get_name_by_position(self, position):
        '''
        Get the column name in a given position.
        Note: The first column position is 1 (not 0 like a python list).
        '''
        assert position > 0
        return self._columns_in_order[position-1] ## -1 because positions are 1 based not 0 based
            
    def get_by_position(self, position):
        '''
        Get the column value by position. 
        Note: The first column position is 1 (not 0 like a python list).
        '''
        assert position > 0
        return self[self._columns_in_order[position-1]] ## -1 because positions are 1 based not 0 based
    
    def set_by_position(self, position, value):
        '''
        Set the column value by position. 
        Note: The first column position is 1 (not 0 like a python list).
        '''
        assert position > 0
        self[self._columns_in_order[position-1]] = value ## -1 because positions are 1 based not 0 based
    
    def rename_column(self, old_name, new_name, ignore_missing = False):
        '''
        Rename a column
        
        Parameters
        ----------
        old_name: str
            The name of the column to find and rename.
        
        new_name: str
            The new name to give the column.
            
        ignore_missing: boolean
            Ignore (don't raise error) if we don't have a column with the name in old_name.
            Defaults to False         
        '''
        new_name = _get_name(new_name)
        assert new_name not in self, "Target column name {} already exists".format(new_name)
        try:
            normalized_key, value = self._get_name_value_pair(old_name)
            #self._cached_column_set = None
            #self._cached_positioned_column_set = None
            ## Update name in _columns_in_order
            position = self._columns_in_order.index(normalized_key)
            self._columns_in_order[position] = new_name
            
            ## Update the name in the parent dict
            super().__delitem__(normalized_key)
            super().__setitem__(new_name, value)            
            
        except (KeyError, ValueError) as e:
            if ignore_missing:
                pass
            else:
                raise e
    
    def rename_columns(self, rename_map, new_parent = None, ignore_missing = False):
        '''
        Rename many columns at once.
        
        Parameters
        ----------
        rename_map: dict, or list of tuples
            A dict or list of tuples to use to rename columns.
            Note: a list of tuples is better to use if the renames need to happen in a certain order.
        
        new_name: str
            The new name to give the column.
            
        new_parent: ETLComponent
            (Optional) Change the parent to the passed value. 
            
        ignore_missing: boolean
            Ignore (don't raise error) if we don't have a column with the name in old_name.
            Defaults to False        
        '''
        ## Note: subset with rename_map is currently slightly faster
        if isinstance(rename_map, dict):
            for k in rename_map.keys():
                self.rename_column(k, rename_map[k], ignore_missing)
        else: # assume it's a list of tuples
            for (old, new) in rename_map:
                self.rename_column(old, new, ignore_missing)
        if new_parent:            
            self._get_info_from_parent(new_parent)

    def remove_columns(self, remove_list, new_parent = None, ignore_missing = False):
        """
        Remove columns from this row instance.
        
        Parameters
        ----------
        remove_list: list
            A list of column names to remvoe
        
        new_parent: ETLComponent
            (Optional) Change the parent to the passed value. 
            
        ignore_missing: boolean
            Ignore (don't raise error) if we don't have a column with a given name
            Defaults to False      
        """        
        for c in remove_list:
            try:
                del self[c]                                
            except KeyError as e:
                if ignore_missing:
                    pass
                else:
                    raise e     
        if new_parent:            
            self._get_info_from_parent(new_parent)            
    
    def subset(self, exclude= None, rename_map = None, keep_only= None, new_parent = None):
        """
        Return a new row instance with a subset of the columns. Original row is not modified
        Excludes are done first, then renames and finally keep_only.
        
        Parameters
        ----------
        exclude: list
            A list of column names (before renmaes) to exclude from the subset.
            Optional. Defaults to no excludes.
            
        rename_map: dict
            A dict to use to rename columns.
            Optional. Defaults to no renames.
            
        keep_only: list
            A list of column names (after renames) of columns to keep.
            Optional. Defaults to keep all.
        
        new_parent: ETLComponent
            (Optional) Change the parent of the subset row to the passed value. 
            
        raise_on_not_exist: boolean
            Raise error if we don't have a column with a given name.
            Default to Trye
        """
        if keep_only is not None:
            keep_only = set([_get_name(c) for c in keep_only])
        if exclude is None:  
            exclude = []
        else:
            exclude = set([_get_name(c) for c in exclude])
        subRow = RowCaseInsensitive(name= self._name, parent= new_parent)
        for k in self._columns_in_order:
            if k not in exclude:
                if rename_map is not None and k in rename_map:
                    outCol = rename_map[k]
                else:
                    outCol = k
                #pylint: disable=protected-access
                if keep_only is None or outCol in keep_only:                    
                    super(RowCaseInsensitive, subRow).__setitem__(outCol, self[k])
                    subRow._columns_in_order.append(outCol)
        if self.primary_key:
            try:
                subRow.primary_key = self.primary_key
            except AttributeError:
                pass
        
        ## TODO: Apply rename_map to primary key
        ## Remove primary_key if any columns in it are excluded or not in keep_only        
        
        return subRow
    
    def clone(self, new_parent = None):
        '''
        Create a clone of this row.
        
        Parameters
        ----------
        new_parent: ETLComponent
            (Optional) Change the parent of the clone to the passed value. 
        '''
        #pylint: disable=protected-access
        new_row = self.subset(new_parent= new_parent)
        #new_row._cached_column_set = self._cached_column_set
        #new_row._cached_positioned_column_set = self._cached_positioned_column_set
        return new_row

    @property
    def columns(self):
        """
        A list of the columns of this row (order not guaranteed in child instances).
        """
        return self._columns_in_order                
    
    @property
    def column_set(self):
        """
        An ImmutableSet of the the columns of this row. 
        Used to store different row configurations in a dictionary or set. 
        We don't get this from the parent since that might have more columns than we do.
        
        WARNING: The resulting set is not ordered. Do not use if the column order affects the operation.
        See positioned_column_set instead.
        """
        #=======================================================================
        # if self._cached_column_set is None:
        #     self._cached_column_set = get_cached_frozen_set(self.columns)
        # return self._cached_column_set
        #=======================================================================
        return get_cached_frozen_set(self.columns)
    
    @property 
    def column_count(self):
        return len(self)
    
    @property
    def positioned_column_set(self):
        """
        An ImmutableSet of the the tuples (column, position) for this row. Used to store different row configurations in a dictionary or set.
        
        Note: column_set would not always work here because the set is not ordered even though the columns are.
         
        We don't get this from the parent since that might have more columns than we do.
        """
        #=======================================================================
        # if self._cached_positioned_column_set is None:
        #     tpl_lst = list()
        #     for key, position in enumerate(self.columns_in_order()):
        #         tpl = (key, position)
        #         tpl_lst.append(tpl)    
        #     self._cached_positioned_column_set = get_cached_frozen_set(tpl_lst)
        # return self._cached_positioned_column_set
        #=======================================================================    
        tpl_lst = list()
        for key, position in enumerate(self.columns_in_order()):
            tpl = (key, position)
            tpl_lst.append(tpl)    
        return get_cached_frozen_set(tpl_lst)
        
    
    def column_position(self, column_name):
        '''
        Get the column position given a column name.
        
        Parameters
        ----------
        column_name: str
            The column name to find the position of        
        '''
        normalized_name = _get_name(column_name)
        return self._columns_in_order.index(normalized_name) + 1 ## index is 0 based, positions are 1 based
    
    def columns_in_order(self):
        """
        A list of the columns of this row in the order they were defined.
        
        Note: If the Row was created using a dict or dict like source, there was no order for the Row to work with. 
        """
        return self._columns_in_order
    
    def values_in_order(self):
        return [self[c] for c in self.columns_in_order()]        
    
    def __delitem__(self, col_name):
        #self._cached_column_set = None
        #self._cached_positioned_column_set = None
        normalized_col_name = _get_name(col_name)
        super().__delitem__(normalized_col_name)
        self._columns_in_order.remove(normalized_col_name)
        
    def _values_equal_coerce(self, val1, val2, col_name):
        if val1 is None:
            if val2 is None:
                return True
            else:
                return False
        elif val2 is None:
            return False
        elif type(val1) == type(val2):
            return val1 == val2
        elif type(val1) in self.NUMERIC_TYPES and type(val2) in self.NUMERIC_TYPES:
            return Decimal(val1) == Decimal(val2)
        else:
            msg = '{row} data type mismatch on compare of {col_name} {type1} vs {type2}'.format(row=self.name,
                                                                                                col_name=col_name,
                                                                                                type1=type(val1),
                                                                                                type2=type(val2),
                                                                                                )
            warnings.warn(msg)
            return str(val1) == str(val2)
    
    def compare_to(self, other_row, exclude= None, compare_only= None, coerce_types=True):
        '''
        Compare one RowCaseInsensitive to another. Returns a list of differences.
        '''
        if compare_only is not None:
            compare_only = set([other_row.get_column_name(c, raise_on_not_exist=False) for c in compare_only])
        
        if exclude is None:  
            exclude = []
        else:
            exclude = set([other_row.get_column_name(c, raise_on_not_exist=False) for c in exclude])
            
        differences_list = list()
        for other_col_name, other_col_value in other_row.items():
            if other_col_name not in exclude:
                if compare_only is None or other_col_name in compare_only:
                    existing_column_value = self[other_col_name]
                    if coerce_types:
                        values_equal= self._values_equal_coerce(existing_column_value, other_col_value, other_col_name)
                    else:
                        values_equal=  existing_column_value == other_col_value
                    if not values_equal:                    
                        differences_list.append(ColumnDifference(column_name= other_col_name, 
                                                                 old_value= existing_column_value, 
                                                                 new_value= other_col_value,
                                                                 )
                                            )
        return differences_list

    def transform(self, col_name, transform_function, *args, **kwargs):
        '''
        Apply a transformation to a column.  
        The transformation function must take the value to be transformed as it's first argument.
        
        Parameters
        ----------
        col_name: str
            The column name in the row to be transformed        
        transform_function: func
            The transformation function to use. It must take the value to be transformed as it's first argument.            
        args: list
            Positional arguments to pass to transform_function
        kwargs: dict
            Keyword arguments to pass to transform_function
        '''
        normalized_col_name, value = self._get_name_value_pair(col_name, raise_on_not_exist= True)
        value = transform_function(value, *args, **kwargs)
        super().__setitem__(normalized_col_name, value)