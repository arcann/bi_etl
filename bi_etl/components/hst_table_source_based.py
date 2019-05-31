import textwrap

from typing import Union, List, Callable

from bi_etl.components.hst_table import HistoryTable
from bi_etl.components.row.row import Row
from bi_etl.components.row.row_status import RowStatus
from bi_etl.components.table import Table
from bi_etl.database import DatabaseMetadata
from bi_etl.exceptions import NoResultFound
from bi_etl.scheduler.task import ETLTask
from bi_etl.statistics import Statistics
from bi_etl.timer import Timer

__all__ = ['HistoryTableSourceBased']


# noinspection PyAbstractClass
class HistoryTableSourceBased(HistoryTable):
    """
    ETL target component for a table that stores history of updates where the source provides the dates to use.
    Also usable as a source.

    Example:
        Target table currently has:
            2016 - A
            2017 - B
            2018 - C

        Source Deletes 2017 version.  A normal HistoryTable load would not touch the 2017 version since it was not
        provided in the source.

        The desired output is:
            2016 - A
            2017 - A
            2018 - C

        This component handles that update by stepping through the provided source versions and existing target versions
        updating each target version as required so it matches the closest source version earlier or equal in time.

    Parameters
    ----------
    task : ETLTask
        The  instance to register in (if not None)

    database : bi_etl.scheduler.task.Database
        The database to find the table/view in.

    table_name : str
        The name of the table/view.

    exclude_columns : list
        Optional. A list of columns to exclude from the table/view. These columns will not be included in SELECT, INSERT, or UPDATE statements.

    Attributes
    ----------

    auto_generate_key: boolean
        Should the primary key be automatically generated by the insert/upsert process?
        If True, the process will get the current maximum value and then increment it with each insert.

    autocommit: boolean
        Automatically commit after delete? Defaults to False.

    begin_date: str
        Name of the begin date field

    end_date: str
        Name of the end date field

    inserts_use_default_begin_date: boolean
        Should inserts use the default begin date instead of the class effective date
        This allows records to match up in joins with other history tables where the effective
        date of the 'primary' might be before the first version effective date.
        Default = True

    default_begin_date: date
        Default begin date to assign for begin_date.
        Used for new records if inserts_use_default_begin_date is True.
        Also used for
        :meth:`get_missing_row`,
        :meth:`get_invalid_row`,
        :meth:`get_not_applicable_row`,
        :meth:`get_various_row`
        Default = 1900-1-1

    default_end_date: date
        Default begin date to assign for end_date for active rows.
        Also used for
        :meth:`get_missing_row`,
        :meth:`get_invalid_row`,
        :meth:`get_not_applicable_row`,
        :meth:`get_various_row`
        Default = 9999-1-1

    auto_generate_key: boolean
        Should the primary key be automatically generated by the insert/upsert process?
        If True, the process will get the current maximum value and then increment it with each insert.
        (inherited from Table)

    batch_size: int
        How many rows should be insert/update/deleted in a single batch.
        (inherited from Table)

    delete_flag : str
        The name of the delete_flag column, if any.
        Optional.
        (inherited from ReadOnlyTable)

    delete_flag_yes : str
        The value of delete_flag for deleted rows.
        Optional.
        (inherited from ReadOnlyTable)

    delete_flag_no : str
        The value of delete_flag for *not* deleted rows.
        Optional.
        (inherited from ReadOnlyTable)

    default_date_format: str
        The date parsing format to use for str -> date conversions.
        If more than one date format exists in the source, then explicit conversions will be required.

        Default = '%m/%d/%Y'
        (inherited from Table)

    force_ascii: boolean
        Should text values be forced into the ascii character set before passing to the database?
        Default = False
        (inherited from Table)

    last_update_date: str
        Name of the column which we should update when table updates are made.
        Default = None
        (inherited from Table)

    log_first_row : boolean
        Should we log progress on the the first row read. *Only applies if Table is used as a source.*
        (inherited from ETLComponent)

    max_rows : int
        The maximum number of rows to read. *Only applies if Table is used as a source.*
        Optional.
        (inherited from ETLComponent)

    primary_key: list
        The name of the primary key column(s). Only impacts trace messages.  Default=None.
        If not passed in, will use the database value, if any.
        (inherited from ETLComponent)

    natural_key: list
        The list of natural key columns (as Column objects).
        The default is the list of non-begin/end date primary key columns.
        The default is *not* appropriate for dimension tables with surrogate keys.

    progress_frequency : int
        How often (in seconds) to output progress messages.
        Optional.
        (inherited from ETLComponent)

    progress_message : str
        The progress message to print.
        Optional. Default is ``"{logical_name} row # {row_number}"``. Note ``logical_name`` and ``row_number``
        substitutions applied via :func:`format`.
        (inherited from ETLComponent)

    special_values_descriptive_columns: list
         A list of columns that get longer descriptive text in
         :meth:`get_missing_row`,
         :meth:`get_invalid_row`,
         :meth:`get_not_applicable_row`,
         :meth:`get_various_row`
         Optional.
         (inherited from ReadOnlyTable)

    track_source_rows: boolean
        Should the :meth:`upsert` method keep a set container of source row keys that it has processed?
        That set would then be used by :meth:`update_not_processed`, :meth:`logically_delete_not_processed`,
        and :meth:`delete_not_processed`.
        (inherited from Table)

    type_1_surrogate: str
        The name of the type 1 surrogate key. The value is automatically generated as equal to the type 2 key on
        inserts and equal to the existing value on updates.
        Optional.

    """

    def __init__(self,
                 task: ETLTask,
                 database: DatabaseMetadata,
                 table_name: str,
                 table_name_case_sensitive: bool = True,
                 schema: str = None,
                 exclude_columns: list = None,
                 **kwargs
                 ):
        # Don't pass kwargs up to super. They should be set at the end of this method
        super().__init__(task=task,
                         database=database,
                         table_name=table_name,
                         schema=schema,
                         table_name_case_sensitive=table_name_case_sensitive,
                         exclude_columns=exclude_columns,
                         )
        self.prior_upsert_key = None
        self.prior_upsert_lookup_name = None
        self.prior_upsert_existing_rows_list = list()
        self.prior_upsert_existing_row_index = 0
        self.prior_upsert_row = None
        self.prior_upsert_update_callback = None
        self.prior_upsert_insert_callback = None
        self.prior_upsert_build_method = None
        self.prior_upsert_stat_name = None
        self.prior_upsert_parent_stats = None

        # Should be the last call of every init
        self.set_kwattrs(**kwargs)

    def _upsert_version_set(
            self,
            source_mapped_as_target_row: Row,
            lookup_name: str = None,
            skip_update_check_on: list = None,
            do_not_update: list = None,
            additional_update_values: dict = None,
            additional_insert_values: dict = None,
            update_callback: Callable[[list, Row], None] = None,
            insert_callback: Callable[[Row], None] = None,
            source_excludes: list = None,
            target_excludes: list = None,
            build_method: HistoryTable.RowBuildMethod = HistoryTable.RowBuildMethod.safe,
            stat_name: str = 'upsert',
            parent_stats: Statistics = None,
            ):
        """
        Update (if changed) or Insert a row in the table.
        Returns the row found/inserted, with the auto-generated key (if that feature is enabled)

        Parameters
        ----------
        source_mapped_as_target_row: :class:`~bi_etl.components.row.row_case_insensitive.Row`
            Row to upsert
        lookup_name: str
            The name of the lookup (see :meth:`define_lookup`) to use when searching for an existing row.
        skip_update_check_on: list
            List of column names to not compare old vs new for updates.
        do_not_update: list
             List of columns to never update.
        additional_update_values: dict
            Additional updates to apply when updating
        additional_insert_values: dict
            Additional values to set on each row when inserting.
        update_callback: func
            Function to pass updated rows to. Function should not modify row.
        insert_callback: func
            Function to pass inserted rows to. Function should not modify row.
        source_excludes: list
            list of source columns to exclude when mapping to this Table.
        target_excludes: list
            list of Table columns to exclude when mapping from the source row
        build_method:
            none, clone, or safe (default is safe)
            None means use the row as is
            Clone means create a subset clone
            Safe does a clone and then checks each column type to ensure it matches the target
        stat_name: string
            Name of this step for the ETLTask statistics. Default = 'upsert'
        parent_stats: bi_etl.statistics.Statistics
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        """
        # This should be the (or a) natural key lookup
        lookup = self.get_lookup(lookup_name)
        nk_tuple = lookup.get_hashable_combined_key(source_mapped_as_target_row)

        if self.prior_upsert_key != nk_tuple or self.prior_upsert_lookup_name != lookup_name:
            # Check if this is the first row and not the end of a batch
            if self.prior_upsert_key is not None:
                # This is the end of a batch
                self.finish_pending_existing_rows()

            # Reset for the next list
            self.prior_upsert_row = None
            self.prior_upsert_key = nk_tuple
            self.prior_upsert_lookup_name = lookup_name
            try:
                existing_rows = lookup.find_versions_list(self.prior_upsert_key)
            except NoResultFound:
                # No existing rows were found, insert
                new_row = source_mapped_as_target_row
                if self.inserts_use_default_begin_date:
                    new_row[self.begin_date_column] = self.default_begin_date

                if additional_insert_values:
                    for colName, value in additional_insert_values.items():
                        new_row[colName] = value
                self.insert(
                    new_row,
                    build_method=build_method,
                    parent_stats=parent_stats,
                )

                if insert_callback:
                    insert_callback(new_row)

                return new_row

            # We only reach here if a result was found from the lookup
            self.prior_upsert_existing_rows_list = existing_rows
            self.prior_upsert_existing_row_index = 0
            self.prior_upsert_update_callback = update_callback
            self.prior_upsert_insert_callback = insert_callback
            self.prior_upsert_build_method = build_method
            self.prior_upsert_stat_name = stat_name
            self.prior_upsert_parent_stats = parent_stats
            if self.inserts_use_default_begin_date:
                # Force first row to use the default begin date (year 1900)
                row_begin_date = self.default_begin_date
                source_mapped_as_target_row[self.begin_date_column] = row_begin_date
            else:
                row_begin_date = source_mapped_as_target_row[self.begin_date_column]
        else:
            row_begin_date = source_mapped_as_target_row[self.begin_date_column]

        # Check that rows are coming in order
        if self.prior_upsert_row is not None:
            if row_begin_date < self.prior_upsert_row[self.begin_date_column]:
                raise RuntimeError(
                    textwrap.dedent("""\
                    rows not in begin date order!
                    nk_tuple = {}
                    row = {}
                    prior_upsert_row = {}
                    """).format(
                        nk_tuple,
                        repr(source_mapped_as_target_row),
                        repr(self.prior_upsert_row)
                    )
                )

        # Nested join over existing rows and pending upsert rows
        first_new_row = None
        get_next_new_row = False
        upsert_row = source_mapped_as_target_row
        while not get_next_new_row:
            needs_upsert = True
            if self.prior_upsert_existing_row_index >= len(self.prior_upsert_existing_rows_list):
                # There is no next existing row, use a max date value
                existing_begin_date = self.default_end_date
                existing_row = None
            else:
                existing_row = self.prior_upsert_existing_rows_list[self.prior_upsert_existing_row_index]
                existing_begin_date = existing_row[self.begin_date_column]

            if row_begin_date < existing_begin_date:
                # New date is before all remaining existing rows
                upsert_row = source_mapped_as_target_row
                get_next_new_row = True
            elif row_begin_date == existing_begin_date:
                # New date equal to existing date
                upsert_row = source_mapped_as_target_row
                get_next_new_row = True
                self.prior_upsert_existing_row_index += 1
            else:
                # New row begin > Existing date
                if self.prior_upsert_row is not None:
                    excludes = set(self.primary_key)
                    excludes.add(self.end_date_column)
                    if source_excludes is not None:
                        excludes.update(source_excludes)
                    upsert_row = self.prior_upsert_row.subset(exclude=excludes)
                    upsert_row[self.begin_date_column] = existing_begin_date
                    self.prior_upsert_existing_row_index += 1
                else:
                    # No prior row, keep existing data
                    upsert_row = existing_row
                    self.prior_upsert_existing_row_index += 1
                    # As the logic stands now we could skip the upsert entirely in this scenario
                    needs_upsert = False

            if needs_upsert:
                new_row = super().upsert(
                    source_row=upsert_row,
                    lookup_name=lookup_name,
                    skip_update_check_on=skip_update_check_on,
                    do_not_update=do_not_update,
                    additional_update_values=additional_update_values,
                    additional_insert_values=additional_insert_values,
                    update_callback=update_callback,
                    insert_callback=insert_callback,
                    source_excludes=source_excludes,
                    target_excludes=target_excludes,
                    build_method=build_method,
                    stat_name=stat_name,
                    parent_stats=parent_stats,
                    )
                if first_new_row is None:
                    first_new_row = new_row
        self.prior_upsert_row = upsert_row

        return first_new_row

    def finish_pending_existing_rows(self):
        if self.prior_upsert_row is not None:
            for existing_row in self.prior_upsert_existing_rows_list[self.prior_upsert_existing_row_index:]:
                existing_begin_date = existing_row[self.begin_date_column]
                excludes = set(self.primary_key)
                excludes.add(self.end_date_column)
                upsert_row = self.prior_upsert_row.subset(exclude=excludes)
                upsert_row[self.begin_date_column] = existing_begin_date
                super().upsert(
                    source_row=upsert_row,
                    lookup_name=self.prior_upsert_lookup_name,
                    update_callback=self.prior_upsert_update_callback,
                    insert_callback=self.prior_upsert_insert_callback,
                    build_method=self.prior_upsert_build_method,
                    stat_name=self.prior_upsert_stat_name,
                    parent_stats=self.prior_upsert_parent_stats,
                )
            else:
                pass
        else:
            pass

    def upsert(self,
               source_row: Union[Row, List[Row]],
               lookup_name: str = None,
               skip_update_check_on: list = None,
               do_not_update: list = None,
               additional_update_values: dict = None,
               additional_insert_values: dict = None,
               update_callback: Callable[[list, Row], None] = None,
               insert_callback: Callable[[Row], None] = None,
               source_excludes: list = None,
               target_excludes: list = None,
               build_method: HistoryTable.RowBuildMethod = HistoryTable.RowBuildMethod.safe,
               stat_name: str = 'upsert',
               parent_stats: Statistics = None,
               **kwargs
               ):
        """
        Update (if changed) or Insert a row in the table.
        Returns the row found/inserted, with the auto-generated key (if that feature is enabled)

        Parameters
        ----------
        source_row: :class:`~bi_etl.components.row.row_case_insensitive.Row`
            Row to upsert
        lookup_name: str
            The name of the lookup (see :meth:`define_lookup`) to use when searching for an existing row.
        skip_update_check_on: list
            List of column names to not compare old vs new for updates.
        do_not_update: list
             List of columns to never update.
        additional_update_values: dict
            Additional updates to apply when updating
        additional_insert_values: dict
            Additional values to set on each row when inserting.
        update_callback: func
            Function to pass updated rows to. Function should not modify row.
        insert_callback: func
            Function to pass inserted rows to. Function should not modify row.
        source_excludes: list
            list of source columns to exclude when mapping to this Table.
        target_excludes: list
            list of Table columns to exclude when mapping from the source row
        build_method:
            none, clone, or safe (default is safe)
            RowBuildMethod.safe matches source to tagret column by column.
            RowBuildMethod.clone makes a clone of the source row. Prevents possible issues with outside changes to the row.
            RowBuildMethod.none uses the row as is.
        stat_name: string
            Name of this step for the ETLTask statistics. Default = 'upsert'
        parent_stats: bi_etl.statistics.Statistics
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        kwargs:
            effective_date: datetime
                The effective date to use for the update
        """

        effective_date = kwargs.get('effective_date')
        if effective_date is None:
            if self.begin_date_column in source_row and source_row[self.begin_date_column] is not None:
                pass
            else:
                source_row[self.begin_date_column] = self.default_effective_date
        else:
            date_coerce = getattr(self, f'_coerce_{self.begin_date_column}')
            source_row[self.begin_date_column] = date_coerce(effective_date)

        stats = self.get_stats_entry(stat_name, parent_stats=parent_stats)
        stats.timer.start()
        self.begin()

        stats['upsert source row count'] += 1

        target_excludes = self._target_excludes_for_updates(target_excludes)

        source_mapped_as_target_row = self.build_row(source_row=source_row,
                                                     source_excludes=source_excludes,
                                                     target_excludes=target_excludes,
                                                     parent_stats=stats,
                                                     )

        if self.track_source_rows:
            # Keep track of source records so we can check if target rows don't exist in source
            self.source_keys_processed.add(self.get_natural_key_tuple(source_mapped_as_target_row))

        if lookup_name is None or lookup_name == self.PK_LOOKUP:
            # PK lookup doesn't need to deal with list of dates, so call the parent upsert routine directly
            return super().upsert(
                source_row=source_mapped_as_target_row,
                lookup_name=lookup_name,
                skip_update_check_on=skip_update_check_on,
                do_not_update=do_not_update,
                additional_update_values=additional_update_values,
                additional_insert_values=additional_insert_values,
                update_callback=update_callback,
                insert_callback=insert_callback,
                source_excludes=source_excludes,
                target_excludes=target_excludes,
                build_method=self.RowBuildMethod.none,
                stat_name=stat_name,
                parent_stats=parent_stats,
                )
        else:
            return self._upsert_version_set(
                source_mapped_as_target_row=source_mapped_as_target_row,
                lookup_name=lookup_name,
                skip_update_check_on=skip_update_check_on,
                do_not_update=do_not_update,
                additional_update_values=additional_update_values,
                additional_insert_values=additional_insert_values,
                update_callback=update_callback,
                insert_callback=insert_callback,
                source_excludes=source_excludes,
                target_excludes=target_excludes,
                build_method=self.RowBuildMethod.none,
                stat_name=stat_name,
                parent_stats=parent_stats,
                )

    def update_not_in_set(
            self,
            updates_to_make: Union[dict, Row],
            set_of_key_tuples: set,
            lookup_name: str = None,
            criteria_list: list = None,
            criteria_dict: dict = None,
            use_cache_as_source: bool = True,
            progress_frequency: int = None,
            stat_name: str = 'update_not_in_set',
            parent_stats: Statistics = None,
            **kwargs
    ):
        """
        Applies update to rows matching criteria that are not in the list_of_key_tuples pass in.

        Parameters
        ----------
        updates_to_make: :class:`Row`
            Row or dict of updates to make
        set_of_key_tuples: set
            Set of tuples comprising the primary key values. This list represents the rows that should *not* be updated.
        lookup_name: str
            The name of the lookup (see :meth:`define_lookup`) to use when searching for an existing row.
        criteria_list : string or list of strings
            Each string value will be passed to :meth:`sqlalchemy.sql.expression.Select.where`.
            https://goo.gl/JlY9us
        criteria_dict : dict
            Dict keys should be columns, values are set using = or in
        use_cache_as_source: bool
            Attempt to read existing rows from the cache?
        stat_name: string
            Name of this step for the ETLTask statistics. Default = 'delete_not_in_set'
        progress_frequency: int
            How often (in seconds) to output progress messages. Default = 10.  None for no progress messages.
        parent_stats: bi_etl.statistics.Statistics
            Optional Statistics object to nest this steps statistics in.
            Default is to place statistics in the ETLTask level statistics.
        kwargs:
            effective_date: datetime
                The effective date to use for the update
        """
        if criteria_list is None:
            criteria_list = []

        criteria_list.extend(
            [
                self.get_column(self.delete_flag) == self.delete_flag_no,
                self.get_column(self.primary_key[0]) > 0,
            ]
        )
        stats = self.get_unique_stats_entry(stat_name, parent_stats=parent_stats)
        stats['rows read'] = 0
        stats['updates count'] = 0

        stats.timer.start()
        self.begin()

        if progress_frequency is None:
            progress_frequency = self.progress_frequency

        progress_timer = Timer()

        # Turn off read progress reports
        saved_progress_frequency = self.progress_frequency
        self.progress_frequency = None

        if lookup_name is None:
            lookup = self.get_nk_lookup()
        else:
            lookup = self.get_lookup(lookup_name)

        # Turn off cache updates
        saved_maintain_cache_during_load = self.maintain_cache_during_load
        self.maintain_cache_during_load = False
        self.cache_clean = False

        # Note, here we select only lookup columns from self
        for row in self.where(column_list=lookup.lookup_keys,
                              criteria_list=criteria_list,
                              criteria_dict=criteria_dict,
                              use_cache_as_source=use_cache_as_source,
                              parent_stats=stats):
            if row.status == RowStatus.unknown:
                pass
            stats['rows read'] += 1
            existing_key = lookup.get_hashable_combined_key(row)

            if 0 < progress_frequency <= progress_timer.seconds_elapsed:
                progress_timer.reset()
                self.log.info(f"update_not_in_set current current row#={stats['rows read']:,} row key={existing_key} updates done so far = {stats['updates count']:,}")

            if existing_key not in set_of_key_tuples:
                stats['updates count'] += 1

                # Direct update method. This will be slow due to new statement per update
                # and also update statements per row
                # self.update(updates_to_make, key_names=lookup.lookup_keys, key_values=existing_key, connection_name='update')

                try:
                    # First we need the entire existing row
                    target_row_list = lookup.find_versions_list(row)
                except NoResultFound:
                    raise RuntimeError("keys {} found in database or cache but not found now by get_by_lookup".format(
                        row.as_key_value_list
                    ))

                for target_row in target_row_list:
                    # Then we can apply the updates to it using Table non-versioned updates
                    Table.apply_updates(
                        self=self,
                        row=target_row,
                        additional_update_values=updates_to_make,
                        parent_stats=stats
                    )

        stats.timer.stop()

        # Restore saved progress_frequency
        self.progress_frequency = saved_progress_frequency
        self.maintain_cache_during_load = saved_maintain_cache_during_load

    def commit(self,
               stat_name='commit',
               parent_stats=None,
               print_to_log=True,
               connection_name: str = None,
               begin_new: bool = True,
               ):
        if len(self.prior_upsert_existing_rows_list) > 0:
            # End the final batch
            self.finish_pending_existing_rows()
        super().commit(stat_name=stat_name,
                       parent_stats=parent_stats,
                       print_to_log=print_to_log,
                       connection_name=connection_name,
                       begin_new=begin_new,
                       )

