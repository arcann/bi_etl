"""
Created on Sep 25, 2014

@author: woodd
"""
import logging
import typing
import warnings
from bi_etl.scheduler.task import ETLTask
from operator import attrgetter
from typing import Iterable

from bi_etl.components.row.row import Row
from bi_etl.statistics import Statistics
from bi_etl.timer import Timer
from bi_etl.utility import dict_to_str
from bi_etl.components.row.row_iteration_header import RowIterationHeader
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
    logging_level_reported = False

    def __init__(self,
                 task: ETLTask,
                 logical_name: str=None,
                 **kwargs
                 ):        
        self.default_stats_id = 'read'
        self.task = task            
        self.logical_name = logical_name or "{cls}#{id}".format(cls=self.__class__.__name__,
                                                                id=id(self))
        self._primary_key = None
        self.__progress_frequency = self.DEFAULT_PROGRESS_FREQUENCY
        self.progress_message = self.DEFAULT_PROGRESS_MESSAGE
        self.max_rows = None        
        self.log_first_row = True
        self._column_names = None  
        # Note this calls the property setter
        self.__trace_data = False
        self._stats = Statistics(stats_id=self.logical_name)
        self._rows_read = 0
        self.__enter_called = False
        self.__close_called = False
        self.read_batch_size = 1000
        self._iterator_applied_filters = False
        self.warnings_issued = 0
        self.warnings_limit = 100

        # self.log = logging.getLogger(__name__)
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        if self.task is not None:
            if not ETLComponent.logging_level_reported:
                self.task.log_logging_level()
                ETLComponent.logging_level_reported = True
        self.row_object = Row
        
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
            cls=self.__class__.__name__,
            task=self.task,
            logical_name=self.logical_name,
            primary_key=self.primary_key,
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
            self.task.log_logging_level()
        else:
            self.log.setLevel(logging.INFO)
            self.task.log_logging_level()
    
    def clear_statistics(self):
        pass
    
    def check_row_limit(self):
        if self.max_rows is not None and self.rows_read >= self.max_rows:
            self.log.info('Max rows limit {rows:,} reached'.format(rows=self.max_rows))
            return True
        else:
            return False
    
    def log_progress(self, row: Row, stats):
        try:
            self.log.info(self.progress_message.format(row_number=stats['rows_read'],
                                                       logical_name=self.logical_name,
                                                       **row.as_dict
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
        self._column_names = []
    
    @property
    def column_names(self) -> typing.List[str]:
        """
        Column names
        """
        if self._column_names is None:
            self._obtain_column_names()
        # noinspection PyTypeChecker
        return self._column_names

    @column_names.setter
    def column_names(self, value: typing.List[str]):
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
                self.log.warning('Column name {} in position {} was duplicated and was renamed to {}'.format(
                    self._column_names[instance_index],
                    instance_index,
                    new_name,
                    ))
                self._column_names[instance_index] = new_name     
    
    @property
    def primary_key(self) -> list:
        try:
            if self._primary_key is not None and len(self._primary_key) > 0:
                if isinstance(self._primary_key[0], Column):
                    self._primary_key = list(map(attrgetter('name'), self._primary_key))
                return self._primary_key
            else:
                return []
        except AttributeError:
            return []

    @primary_key.setter
    def primary_key(self, value: Iterable[str]):
        if value is None:
            self._primary_key = []
        else:            
            if isinstance(value, str):
                value = [value]
            assert hasattr(value, '__iter__'), "Row primary_key must be iterable or string"
            self._primary_key = list(value)

    @property
    def trace_data(self) -> bool:
        """
        boolean
            Should a debug message be printed with the parsed contents (as columns) of each row.
        """
        return self.__trace_data

    @trace_data.setter
    def trace_data(self, value: bool):
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
    def row_name(self) -> str:
        return str(self)

    @property
    def rows_read(self) -> int:
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
                    columns_in_order: list = None,
                    criteria_dict: dict = None,
                    logical_name=None,
                    progress_frequency: int = None,
                    stats_id: str = None,
                    parent_stats: Statistics = None) -> Iterable[Row]:
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
        stats = self.get_unique_stats_entry(stats_id=stats_id, parent_stats=parent_stats)
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
        this_iteration_header = self.generate_iteration_header(
            logical_name=logical_name,
            columns_in_order=columns_in_order,
        )

        # noinspection PyTypeChecker
        for row in result_iter:
            if not self._iterator_applied_filters:
                if criteria_dict is not None:
                    passed_filter = True
                    for col, value in criteria_dict.items():
                        if row[col] != value:
                            passed_filter = False
                            break
                    if not passed_filter:
                        continue
            if not isinstance(row, self.row_object):
                row = self.row_object(this_iteration_header, data=row)
            # If we already have a Row object, we'll keep the same iteration header

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
                # noinspection PyTypeChecker
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
                self.log.debug("READ {name}:\n{row}".format(name=self,
                                                            row=dict_to_str(row).encode('utf-8',
                                                                                        errors='replace')
                                                            )
                              )
            stats.timer.stop()

            yield row
            stats.timer.start()
            if self.check_row_limit():
                break            
        stats.timer.stop()

    # noinspection PyProtocol
    def __iter__(self)-> Iterable[Row]:
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
        
    def where(self,
              criteria_list: list = None,
              criteria_dict: dict = None,
              order_by: list = None,
              column_list: typing.List[typing.Union[Column, str]] = None,
              exclude_cols: typing.List[typing.Union[Column, str]] = None,
              use_cache_as_source: bool = None,
              progress_frequency: int = None,
              stats_id: str = None,
              parent_stats: Statistics = None,
              ) -> Iterable[Row]:
        """

        Parameters
        ----------
        criteria_list:
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            http://docs.sqlalchemy.org/en/rel_1_0/core/selectable.html?highlight=where#sqlalchemy.sql.expression.Select.where
        criteria_dict:
            Dict keys should be columns, values are set using = or in
        order_by:
            List of sort keys
        column_list:
            List of columns (str or Column)
        exclude_cols
        use_cache_as_source
        progress_frequency
        stats_id
        parent_stats

        Returns
        -------
        rows

        """
        assert order_by is None, '{} does not support order_by'.format(self)
        assert criteria_list is None, '{} does not support criteria_list'.format(self)
        return self.iter_result(self._raw_rows(), criteria_dict=criteria_dict, stats_id=stats_id, parent_stats=parent_stats)
        
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
    
    def __enter__(self) -> 'ETLComponent':
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

        if stats_id not in parent_stats:
            stats = Statistics(stats_id=stats_id, parent=parent_stats, print_start_stop_times=print_start_stop_times)
        else:
            stats = parent_stats[stats_id]
             
        return stats

    def get_unique_stats_entry(self, stats_id, parent_stats=None, print_start_stop_times=None):
        parent_stats = self._get_stats_parent(parent_stats)
        stats_id = parent_stats.get_unique_stats_id(stats_id)
        new_stats = Statistics(stats_id=stats_id, parent=parent_stats, print_start_stop_times=print_start_stop_times)
        return new_stats 
        
    @property
    def statistics(self):
        return self._stats

    # noinspection PyPep8Naming
    def Row(self, data=None, logical_name=None, iteration_header=None):
        """
        Make a new empty row with this components structure.
        """
        if iteration_header is None:
            iteration_header = self.generate_iteration_header(logical_name=logical_name)
        return self.row_object(iteration_header=iteration_header, data=data)

    def generate_iteration_header(self, logical_name=None, columns_in_order=None):
        if logical_name is None:
            logical_name = self.row_name

        if columns_in_order is None:
            result_primary_key = self.primary_key
        else:
            result_primary_key = None

        return RowIterationHeader(logical_name=logical_name,
                                  primary_key=result_primary_key,
                                  parent=self,
                                  columns_in_order=columns_in_order,
                                  )
