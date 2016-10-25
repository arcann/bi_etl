"""
Created on Sep 25, 2014

@author: woodd
"""
import logging
import warnings
from operator import attrgetter
from typing import Iterable

import bi_etl
from bi_etl.components.row import Row
from bi_etl.statistics import Statistics
from bi_etl.timer import Timer
from bi_etl.utility import dict_to_str
from sqlalchemy.sql.schema import Column

__all__ = ['ETLComponent']


class ETLComponent(Iterable):
    """
    Base class for ETLComponents (readers, writers, etc)
    
    Parameters
    ----------
    task: ETLTask
        The  instance to register in (if not None)
    
    logical_name: str
        The logical name of this source. Used for log messages.
        
    Attributes
    ----------
    log_first_row : boolean
        Should we log progress on the the first row read. *Only applies if Table is used as a source.*
        
    max_rows : int, optional
        The maximum number of rows to read. *Only applies if Table is used as a source.*
    
    primary_key: list
        The name of the primary key column(s). Only impacts trace messages.  Default=None.
    
    progress_frequency: int
        How often (in seconds) to output progress messages. None for no progress messages.
    
    progress_message: str
        The progress message to print. Default is ``"{logical_name} row # {row_number}"``. Note ``logical_name`` and ``row_number`` subs.    
            
    """
    DEFAULT_PROGRESS_FREQUENCY = 10  # Seconds
    DEFAULT_PROGRESS_MESSAGE = "{logical_name} current row # {row_number:,}"

    def __init__(self,
                 task,
                 logical_name = None,
                 **kwargs
                 ):        
        self.default_stats_id = 'read'
        self.task = task            
        self.logical_name = logical_name or id(self)
        self._primary_key = None
        self.__progress_frequency = self.DEFAULT_PROGRESS_FREQUENCY
        self.progress_message = self.DEFAULT_PROGRESS_MESSAGE
        self.max_rows = None        
        self.log_first_row = True
        self._column_names = None  
        # Note this calls the property setter
        self.__trace_data = False
        self._stats = Statistics(name=self.logical_name)
        self._rows_read = 0
        self.__enter_called = False
        self.__close_called = False
        self.read_batch_size = 1000
        self._iterator_applied_filters = False
        self.warnings_issued = 0
        self.warnings_limit = 100
        
        # self.log = logging.getLogger(__name__)
        self.log = logging.getLogger("{mod}.{cls}".format(mod = self.__class__.__module__, cls= self.__class__.__name__))
        bi_etl.utility.log_logging_level(self.log)
        
        # Register this component with it's parent task        
        if task is not None:
            task.register_object(self)

        # Should be the last call of every init            
        self.set_kwattrs(**kwargs) 

    def set_kwattrs(self, **kwargs):
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])
    
    def __repr__(self):
        return "{cls}(task={task},logical_name={logical_name},primary_key={primary_key})".format(
            cls= self.__class__.__name__,
            task= self.task,
            logical_name= self.logical_name,
            primary_key= self.primary_key,
            )
        
    def __str__(self):
        if self.logical_name is not None:
            if isinstance(self.logical_name, str):
                return self.logical_name
            else:
                return str(self.logical_name)
        else:
            return repr(self)
    
    def debug_log(self, state=True):
        if state:
            self.log.setLevel(logging.DEBUG)
            bi_etl.utility.log_logging_level(self.log)
        else:
            self.log.setLevel(logging.INFO)
            bi_etl.utility.log_logging_level(self.log)
    
    def clear_statistics(self):
        pass
    
    def check_row_limit(self):
        if not self.max_rows is None and self.rows_read >= self.max_rows:
            self.log.info('Max rows limit {rows:,} reached'.format(rows=self.max_rows))
            return True
        else:
            return False
    
    def log_progress(self, row, stats):
        try:
            self.log.info(self.progress_message.format(row_number= stats['rows_read'],
                                                       logical_name = self.logical_name,
                                                       **row
                                                       )
                          )
        except (IndexError, ValueError, KeyError) as e:
            self.log.error(repr(e))
            self.log.info("Bad format. Changing to default progress_message. Was {}".format(self.progress_message))
            self.progress_message = "{logical_name} row # {row_number:,}"

    def _obtain_column_names(self):
        """
        Override to provide a way to lookup column names as they are asked for.
        """
        pass
    
    @property
    def column_names(self):
        """
        Column names
        """
        if self._column_names is None:
            self._obtain_column_names()
        return self._column_names

    @column_names.setter
    def column_names(self, value):
        self._column_names = list(value)
        # Ensure names are unique
        name_dict = dict()
        duplicates = dict()
        for col_index, name in enumerate(self._column_names):
            if name in name_dict:
                # Duplicate name found
                # Keep a list of the instances
                if name in duplicates:
                    instance_list = duplicates[name]
                else:
                    instance_list = list()
                    # Put the first instance int to the list
                    instance_list.append(name_dict[name])                    
                instance_list.append(col_index)
                duplicates[name] = instance_list 
            else:
                name_dict[name] = col_index
    
        for name, instance_list in duplicates.items():
            for instance_number, instance_index in enumerate(instance_list):
                new_name = name + '_' + str(instance_number + 1)
                self.log.warning('Column name {} in position {} was duplicated and was renamed to {}'.format(self._column_names[instance_index],
                                                                                                             instance_index,
                                                                                                             new_name,
                                                                                                             ))
                self._column_names[instance_index] = new_name     
    
    @property
    def primary_key(self):
        try:
            if self._primary_key is not None and len(self._primary_key) > 0:
                if isinstance(self._primary_key[0], Column):
                    self._primary_key = list(map(attrgetter('name'), self._primary_key))
                return self._primary_key
            else:
                return None
        except AttributeError:
            return None

    @primary_key.setter
    def primary_key(self, value):
        if value is None:
            self._primary_key = []
        else:            
            if isinstance(value, str):
                value = [value]
            assert hasattr(value, '__iter__'), "Row primary_key must be iterable or string"
            self._primary_key = value            

    @property
    def trace_data(self):
        """
        boolean
            Should a debug message be printed with the parsed contents (as columns) of each row.
        """
        return self.__trace_data

    @trace_data.setter
    def trace_data(self, value):
        self.__trace_data = value
        # If we are tracing data, automatically set logging level to DEBUG
        if value:
            self.log.setLevel(logging.DEBUG)
    
    @property
    def progress_frequency(self) -> int:
        return self.__progress_frequency
    
    @progress_frequency.setter
    def progress_frequency(self, value: int):
        self.__progress_frequency = value
            
    @property
    def row_name(self):
        return str(self)
    
    def Row(self, data=None, name=None):
        """
        Make a new empty row with this components structure.
        """
        if name is None:
            name = self.row_name
        return Row(data, name=name, primary_key=self.primary_key, parent= self)
    
    @property
    def rows_read(self):
        """
        int
            The number of rows read and returned.
        """
        return self._rows_read
    
    def process_messages(self):
        """
        Processes messages for this components task.  Should be called somewhere in any row looping. The standard iterator does this for you.
        """
        if self.task is not None:
            self.task.process_messages()
    
    def _fetch_many_iter(self, result):
        while True:
            chunk = result.fetchmany(self.read_batch_size)
            if not chunk:
                break
            for row in chunk:
                yield row

    def _raw_rows(self):
        pass
                
    def iter_result(self,
                    result_list: object,
                    where_dict: dict = None,
                    progress_frequency: int = None,
                    stats_id: str = None,
                    parent_stats: Statistics = None) -> Iterable(Row):
        """
        yields
        ------
        row: :class:`~bi_etl.components.row.row_case_insensitive.Row`
            next row
        """
        if stats_id is None:
            stats_id = self.default_stats_id
            if stats_id is None:
                stats_id = 'read'
        stats = self.get_stats_entry(stats_id=stats_id, parent_stats=parent_stats)
        stats.timer.start()
        if progress_frequency is None:
            progress_frequency = self.__progress_frequency
        progress_timer = Timer()
        # Support result_list that is actually query result
        if hasattr(result_list, 'fetchmany'):
            # noinspection PyTypeChecker
            result_iter = self._fetch_many_iter(result_list)
        else:
            result_iter = result_list

        # noinspection PyTypeChecker
        for row in result_iter:
            if not self._iterator_applied_filters:
                if where_dict is not None:
                    passed_filter = True
                    for col, value in where_dict.items():
                        if row[col] != value:
                            passed_filter = False
                            break
                    if not passed_filter:
                        continue
                                
            # Add to global read counter
            self._rows_read += 1 
            # Add to current stat counter
            stats['rows_read'] += 1
            if stats['rows_read'] == 1:
                self.process_messages()
                stats['first row seconds'] = stats.timer.seconds_elapsed_formatted
                if self.log_first_row:
                    self.log_progress(row, stats)
            elif progress_frequency is not None:
                if 0 < progress_frequency < progress_timer.seconds_elapsed:
                    self.process_messages()
                    self.log_progress(row, stats)
                    progress_timer.reset()
                elif progress_frequency == 0:
                    # Log every row
                    self.process_messages()
                    self.log_progress(row, stats)            
            if self.trace_data:
                self.process_messages()
                self.log.debug("READ {name}:\n{row}".format(name=self, row=dict_to_str(row).encode('utf-8',errors='replace')))
            stats.timer.stop()
            if isinstance(row, Row):
                yield row
            else:
                yield self.Row(row)
            stats.timer.start()
            if self.check_row_limit():
                break            
        stats.timer.stop()
        
    def __iter__(self)-> Iterable(Row):
        """
        Iterate over all rows.
        
        Yields
        ------
        row: :class:`~bi_etl.components.row.row_case_insensitive.Row`
            :class:`~bi_etl.components.row.row_case_insensitive.Row` object with contents of a table/view row.
        """
        # Note: iter_result has a lot of important statistics keeping features
        # So we use that on top of _raw_rows 
        return self.iter_result(self._raw_rows()) 
        
    def where(self, criteria= None, order_by = None,  stats_id= None, parent_stats= None) -> Iterable(Row):
        assert order_by is None, '{} does not support order_by'.format(self)
        return self.iter_result(self._raw_rows(), where_dict=criteria, stats_id=stats_id, parent_stats=parent_stats)
        
    def close(self):
        self.__close_called = True
        if self.default_stats_id in self._stats:
            self._stats[self.default_stats_id].timer.stop()
    
    def __del__(self):
        # Close the any connections
        if hasattr(self, '__close_called'):
            if not self.__close_called:
                warnings.warn("{o} used without calling close.  It's suggested to use 'with' to control lifespan.".format(o=self), stacklevel=2)
                self.close()   
    
    def __enter__(self):
        self.__enter_called = True
        return self   
        
    def __exit__(self, exit_type, exit_value, exit_traceback):  
        # Close the any connections
        self.close()
        
    def _get_stats_parent(self, parent_stats=None):
        if parent_stats is None:
            # Set parent stats as etl_components root stats entry
            return self.statistics
        else:
            return parent_stats
        
    def get_stats_entry(self,
                        stats_id: str,
                        parent_stats: Statistics = None,
                        print_start_stop_times: bool = None):
        parent_stats = self._get_stats_parent(parent_stats)
        
        # Default to showing start stop times if parent_stats is self stats
        default_print_start_stop_times = (parent_stats == self._stats)
            
        if print_start_stop_times is None:
            print_start_stop_times = default_print_start_stop_times
        
        name = '{}.{}'.format(parent_stats.name, stats_id) 
        
        if stats_id not in parent_stats:
            stats = Statistics(name=name, print_start_stop_times= print_start_stop_times)
            parent_stats[stats_id] = stats
        else:
            stats = parent_stats[stats_id]
             
        return stats            
    
    def add_stats_entry(self, stats_id, stats_entry, parent_stats=None):
        parent_stats = self._get_stats_parent(parent_stats)
        
        id_nbr = 1
        base_stats_id = stats_id
        while stats_id in parent_stats:
            id_nbr += 1
            stats_id = '{} {}'.format(base_stats_id, id_nbr)
        name = '{}.{}'.format(parent_stats.name, stats_id)
        stats_entry.name = name
        parent_stats[stats_id] = stats_entry
        
    def get_unique_stats_entry(self, stats_id, parent_stats=None, print_start_stop_times= None):
        new_stats = Statistics(print_start_stop_times= print_start_stop_times)
        self.add_stats_entry(stats_id= stats_id, 
                             stats_entry= new_stats, 
                             parent_stats= parent_stats
                             )
        return new_stats 
        
    @property
    def statistics(self):
        return self._stats

