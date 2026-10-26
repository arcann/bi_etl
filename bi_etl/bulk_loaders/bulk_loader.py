# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

from abc import ABC, abstractmethod

import logging
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import *
from datetime import datetime

import sqlalchemy

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_status import RowStatus

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.etl_task import ETLTask


class BulkLoader(ABC):
    """
    Base class for loaders that load rows into a database table using the database's bulk load facility.

    Subclasses must implement :meth:`load_from_iterable`. Loaders that work from files
    can also implement :meth:`load_from_files`.
    """

    def __init__(
            self,
    ):
        """Create the logger and the empty set of values to redact from logged messages."""
        self.log =logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self._redact_values = set()

    def __str__(self) -> str:
        """Return the class name followed by empty parentheses."""
        return f"{self.__class__.__name__}()"

    def add_redact_value(self, redact_value: str):
        """
        Register a value (such as a password) that :meth:`log_with_redactions` must hide.

        Parameters
        ----------
        redact_value:
            Text to replace with asterisks in logged messages. None is ignored.
        """
        if redact_value is not None:
            self._redact_values.add(redact_value)

    def log_with_redactions(
            self,
            *,
            log_level: int,
            message: str
    ):
        """
        Log *message* after replacing every registered redaction value with asterisks.

        Parameters
        ----------
        log_level:
            Logging level, such as :data:`logging.INFO`.
        message:
            Text to log.
        """
        for redaction in self._redact_values:
            message = message.replace(redaction, '*' * 6)
        self.log.log(
            level=log_level,
            msg=message,
        )

    @property
    def needs_all_columns(self):
        """
        True if the rows passed to the loader must contain every column of the target table, in table order.

        Returns
        -------
        bool
            True by default. Loaders that can map columns by name override this to return False.
        """
        return True

    @staticmethod
    def _get_table_specific_folder_name(
            base_folder: str,
            table_object: Table,
    ):
        """
        Build a folder path unique to this table and this load.

        Parameters
        ----------
        base_folder:
            Folder that the table specific folder is created under.
        table_object:
            The table being loaded.

        Returns
        -------
        str
            ``base_folder`` followed by the qualified table name (with ``.`` replaced by ``_``) and a random UUID.
        """
        table_name_for_folder = table_object.qualified_table_name.replace('.', '_')
        # Add a random UID that is filename safe to the path.
        # That will prevent two envts that accidentally share a bucket & folder
        # from clobbering each other's files
        uid = uuid.uuid4()
        return f'{base_folder}/{table_name_for_folder}_{uid.hex}'

    # --- Background file upload hooks ----------------------------------------
    # Loaders that stage their files somewhere remote (e.g. S3) override these so that
    # finished files are uploaded while the next ones are still being written.
    # The defaults do nothing, so a loader that loads local files needs no changes.

    def _begin_file_uploads(self, table_object: Table) -> None:
        """
        Called by ``load_from_iterable`` implementations before the first file is written.

        Parameters
        ----------
        table_object:
            The table being loaded.
        """

    def _queue_file_for_upload(self, local_file: str | Path) -> None:
        """
        Called by ``load_from_iterable`` implementations each time a file is completely written and closed.

        Parameters
        ----------
        local_file:
            Path of the finished file.
        """

    def _abort_file_uploads(self) -> None:
        """
        Stop any uploads that were not collected by :meth:`load_from_files`.

        Must be safe to call when no uploads are active.
        """

    def _handle_load_failure(self) -> None:
        """
        Called when a load fails, after :meth:`_abort_file_uploads` has stopped any uploads.

        Must be safe to call more than once and must not raise, so that the original error is the one reported.
        """

    @contextmanager
    def _file_upload_session(self, table_object: Table) -> Iterator[None]:
        """
        Context manager that calls :meth:`_begin_file_uploads` on entry and :meth:`_abort_file_uploads` on exit.
        If the body raises, :meth:`_handle_load_failure` is also called.

        Use it in the same ``with`` statement as the temporary directory holding the files, listed after the
        directory, so that uploads are stopped before the directory is removed.

        Parameters
        ----------
        table_object:
            The table being loaded.
        """
        self._begin_file_uploads(table_object)
        try:
            yield
        except BaseException:
            # Uploads are stopped first. The upload thread is the only user of the S3 bucket until it is joined.
            self._abort_file_uploads()
            self._handle_load_failure()
            raise
        finally:
            self._abort_file_uploads()

    def load_from_files(
            self,
            local_files: list,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str | None = None,
    ) -> int:
        """
        Note: This method is NOT required for all bulk loaders.
        """
        raise NotImplementedError()

    @abstractmethod
    def load_from_iterable(
            self,
            iterable: Iterable[Row],
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str | None = None,
            parent_task: Optional[ETLTask] = None,
    ) -> int:
        """
        Note: This method is IS required for all bulk loaders.
        """
        raise NotImplementedError()

    def load_table_from_cache(
            self,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str | None = None,
    ) -> int:
        """
        Bulk load the rows cached by *table_object* using :meth:`load_from_iterable`.

        Parameters
        ----------
        table_object:
            Table whose cache is loaded.
        table_to_load:
            Name of the table (or temp table) that was loaded, used for the rename.
        perform_rename:
            If True, call :meth:`rename_table` after the load.
        progress_frequency:
            Seconds between progress log messages.
        analyze_compression:
            Passed through to :meth:`load_from_iterable`.

        Returns
        -------
        int
            Number of rows loaded.
        """
        row_count = self.load_from_iterable(
            iterable=table_object.cache_iterable(),
            table_object=table_object,
            perform_rename=False,  # False since we do it here
            analyze_compression=analyze_compression,
        )
        if perform_rename:
            self.rename_table(table_to_load, table_object)
        return row_count

    def rename_table(
            self,
            temp_table_name: str | None,
            table_object: Table,
    ):
        """
        Swap a freshly loaded temp table in place of *table_object*.

        The existing table is renamed with an ``_old`` suffix (dropping any earlier ``_old`` table first),
        and *temp_table_name* is renamed to the name of *table_object*.

        Parameters
        ----------
        temp_table_name:
            Name of the table that was loaded. If None, a warning is logged and nothing is renamed.
        table_object:
            The table to replace.
        """
        if temp_table_name is not None:
            old_name = table_object.qualified_table_name + '_old'

            table_object.database.drop_table_if_exists(old_name)

            with Table(
                    table_object.task,
                    table_name=temp_table_name,
                    database=table_object.database,
            ) as table_to_load_object:
                assert isinstance(table_to_load_object, Table)
                table_object.table.rename(old_name)
                table_to_load_object.table.rename(table_object.table_name)
        else:
            self.log.warning(f'Asked to perform rename but load went directly to {table_object}')

    def apply_updates(
            self,
            table_object: Table,
            update_rows: Sequence[Row]
    ):
        """
        NOT TESTED !
        """
        bcp_update_table_dict = dict()

        for row in update_rows:
            if row.status not in [RowStatus.deleted, RowStatus.insert]:
                update_stmt_key = row.column_set
                if update_stmt_key in bcp_update_table_dict:
                    update_table_object, pending_rows = bcp_update_table_dict[update_stmt_key]
                else:
                    created = False
                    tmp_id = 0
                    table_name = None
                    while not created:
                        # Create a new temp table
                        table_name = "tmp_" + str(datetime.now().toordinal()) + str(tmp_id)
                        try:
                            row_columns = [table_object.get_column(col_name).copy() for col_name in
                                           row.columns_in_order]
                            sa_table = sqlalchemy.schema.Table(
                                table_name,
                                table_object.database,
                                *row_columns
                            )
                            sa_table.create(table_object.connection())
                            created = True
                        except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.InvalidRequestError):
                            tmp_id += 1
                    assert table_name is not None
                    update_table_object = Table(
                        task=table_object.task,
                        table_name=table_name,
                        database=table_object.database,
                    )
                    update_table_object.close()
                    pending_rows = list()
                    bcp_update_table_dict[update_stmt_key] = update_table_object, pending_rows
                pending_rows.append(row)

        for update_table_object, pending_rows in bcp_update_table_dict.values():
            self.load_from_iterable(
                iterable=pending_rows,
                table_object=update_table_object,
            )

            database_type = type(table_object.connection().dialect).name
            if database_type == 'oracle':
                raise NotImplementedError("Oracle MERGE not yet implemented")
            elif database_type in ['mssql']:
                sets_list = [f"{column} = {update_table_object.table_name}.{column}"
                             for column in update_table_object.column_names
                             ]
                sets = ','.join(sets_list)

                key_join_list = [
                    f"{table_object}.{column} = {update_table_object.table_name}.{column}"
                    for column in table_object.primary_key
                ]
                key_joins = ','.join(key_join_list)

                sql = f"""\
                    UPDATE {table_object.qualified_table_name}
                    SET {sets}
                    FROM {table_object.qualified_table_name}
                         INNER JOIN
                         {update_table_object.qualified_table_name}
                           ON {key_joins}
                    """
                table_object.execute(sql)
            else:
                raise NotImplementedError(f"UPDATE FROM/MERGE not yet implemented for {database_type}")
