"""
Created on Sep 25, 2014

@author: woodd
"""
import logging
import typing
import warnings
from operator import attrgetter
from typing import Iterable

from sqlalchemy.sql.schema import Column

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.row.row_status import RowStatus
from bi_etl.lookups.autodisk_lookup import AutoDiskLookup
from bi_etl.lookups.lookup import Lookup
from bi_etl.scheduler.task import ETLTask
from bi_etl.statistics import Statistics
from bi_etl.timer import Timer
from bi_etl.utility import dict_to_str

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
                 logical_name: str = None,
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
        if not hasattr(self, '_column_names'):
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

        self.__lookups = dict()
        # Default lookup class is AutoDiskLookup
        self.default_lookup_class = AutoDiskLookup
        self.default_lookup_class_kwargs = dict()
        if self.task is not None:
            self.default_lookup_class_kwargs['config'] = self.task.config

        self.cache_filled = False
        self.cache_clean = False

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
            self.process_messages()
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
                stats['first row seconds'] = stats.timer.seconds_elapsed_formatted
                if self.log_first_row:
                    self.log_progress(row, stats)
            elif progress_frequency is not None:
                # noinspection PyTypeChecker
                if 0 < progress_frequency < progress_timer.seconds_elapsed:
                    self.log_progress(row, stats)
                    progress_timer.reset()
                elif progress_frequency == 0:
                    # Log every row
                    self.log_progress(row, stats)
            if self.trace_data:
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

    def get_column_name(self, column):
        if column in self.column_names:
            return column
        else:
            raise KeyError(f'{self} does not have a column named {column}, it does have {self.column_names}')

    def define_lookup(self,
                      lookup_name: str,
                      lookup_keys: list,
                      lookup_class=None,
                      lookup_class_kwargs=None,
                      ):
        """
        Define a new lookup.

        Parameters
        ----------
        lookup_name: str
            Name for the lookup. Used to refer to it later.

        lookup_keys: list
            list of lookup key columns

        lookup_class: Class
            Optional python class to use for the lookup. Defaults to value of default_lookup_class attribute.

        lookup_class_kwargs: dict
            Optional dict of additional parameters to pass to lookup constructor. Defaults to empty dict.
        """
        if not self.__lookups:
            self.__lookups = dict()
        if lookup_name in self.__lookups:
            self.log.warning("{} define_lookup is overriding the {} lookup with {}".format(
                self,
                lookup_name,
                lookup_keys
            )
            )
        if lookup_class is None:
            lookup_class = self.default_lookup_class
        if lookup_class_kwargs is None:
            lookup_class_kwargs = self.default_lookup_class_kwargs

        for key in lookup_keys:
            self.get_column_name(key)

        lookup = lookup_class(lookup_name="{}.{}".format(self.logical_name, lookup_name),
                              lookup_keys=lookup_keys,
                              parent_component=self,
                              **lookup_class_kwargs
                              )
        self.__lookups[lookup_name] = lookup
        return lookup

    @property
    def lookups(self):
        return self.__lookups

    def get_lookup(self, lookup_name) -> Lookup:
        self._check_pk_lookup()

        try:
            return self.__lookups[lookup_name]
        except KeyError:
            raise KeyError("{} does not contain a lookup named {}".format(self, lookup_name))

    def get_lookup_keys(self, lookup_name):
        return self.get_lookup(lookup_name).lookup_keys

    def get_lookup_tuple(self, lookup_name, row):
        return self.__lookups[lookup_name].get_hashable_combined_key(row)

    def init_cache(self):
        """
        Initialize all lookup caches as empty.
        """
        self.cache_filled = False
        for lookup in self.__lookups.values():
            lookup.init_cache()

    def clear_cache(self):
        """
        Clear all lookup caches.
        Sets to un-cached state (unknown state v.s. empty state which is what init_cache gives)
        """
        self.cache_filled = False
        for lookup in self.__lookups.values():
            lookup.clear_cache()

    def cache_row(self, row, allow_update=False):
        for lookup in self.__lookups.values():
            if lookup.cache_enabled:
                lookup.cache_row(row, allow_update)

    def cache_commit(self):
        for lookup in self.__lookups.values():
            lookup.commit()

    def uncache_row(self, row):
        for lookup in self.__lookups.values():
            lookup.uncache_row(row)

    def uncache_where(self, key_names, key_values_dict):
        if self.__lookups:
            for lookup in self.__lookups.values():
                lookup.uncache_where(key_names=key_names, key_values_dict=key_values_dict)

    def _check_pk_lookup(self):
        """
        Placeholder for components with PKs

        :return:
        """
        pass

    def fill_cache(self,
                   progress_frequency: float = 10,
                   progress_message="{component} fill_cache current row # {row_number:,}",
                   criteria_list: list = None,
                   criteria_dict: dict = None,
                   column_list: list = None,
                   exclude_cols: list = None,
                   order_by: list = None,
                   assume_lookup_complete: bool = None,
                   row_limit: int = None,
                   parent_stats: Statistics = None,
                   ):
        """
        Fill all lookup caches from the table.

        Parameters
        ----------
        progress_frequency : int, optional
            How often (in seconds) to output progress messages. Default 10. None for no progress messages.
        progress_message : str, optional
            The progress message to print.
            Default is ``"{component} fill_cache current row # {row_number:,}"``. Note ``logical_name`` and ``row_number``
            substitutions applied via :func:`format`.
        criteria_list : string or list of strings
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            https://goo.gl/JlY9us
        criteria_dict : dict
            Dict keys should be columns, values are set using = or in
        column_list:
            List of columns to include
        exclude_cols: list
            Optional. Columns to exclude when filling the cache
        order_by: list
            list of columns to sort by when filling the cache (helps range caches)
        assume_lookup_complete: boolean
            Should later lookup calls assume the cache is complete?
            If so, lookups will raise an Exception if a key combination is not found.
            Default to False if filtering criteria was used, otherwise defaults to True.
        row_limit: int
            limit on number of rows to cache.
        parent_stats: bi_etl.statistics.Statistics
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        """
        self._check_pk_lookup()

        # If we have, or can build a natural key
        if hasattr(self, 'natural_key'):
            if self.natural_key:
                # Make sure to build the lookup so it can be filled
                if hasattr(self, 'ensure_nk_lookup'):
                    self.ensure_nk_lookup()

        assert isinstance(progress_frequency, int), "fill_cache progress_frequency expected to be int not {}".format(
            type(progress_frequency))
        self.log.info(f'{self}.fill_cache started')
        stats = self.get_unique_stats_entry('fill_cache', parent_stats=parent_stats)
        stats.timer.start()

        self.clear_cache()
        progress_timer = Timer()
        # Temporarily turn off read progress messages
        saved_read_progress = self.__progress_frequency
        self.__progress_frequency = None
        rows_read = 0
        limit_reached = False

        self.init_cache()

        for row in self.where(
                criteria_list=criteria_list,
                criteria_dict=criteria_dict,
                column_list=column_list,
                exclude_cols=exclude_cols,
                order_by=order_by,
                use_cache_as_source=False,
                parent_stats=stats
        ):
            rows_read += 1
            if row_limit is not None and rows_read >= row_limit:
                limit_reached = True
                self.log.warning(f"{self}.fill_cache aborted at limit {rows_read:,} rows of data")

                self.log.warning(f"{self} proceeding without using cache lookup")

                # We'll operate in partially cached mode
                self.cache_filled = False
                self.cache_clean = False
                break
            # Actually cache the row now
            row.status = RowStatus.existing
            self.cache_row(row, allow_update=False)

            # noinspection PyTypeChecker
            if 0.0 < progress_frequency <= progress_timer.seconds_elapsed:
                self.process_messages()
                progress_timer.reset()
                self.log.info(progress_message.format(
                    row_number=rows_read,
                    component=self,
                    table=self,
                )
                )
        if not limit_reached:
            self.cache_filled = True
            self.cache_clean = True

            self.log.info(f"{self}.fill_cache cached {rows_read:,} rows of data")

            ram_size = 0
            disk_size = 0
            for lookup in self.__lookups.values():
                this_ram_size = lookup.get_memory_size()
                this_disk_size = lookup.get_disk_size()
                self.log.info('Lookup {} Rows {:,} Size RAM= {:,} bytes DISK={:,} bytes'.format(
                    lookup,
                    len(lookup),
                    this_ram_size,
                    this_disk_size
                )
                )
                ram_size += this_ram_size
                disk_size += this_disk_size
            self.log.info('Note: RAM sizes do not add up as memory lookups share row objects')
            self.log.info('Total Lookups Size DISK={:,} bytes'.format(disk_size))

            for lookup_name, lookup in self.__lookups.items():
                stats[f'rows in {lookup_name}'] = len(lookup)

        self.cache_commit()
        stats.timer.stop()
        # Restore read progress messages
        self.__progress_frequency = saved_read_progress

    def get_by_lookup(self,
                      lookup_name: str,
                      source_row: Row,
                      stats_id: str = 'get_by_lookup',
                      parent_stats: typing.Optional[Statistics] = None,
                      fallback_to_db: bool = False,
                      ) -> Row:
        """
        Get by an alternate key.
        Returns a :class:`~bi_etl.components.row.row_case_insensitive.Row`

        Throws:
            NoResultFound
        """
        stats = self.get_stats_entry(stats_id, parent_stats=parent_stats)
        stats.print_start_stop_times = False
        stats.timer.start()

        self._check_pk_lookup()

        lookup = self.get_lookup(lookup_name)
        assert isinstance(lookup, Lookup)

        return lookup.find(row=source_row,
                           fallback_to_db=fallback_to_db,
                           stats=stats
                           )
