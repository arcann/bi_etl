"""
Created on Sep 25, 2014

@author: Derek Wood
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import functools
import logging
import warnings
from collections import defaultdict
from operator import attrgetter
from typing import *

from sqlalchemy.sql.schema import Column

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.row.row_status import RowStatus
from bi_etl.exceptions import ColumnMappingError
from bi_etl.lookups.autodisk_lookup import AutoDiskLookup
from bi_etl.lookups.lookup import Lookup
from bi_etl.statistics import Statistics
from bi_etl.timer import Timer
from bi_etl.utility import dict_to_str

if TYPE_CHECKING:
    from bi_etl.scheduler.task import ETLTask

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
        Should we log progress on the first row read. *Only applies if used as a source.*
        
    max_rows : int, optional
        The maximum number of rows to read. *Only applies if Table is used as a source.*

    progress_message: str
        The progress message to print. Default is ``"{logical_name} row # {row_number}"``.
        Note ``logical_name`` and ``row_number`` subs.
            
    """
    DEFAULT_PROGRESS_FREQUENCY = 10
    """
    Default for number of seconds between progress messages when reading from this component.
    See :py:attr:`ETLComponent.progress_frequency`` to override.
    """

    DEFAULT_PROGRESS_MESSAGE = "{logical_name} current row # {row_number:,}"
    """
    Default progress message when reading from this component.
    See :py:attr:`ETLComponent.progress_message`` to override. 
    """

    FULL_ITERATION_HEADER = 'full'
    """
    Constant value passed into :py:meth:`ETLComponent.Row` to request all columns in the row.
    **Deprecated**: Please use :py:meth:`ETLComponent.full_row_instance` to get a row with all columns.
    """

    logging_level_reported = False
    """
    Has the logging level of this component been reported (logged) yet?
    Stored at class level so that it can be logged only once.
    """

    def __init__(
            self,
            task: Optional[ETLTask],
            logical_name: Optional[str] = None,
            **kwargs
    ):
        self.default_stats_id = 'read'
        self.task = task
        self.logical_name = logical_name or f"{self.__class__.__name__}#{id(self)}"
        self._primary_key = None
        self._primary_key_tuple = tuple()
        self.__progress_frequency = self.DEFAULT_PROGRESS_FREQUENCY
        self.progress_message = self.DEFAULT_PROGRESS_MESSAGE
        self.max_rows = None
        self.log_first_row = True
        if not hasattr(self, '_column_names'):
            self._column_names = None
        self._column_names_set = None
        # Note this calls the property setter
        self.__trace_data = False
        self._stats = Statistics(stats_id=self.logical_name)
        self._rows_read = 0
        self.__enter_called = False
        self.__close_called = False
        self.read_batch_size = 1000
        self._iterator_applied_filters = False
        self._empty_iteration_header = None
        self._full_iteration_header = None
        self.time_first_read = True
        self.time_all_reads = False
        self.warnings_issued = 0
        self.warnings_limit = 100

        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        if self.task is not None:
            if not ETLComponent.logging_level_reported:
                self.task.log_logging_level()
                ETLComponent.logging_level_reported = True
        self.row_object = Row

        # Register this component with its parent task
        if task is not None:
            task.register_object(self)

        self.__lookups = dict()
        # Default lookup class is AutoDiskLookup
        self.default_lookup_class = AutoDiskLookup
        self.default_lookup_class_kwargs = dict()

        self.sanity_check_default_iterator_done = False
        self.sanity_checked_sources = set()
        self._row_builders = dict()

        self.ignore_source_not_in_target = False
        self.ignore_target_not_in_source = False
        self.raise_on_source_not_in_target = False
        self.raise_on_target_not_in_source = False

        self.cache_filled = False
        self.cache_clean = False

        # Should be the last call of every init            
        self.set_kwattrs(**kwargs)

    @staticmethod
    def kwattrs_order() -> Dict[str, int]:
        """
        Certain values need to be set before others in order to work correctly.
        This method should return a dict mapping those key values = arg name to
        a value less than the default of 9999, which will be used for any arg
        not explicitly listed here.
        """
        return {
        }

    def set_kwattrs(self, **kwargs):
        # Certain values need to be set before others in order to work correctly
        kw_order = defaultdict(lambda: 9999)
        kw_order.update(self.kwattrs_order())

        kw_arg_tuple_list = {arg: kw_order[arg] for arg in kwargs}

        for attr in sorted(kw_arg_tuple_list, key=lambda x: kw_arg_tuple_list[x]):
            if attr == 'column_names':
                # Use the setter
                self.column_names = kwargs[attr]
            else:
                setattr(self, attr, kwargs[attr])

    def __repr__(self):
        return f"{self.__class__.__name__}" \
               f"(task={self.task},logical_name={self.logical_name},primary_key={self.primary_key})"

    def __str__(self):
        if self.logical_name is not None:
            if isinstance(self.logical_name, str):
                return self.logical_name
            else:
                return str(self.logical_name)
        else:
            return repr(self)

    def __reduce_ex__(self, protocol):
        return (
            # A callable object that will be called to create the initial version of the object.
            self.__class__,

            # A tuple of arguments for the callable object.
            # An empty tuple must be given if the callable does not accept any argument
            (self.task, self.logical_name),

            # Optionally, the object’s state, which will be passed to the object’s __setstate__()
            # method as previously described.
            # If the object has no such method then, the value must be a dictionary,
            # and it will be added to the object’s __dict__ attribute.
            self.__dict__,

            # Optionally, an iterator (and not a sequence) yielding successive items.
            # These items will be appended to the object either using obj.append(item) or,
            # in batch, using obj.extend(list_of_items).

            # Optionally, an iterator (not a sequence) yielding successive key-value pairs.
            # These items will be stored to the object using obj[key] = value

            # PROTOCOL 5+ only
            # Optionally, a callable with a (obj, state) signature.
            # This callable allows the user to programmatically control
            # the state-updating behavior of a specific object,
            # instead of using obj’s static __setstate__() method.
            # If not None, this callable will have priority over obj’s __setstate__().
        )

    @property
    def empty_iteration_header(self) -> RowIterationHeader:
        if self._empty_iteration_header is None:
            self._empty_iteration_header = self.generate_iteration_header(
                logical_name='empty',
                columns_in_order=[],
            )
        return self._empty_iteration_header

    @property
    def full_iteration_header(self) -> RowIterationHeader:
        if self._full_iteration_header is None:
            self._full_iteration_header = self.generate_iteration_header()
        return self._full_iteration_header

    def debug_log(
            self,
            state: bool = True
    ):
        if state:
            self.log.setLevel(logging.DEBUG)
            self.task.log_logging_level()
        else:
            self.log.setLevel(logging.INFO)
            self.task.log_logging_level()

    def clear_statistics(self):
        pass

    @property
    def check_row_limit(self):
        if self.max_rows is not None and self.rows_read >= self.max_rows:
            self.log.info(f'Max rows limit {self.max_rows:,} reached')
            return True
        else:
            return False

    def log_progress(
            self,
            row: Row,
            stats: Statistics,
    ):
        try:
            self.log.info(
                self.progress_message.format(
                    row_number=stats['rows_read'],
                    logical_name=self.logical_name,
                    **row.as_dict
                    )
                )
        except (IndexError, ValueError, KeyError) as e:
            self.log.error(repr(e))
            self.log.info(f"Bad format. Changing to default progress_message. Was {self.progress_message}")
            self.progress_message = "{logical_name} row # {row_number:,}"

    def _obtain_column_names(self):
        """
        Override to provide a way to lookup column names as they are asked for.
        """
        self._column_names = []

    @property
    def column_names(self) -> List[str]:
        """
        The list of column names for this component.
        """
        if self._column_names is None:
            self._obtain_column_names()
        # noinspection PyTypeChecker
        return self._column_names

    @column_names.setter
    def column_names(
            self,
            value: List[str],
    ):
        if isinstance(value, list):
            self._column_names = value
        else:
            self._column_names = list(value)
        self._column_names_set = None
        self._full_iteration_header = None
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
                self.log.warning(
                    f'Column name {self._column_names[instance_index]} in position {instance_index} was duplicated and was renamed to {new_name}'
                )
                self._column_names[instance_index] = new_name

    @property
    def column_names_set(self) -> set:
        """
        A set containing the column names for this component.
        Usable to quickly check if the component contains a certain column.
        """
        # TODO: Make this a frozenset

        if self._column_names_set is None:
            self._column_names_set = set(self.column_names)
        return self._column_names_set

    @property
    def primary_key(self) -> list:
        """
        The name of the primary key column(s). Only impacts trace messages.  Default=Empty list.
        """
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
        """
        :noindex:
        """
        if value is None:
            self._primary_key = []
        else:
            if isinstance(value, str):
                value = [value]
            assert hasattr(value, '__iter__'), "Row primary_key must be iterable or string"
            self._primary_key = list(value)
        self._primary_key_tuple = tuple(self.primary_key)

    @property
    def primary_key_tuple(self) -> tuple:
        """
        The name of the primary key column(s) in a tuple. Used when a hashable PK definition is needed.
        """
        return self._primary_key_tuple

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
        """
        How often (in seconds) to output progress messages. None for no progress messages.
        """
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

    def _fetch_many_iter(self, result):
        while True:
            chunk = result.fetchmany(self.read_batch_size)
            if not chunk:
                break
            for row in chunk:
                yield row

    def _raw_rows(self):
        pass

    def iter_result(
            self,
            result_list: object,
            columns_in_order: Optional[list] = None,
            criteria_dict: Optional[dict] = None,
            logical_name: Optional[str] = None,
            progress_frequency: Optional[int] = None,
            stats_id: Optional[str] = None,
            parent_stats: Optional[Statistics] = None,
    ) -> Iterable[Row]:
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
        if self.time_all_reads or (self._rows_read == 0 and self.time_first_read):
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
        this_iteration_header = None

        # noinspection PyTypeChecker
        for row in result_iter:
            if this_iteration_header is None:
                this_iteration_header = self.generate_iteration_header(
                    columns_in_order=columns_in_order,
                    logical_name=logical_name,
                )
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
            if self.time_first_read:
                if stats['rows_read'] == 1:
                    stats['first row seconds'] = stats.timer.seconds_elapsed
                    if self.log_first_row:
                        self.log_progress(row, stats)

            if progress_frequency is not None:
                # noinspection PyTypeChecker
                if 0 < progress_frequency < progress_timer.seconds_elapsed:
                    self.log_progress(row, stats)
                    progress_timer.reset()
                elif progress_frequency == 0:
                    # Log every row
                    self.log_progress(row, stats)
            if self.trace_data:
                row_str = dict_to_str(row).encode(
                    'utf-8',
                    errors='replace'
                )
                self.log.debug(
                    f"READ {self}:\n{row_str}"
                )
            if self.time_all_reads:
                stats.timer.stop()

            yield row
            if self.time_all_reads:
                stats.timer.start()
            if self.check_row_limit:
                break
        if hasattr(result_list, 'close'):
            result_list.close()
        if self.time_all_reads:
            stats.timer.stop()

    # noinspection PyProtocol
    def __iter__(self) -> Iterable[Row]:
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

    def where(
            self,
            criteria_list: Optional[list] = None,
            criteria_dict: Optional[dict] = None,
            order_by: Optional[list] = None,
            column_list: List[Union[Column, str]] = None,
            exclude_cols: FrozenSet[Union[Column, str]] = None,
            use_cache_as_source: Optional[bool] = None,
            progress_frequency: Optional[int] = None,
            stats_id: Optional[str] = None,
            parent_stats: Optional[Statistics] = None,
    ) -> Iterable[Row]:
        """

        Parameters
        ----------
        criteria_list:
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            https://docs.sqlalchemy.org/en/14/core/selectable.html?highlight=where#sqlalchemy.sql.expression.Select.where
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
        assert order_by is None, f'{self} does not support order_by'
        assert criteria_list is None, f'{self} does not support criteria_list'
        return self.iter_result(
            self._raw_rows(),
            criteria_dict=criteria_dict,
            stats_id=stats_id,
            parent_stats=parent_stats,
        )

    @property
    def is_closed(self):
        return self.__close_called

    def close(self, error: bool = False):
        self.__close_called = True
        if self.default_stats_id in self._stats:
            self._stats[self.default_stats_id].timer.stop()

    def __del__(self):
        # Close any connections and cleanup
        if hasattr(self, '__close_called'):
            if not self.__close_called:
                warnings.warn(
                    f"{self} used without calling close.  "
                    f"It's suggested to use 'with' to control lifespan.",
                    stacklevel=2
                )
                self.close(error=False)

    def __enter__(self) -> 'ETLComponent':
        self.__enter_called = True
        return self

    def __exit__(self, exit_type, exit_value, exit_traceback):
        # Close any connections and cleanup
        self.close(error=False)

    def _get_stats_parent(
            self,
            parent_stats: Optional[Statistics] = None,
    ):
        if parent_stats is None:
            # Set parent stats as etl_components root stats entry
            return self.statistics
        else:
            return parent_stats

    def get_stats_entry(
            self,
            stats_id: str,
            parent_stats: Optional[Statistics] = None,
            print_start_stop_times: Optional[bool] = None
    ):
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

    def get_unique_stats_entry(
            self,
            stats_id: str,
            parent_stats: Optional[Statistics] = None,
            print_start_stop_times: Optional[bool] = None,
    ):
        parent_stats = self._get_stats_parent(parent_stats)
        stats_id = parent_stats.get_unique_stats_id(stats_id)
        new_stats = Statistics(stats_id=stats_id, parent=parent_stats, print_start_stop_times=print_start_stop_times)
        return new_stats

    @property
    def statistics(self):
        return self._stats

    # noinspection PyPep8Naming
    def Row(
        self,
        data: Union[MutableMapping, Iterator, None] = None,
        iteration_header: Union[RowIterationHeader, str, None] = None,
    ) -> Row:
        """
        Make a new empty row with this components structure.
        """
        if iteration_header is None:
            iteration_header = self.empty_iteration_header
        elif iteration_header == self.FULL_ITERATION_HEADER:
            warnings.warn('Use of FULL_ITERATION_HEADER is deprecated. Please use full_row_instance instead.')
            iteration_header = self.full_iteration_header
        return self.row_object(iteration_header=iteration_header, data=data)

    def full_row_instance(
        self,
        data: Union[MutableMapping, Iterator, None] = None,
    ) -> Row:
        """
        Build a full row (all columns) using the source data.

        Note: If data is passed here, it uses :py:meth:`bi_etl.components.row.row.Row.update` to map the data
        into the columns.  That is nicely automatic, but slower since it has to try various
        ways to read the data container object.

        Consider using the appropriate one of the more specific update methods
        based on the source data container.

        * :py:meth:`bi_etl.components.row.row.Row.update_from_namedtuple`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_dict`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_row_proxy`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_tuples`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_dataclass`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_pydantic`
        * :py:meth:`bi_etl.components.row.row.Row.update_from_values`
        """
        return self.row_object(
            iteration_header=self.full_iteration_header,
            data=data,
        )

    def generate_iteration_header(
            self,
            logical_name: Optional[str] = None,
            columns_in_order: Optional[list] = None,
            result_primary_key: Optional[list] = None,
    ) -> RowIterationHeader:
        if logical_name is None:
            logical_name = self.row_name

        if columns_in_order is None:
            columns_in_order = self.column_names

        if result_primary_key is None:
            result_primary_key = self.primary_key

        # noinspection PyPep8Naming
        RowIterationHeader_Class = self.row_object.RowIterationHeader_Class

        return RowIterationHeader_Class(
            logical_name=logical_name,
            primary_key=result_primary_key,
            parent=self,
            columns_in_order=columns_in_order,
        )

    def get_column_name(
            self,
            column: str,
    ):
        if column in self.column_names:
            return column
        else:
            raise KeyError(f'{self} does not have a column named {column}, it does have {self.column_names}')

    @functools.lru_cache(maxsize=10)
    def get_qualified_lookup_name(self, base_lookup_name: str) -> str:
        if '.' in base_lookup_name:
            return base_lookup_name
        else:
            return f"{self.logical_name}.{base_lookup_name}"

    def define_lookup(
            self,
            lookup_name: str,
            lookup_keys: list,
            lookup_class: Type[Lookup] = None,
            lookup_class_kwargs: Optional[dict] = None,
    ):
        """
        Define a new lookup.

        Parameters
        ----------
        lookup_name:
            Name for the lookup. Used to refer to it later.

        lookup_keys:
            list of lookup key columns

        lookup_class:
            Optional python class to use for the lookup. Defaults to value of default_lookup_class attribute.

        lookup_class_kwargs:
            Optional dict of additional parameters to pass to lookup constructor. Defaults to empty dict.
        """
        if not self.__lookups:
            self.__lookups = dict()

        lookup_name = self.get_qualified_lookup_name(lookup_name)

        if lookup_name in self.__lookups:
            self.log.warning(
                f"{self} define_lookup is overriding the {lookup_name} lookup with {lookup_keys}"
            )
        if lookup_class is None:
            lookup_class = self.default_lookup_class
        if lookup_class_kwargs is None:
            lookup_class_kwargs = self.default_lookup_class_kwargs

        for key in lookup_keys:
            self.get_column_name(key)

        lookup = lookup_class(
            config=self.task.config,
            lookup_name=lookup_name,
            lookup_keys=lookup_keys,
            parent_component=self,
            **lookup_class_kwargs
        )
        self.__lookups[lookup_name] = lookup
        return lookup

    @property
    def lookups(self):
        return self.__lookups

    @functools.lru_cache(maxsize=10)
    def get_lookup(
            self,
            lookup_name: str,
    ) -> Lookup:
        self._check_pk_lookup()

        try:
            return self.__lookups[lookup_name]
        except KeyError:
            if '.' not in lookup_name:
                qual_lookup_name = f"{self.logical_name}.{lookup_name}"
                try:
                    return self.__lookups[qual_lookup_name]
                except KeyError:
                    raise KeyError(f"{self} does not contain a lookup named {lookup_name} or {qual_lookup_name}")
            else:
                raise KeyError(f"{self} does not contain a lookup named {lookup_name}")

    @functools.lru_cache(maxsize=10)
    def get_lookup_keys(
            self,
            lookup_name: str,
    ) -> list:
        return self.get_lookup(lookup_name).lookup_keys

    def get_lookup_tuple(
            self,
            lookup_name: str,
            row: Row,
    ) -> tuple:
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

    def cache_row(
            self,
            row: Row,
            allow_update: bool = False,
            allow_insert: bool = True,
    ):
        for lookup in self.__lookups.values():
            if lookup.cache_enabled:
                lookup.cache_row(
                    row=row,
                    allow_update=allow_update,
                    allow_insert=allow_insert,
                )

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

    def sanity_check_source_mapping(
            self,
            source_definition: ETLComponent,
            source_name: str = None,
            source_excludes: frozenset = None,
            target_excludes: frozenset = None,
            ignore_source_not_in_target: bool = None,
            ignore_target_not_in_source: bool = None,
            raise_on_source_not_in_target: bool = None,
            raise_on_target_not_in_source: bool = None,
    ):
        if ignore_source_not_in_target is None:
            ignore_source_not_in_target = self.ignore_source_not_in_target
        if ignore_target_not_in_source is None:
            ignore_target_not_in_source = self.ignore_target_not_in_source
        if raise_on_source_not_in_target is None:
            raise_on_source_not_in_target = self.raise_on_source_not_in_target
        if raise_on_target_not_in_source is None:
            raise_on_target_not_in_source = self.raise_on_target_not_in_source

        target_set = set(self.column_names)
        target_col_list = list(self.column_names)
        if target_excludes is not None:
            for exclude in target_excludes:
                if exclude is not None:
                    if exclude in target_set:
                        target_set.remove(exclude)

        if isinstance(source_definition, ETLComponent):
            source_col_list = source_definition.column_names
            if source_name is None:
                source_name = str(source_definition)
        elif isinstance(source_definition, Row):
            source_col_list = source_definition
        elif isinstance(source_definition, set):
            source_col_list = list(source_definition)
        elif isinstance(source_definition, list):
            source_col_list = source_definition
        else:
            self.log.error(
                "check_column_mapping source_definition needs to be ETLComponent, Row, set, or list. "
                f"Got {type(source_definition)}"
            )
            return False

        if source_name is None:
            source_name = ''

        source_set = set(source_col_list)
        if not ignore_source_not_in_target:
            if source_excludes is None:
                source_excludes = frozenset()
            pos = 0
            for src_col in source_col_list:
                pos += 1
                if src_col not in source_excludes:
                    if src_col not in target_set:
                        if isinstance(source_definition, set):
                            pos = 'N/A'
                        msg = f"Sanity Check: Source {source_name} contains column " \
                              f"{src_col}({pos}) not in target {self} ({target_set})"
                        if raise_on_source_not_in_target:
                            raise ColumnMappingError(msg)
                        else:
                            self.log.warning(msg)

        if not ignore_target_not_in_source:
            show_source_defn = False
            for tgtCol in target_set:
                if tgtCol not in source_set:
                    pos = target_col_list.index(tgtCol)
                    msg = f"Sanity Check: Target {self} contains column {tgtCol}(col {pos}) not in source {source_name}"
                    if raise_on_target_not_in_source:
                        raise ColumnMappingError(msg)
                    else:
                        show_source_defn = True
                        self.log.warning(msg)
            if show_source_defn:
                self.log.warning(f"Source {source_name} definition {source_definition}")

    def sanity_check_example_row(
            self,
            example_source_row,
            source_excludes=None,
            target_excludes=None,
            ignore_source_not_in_target=None,
            ignore_target_not_in_source=None,
            ):
        self.sanity_check_source_mapping(
            example_source_row,
            example_source_row.name,
            source_excludes=source_excludes,
            target_excludes=target_excludes,
            ignore_source_not_in_target=ignore_source_not_in_target,
            ignore_target_not_in_source=ignore_target_not_in_source,
            )

    def _get_coerce_method_name_by_str(self, target_column_name: str) -> str:
        return ''

    def build_row(
            self,
            source_row: Row,
            source_excludes: Optional[frozenset] = None,
            target_excludes: Optional[frozenset] = None,
            stat_name: str = 'build_row_safe',
            parent_stats: Optional[Statistics] = None,
    ) -> Row:
        """
        Use a source row to build a row with correct data types for this table.

        Parameters
        ----------
        source_row
        source_excludes
        target_excludes
        stat_name
            Name of this step for the ETLTask statistics. Default = 'build rows'
        parent_stats

        Returns
        -------
            Row
        """
        build_row_stats = self.get_stats_entry(stat_name, parent_stats=parent_stats)
        build_row_stats.print_start_stop_times = False
        build_row_stats.timer.start()
        build_row_stats['calls'] += 1

        try:
            iteration_id = source_row.iteration_header.iteration_id
            build_row_key = (iteration_id, source_excludes, target_excludes)
            needs_builder = build_row_key not in self._row_builders
        except AttributeError:
            if not isinstance(source_row, Row):
                raise ValueError(f'source_row is not a Row instead it is {type(source_row)}')
            raise
        except TypeError:
            if source_excludes is not None and not isinstance(source_excludes, frozenset):
                raise TypeError(f'source_excludes is not a frozenset instead it is {type(source_excludes)}')
            if target_excludes is not None and not isinstance(target_excludes, frozenset):
                raise TypeError(f'target_excludes is not a frozenset instead it is {type(target_excludes)}')
            raise

        if needs_builder:
            # Check row mapping and make a row builder for this source

            self.sanity_check_example_row(
                example_source_row=source_row,
                source_excludes=source_excludes,
                target_excludes=target_excludes,
            )

            source_row_columns = source_row.columns_in_order
            if source_excludes is not None:
                source_row_columns = [column_name for column_name in source_row_columns
                                      if column_name not in source_excludes
                                      ]

            target_column_set = self.column_names_set
            if target_excludes is not None:
                target_column_set = target_column_set - target_excludes

            new_row_columns = [column_name for column_name in source_row_columns if column_name in target_column_set]

            build_row_method_name = f"_build_row_{iteration_id}_{id(source_excludes)}_{id(target_excludes)}"

            new_row_iteration_header = self.generate_iteration_header(
                logical_name=f'{self} built from source {source_row.iteration_header.iteration_id} '
                             f'{source_row.iteration_header.logical_name} ',
                columns_in_order=new_row_columns,
            )

            code = f"def {build_row_method_name}(self, source_row):\n"
            code += f"    new_row = self.row_object(iteration_header={new_row_iteration_header.iteration_id})\n"
            code += f"    source_values = source_row.values()\n"
            # TODO: It's worth spending more time here to see if we can do the quick build
            if (
                    set(new_row_columns).issubset(self.column_names)
                    and source_excludes is None
                    and source_row.iteration_header.parent == self
                    and len(source_row.values()) == len(new_row_columns)
            ):
                code += f"    new_row._data_values = source_values.copy()\n"
            else:
                code += f"    new_row_values = [\n"
                for column_name in new_row_columns:
                    coerce_method_name = self._get_coerce_method_name_by_str(column_name)
                    if coerce_method_name is None:
                        coerce_method_name = ''
                    if coerce_method_name != '':
                        coerce_method_name = f'self.{coerce_method_name}'
                    source_column_number = source_row.get_column_position(column_name)
                    code += f"        {coerce_method_name}(source_values[{source_column_number}]),\n"
                code += f"    ]\n"
                code += f"    new_row._data_values = new_row_values\n"
            code += f"    return new_row\n"
            try:
                code = compile(code, filename=build_row_method_name, mode='exec')
                exec(code)
            except SyntaxError as e:
                self.log.exception(f"{e} from code\n{code}")
                raise RuntimeError('Error with generated code')
            # Add the new function as a method in this class
            exec(f"self.{build_row_method_name} = {build_row_method_name}.__get__(self)")
            build_row_method = getattr(self, build_row_method_name)
            self._row_builders[build_row_key] = build_row_method

        new_row = self._row_builders[build_row_key](source_row)
        build_row_stats.timer.stop()
        return new_row

    def build_row_dynamic_source(
            self,
            source_row: Row,
            source_excludes: Optional[frozenset] = None,
            target_excludes: Optional[frozenset] = None,
            stat_name: str = 'build_row_dynamic_source',
            parent_stats: Optional[Statistics] = None,
    ) -> Row:
        """
        Use a source row to build a row with correct data types for this table.
        This version expects dynamically changing source rows, so it sanity checks **all** rows.

        Parameters
        ----------
        source_row
        source_excludes
        target_excludes
        stat_name
            Name of this step for the ETLTask statistics. Default = 'build rows'
        parent_stats

        Returns
        -------
            Row
        """
        build_row_stats = self.get_stats_entry(stat_name, parent_stats=parent_stats)
        build_row_stats.print_start_stop_times = False
        build_row_stats.timer.start()
        build_row_stats['calls'] += 1
        self.sanity_check_example_row(
            example_source_row=source_row,
            source_excludes=source_excludes,
            target_excludes=target_excludes,
        )
        target_set = set(self.column_names)
        new_row = source_row.subset(exclude=source_excludes, keep_only=target_set)
        for column_name in new_row.columns:
            coerce_method_name = self._get_coerce_method_name_by_str(column_name)
            if coerce_method_name is not None and coerce_method_name != '':
                coerce_method = getattr(self, f'self.{coerce_method_name}')
                new_row.transform(column_name, coerce_method)
        build_row_stats.timer.stop()
        return new_row

    def fill_cache_from_source(
            self,
            source: ETLComponent,
            progress_frequency: float = 10,
            progress_message="{component} fill_cache current row # {row_number:,}",
            criteria_list: list = None,
            criteria_dict: dict = None,
            column_list: list = None,
            exclude_cols: frozenset = None,
            order_by: list = None,
            assume_lookup_complete: bool = None,
            allow_duplicates_in_src: bool = False,
            row_limit: int = None,
            parent_stats: Statistics = None,
    ):
        """
        Fill all lookup caches from the database table.  Note that filtering criteria can be specified so that
        the resulting cache is not the entire current contents.  See ``assume_lookup_complete`` for how the lookup will
        handle cache misses -- note only database table backed components have the ability to fall back to querying
        the existing data on cache misses.

        Parameters
        ----------
        source:
            Source component to get rows from.
        progress_frequency :
            How often (in seconds) to output progress messages. Default 10. None for no progress messages.
        progress_message :
            The progress message to print.
            Default is ``"{component} fill_cache current row # {row_number:,}"``.
            Note ``logical_name`` and ``row_number``
            substitutions applied via :func:`format`.
        criteria_list :
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            https://goo.gl/JlY9us
        criteria_dict :
            Dict keys should be columns, values are set using = or in
        column_list:
            List of columns to include
        exclude_cols:
            Optional. Columns to exclude when filling the cache
        order_by:
            list of columns to sort by when filling the cache (helps range caches)
        assume_lookup_complete:
            Should later lookup calls assume the cache is complete?
            If so, lookups will raise an Exception if a key combination is not found.
            Default to False if filtering criteria was used, otherwise defaults to True.
        allow_duplicates_in_src:
            Should we quietly let the source provide multiple rows with the same key values? Default = False
        row_limit:
            limit on number of rows to cache.
        parent_stats:
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        """
        self._check_pk_lookup()

        # If we have, or can build a natural key
        if hasattr(self, 'natural_key'):
            if self.natural_key:
                # Make sure to build the lookup, so it can be filled
                if hasattr(self, 'ensure_nk_lookup'):
                    self.ensure_nk_lookup()

        assert isinstance(progress_frequency, int), (
            f"fill_cache progress_frequency expected to be int not {type(progress_frequency)}"
        )
        self.log.info(f'{self}.fill_cache started')
        stats = self.get_unique_stats_entry('fill_cache', parent_stats=parent_stats)
        stats.timer.start()

        self.clear_cache()
        progress_timer = Timer()
        # # Temporarily turn off read progress messages
        # saved_read_progress = self.__progress_frequency
        # self.__progress_frequency = None
        rows_read = 0
        limit_reached = False

        self.init_cache()

        for row in source.where(
                criteria_list=criteria_list,
                criteria_dict=criteria_dict,
                column_list=column_list,
                exclude_cols=exclude_cols,
                order_by=order_by,
                use_cache_as_source=False,
                progress_frequency=86400,
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

            if source != self:
                row = self.build_row(row, parent_stats=stats)

            # Actually cache the row now
            row.status = RowStatus.existing
            self.cache_row(row, allow_update=allow_duplicates_in_src)

            # noinspection PyTypeChecker
            if 0.0 < progress_frequency <= progress_timer.seconds_elapsed:
                progress_timer.reset()
                self.log.info(
                    progress_message.format(
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
                self.log.info(
                    f'Lookup {lookup} Rows {len(lookup):,} Size RAM= {this_ram_size:,} '
                    f'bytes DISK={this_disk_size:,} bytes'
                )
                if lookup.use_value_cache:
                    lookup.report_on_value_cache_effectiveness()
                else:
                    self.log.info('Value cache not enabled')
                ram_size += this_ram_size
                disk_size += this_disk_size
            self.log.info('Note: RAM sizes do not add up as memory lookups share row objects')
            self.log.info(f'Total Lookups Size DISK={disk_size:,} bytes')

            for lookup_name, lookup in self.__lookups.items():
                stats[f'rows in {lookup_name}'] = len(lookup)

        self.cache_commit()
        stats.timer.stop()
        # Restore read progress messages
        # self.__progress_frequency = saved_read_progress

    def fill_cache(
            self,
            progress_frequency: float = 10,
            progress_message="{component} fill_cache current row # {row_number:,}",
            criteria_list: list = None,
            criteria_dict: dict = None,
            column_list: list = None,
            exclude_cols: frozenset = None,
            order_by: list = None,
            assume_lookup_complete: bool = None,
            allow_duplicates_in_src: bool = False,
            row_limit: int = None,
            parent_stats: Statistics = None,
    ):
        """
        Fill all lookup caches from the table.

        Parameters
        ----------
        progress_frequency :
            How often (in seconds) to output progress messages. Default 10. None for no progress messages.
        progress_message :
            The progress message to print.
            Default is ``"{component} fill_cache current row # {row_number:,}"``.
            Note ``logical_name`` and ``row_number``
            substitutions applied via :func:`format`.
        criteria_list :
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            https://goo.gl/JlY9us
        criteria_dict :
            Dict keys should be columns, values are set using = or in
        column_list:
            List of columns to include
        exclude_cols: frozenset
            Optional. Columns to exclude when filling the cache
        order_by:
            list of columns to sort by when filling the cache (helps range caches)
        assume_lookup_complete:
            Should later lookup calls assume the cache is complete?
            If so, lookups will raise an Exception if a key combination is not found.
            Default to False if filtering criteria was used, otherwise defaults to True.
        allow_duplicates_in_src:
            Should we quietly let the source provide multiple rows with the same key values? Default = False
        row_limit:
            limit on number of rows to cache.
        row_limit:
            limit on number of rows to cache.
        parent_stats:
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        """
        self.fill_cache_from_source(
            source=self,
            progress_frequency=progress_frequency,
            progress_message=progress_message,
            criteria_list=criteria_list,
            criteria_dict=criteria_dict,
            column_list=column_list,
            exclude_cols=exclude_cols,
            order_by=order_by,
            assume_lookup_complete=assume_lookup_complete,
            allow_duplicates_in_src=allow_duplicates_in_src,
            row_limit=row_limit,
            parent_stats=parent_stats,
        )

    def get_by_lookup(
            self,
            lookup_name: str,
            source_row: Row,
            stats_id: str = 'get_by_lookup',
            parent_stats: Optional[Statistics] = None,
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

        if isinstance(lookup_name, Lookup):
            lookup = lookup_name
        else:
            lookup = self.get_lookup(lookup_name)
            assert isinstance(lookup, Lookup)

        return lookup.find(
            row=source_row,
            fallback_to_db=fallback_to_db,
            stats=stats
            )
