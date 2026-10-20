# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import gzip
import io
import os.path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Iterable, Optional

from bi_etl.components.csv_writer import CSVWriter, QUOTE_MINIMAL
from bi_etl.timer import Timer

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.etl_task import ETLTask


class CsvBulkLoaderMixin:
    """Mixin providing CSV chunk writing, compression setup, and loading.

    Subclasses must call :meth:`_init_csv` from their ``__init__`` to
    configure the delimiter, header behaviour, and chunk size.

    .. note::

       :class:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader` also defines
       :meth:`load_from_iterable` (raising ``NotImplementedError``).  For
       this mixin's implementation to win the MRO, concrete CSV loaders
       must list ``CsvBulkLoaderMixin`` *before* :class:`BulkLoader` (or
       any base deriving from it) in their own bases.
    """

    def _init_csv(
            self,
            chunk_size: int = 25000,
            has_header: bool = True,
            delimiter: str = '|',
            null_value: str = '',
    ):
        """
        Initialise CSV settings.  Call from subclass ``__init__``.
        """
        self.chunk_size = chunk_size
        self.has_header = has_header
        self.csv_delimiter = delimiter
        self.null_value = null_value

    # --- CSV file helpers ----------------------------------------------------

    def _open_csv_writer(
            self,
            filepath: str,
            column_names: list[str],
            parent_task=None,
    ) -> tuple:
        """Open a gzipped CSV file and return ``(writer, text_wrapper, zip_file)``."""
        zip_file = gzip.open(filepath, 'wb')
        # noinspection PyTypeChecker
        text_wrapper = io.TextIOWrapper(zip_file, encoding='utf-8')
        writer = CSVWriter(
            parent_task,
            text_wrapper,
            delimiter=self.csv_delimiter,
            column_names=column_names,
            include_header=self.has_header,
            encoding='utf-8',
            escapechar='\\',
            quoting=QUOTE_MINIMAL,
        )
        return writer, text_wrapper, zip_file

    @staticmethod
    def _close_csv_writer(writer, text_wrapper, zip_file):
        """Close the CSV writer and its underlying streams."""
        writer.close()
        text_wrapper.close()
        zip_file.close()

    # --- Load from iterable ---------------------------------------------------

    def load_from_iterable(
            self,
            iterable: Iterable,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str | None = None,
            parent_task: Optional[ETLTask] = None,
    ) -> int:
        """Write rows from *iterable* to local gzipped CSV files and load them
        via :meth:`load_from_files`.

        Parameters
        ----------
        iterable
            Source of :class:`~bi_etl.components.row.row.Row` objects to load.
        table_object
            Table the rows are being loaded into.
        table_to_load
            Name of the table (or temp table) to load into.  Defaults to
            ``table_object.qualified_table_name``.
        perform_rename
            Passed through to :meth:`load_from_files`.
        progress_frequency
            Seconds between progress log messages.  Pass ``None`` to disable.
        analyze_compression
            Passed through to :meth:`load_from_files`.
        parent_task
            Optional parent task, forwarded to :class:`CSVWriter`.

        Returns
        -------
        int
            Number of rows written.
        """
        table_to_load = table_to_load or table_object.qualified_table_name
        # Resolve column names once before the loop to avoid repeated RPC calls
        column_names = table_object.column_names

        with TemporaryDirectory(
                dir=self.config.temp_file_path,
                ignore_cleanup_errors=True,
        ) as temp_dir:
            local_files_list: list[str] = []
            file_number = 0
            row_count = 0
            current_chunk_rows = 0
            writer = None
            text_wrapper = None
            zip_file = None

            try:
                progress_timer = Timer()
                for row_number, row in enumerate(iterable):
                    if writer is None or current_chunk_rows >= self.chunk_size:
                        # Close the current file if one is open
                        if writer is not None:
                            self._close_csv_writer(writer, text_wrapper, zip_file)
                            self.log.debug(
                                f"Closed CSV bulk load chunk {file_number}: "
                                f"{local_files_list[-1]}"
                            )
                            file_number += 1

                        # Open a new chunk file
                        current_chunk_rows = 0
                        filepath = os.path.join(temp_dir, f'data_{file_number}.csv.gz')
                        local_files_list.append(filepath)
                        self.log.debug(f"Starting CSV bulk load chunk {file_number}")
                        writer, text_wrapper, zip_file = self._open_csv_writer(
                            filepath=filepath,
                            column_names=column_names,
                            parent_task=parent_task,
                        )

                    row_count += 1
                    current_chunk_rows += 1
                    writer.insert_row(row)

                    if progress_frequency is not None:
                        if 0 < progress_frequency < progress_timer.seconds_elapsed:
                            self.log.info(f"Wrote row {row_number:,}")
                            progress_timer.reset()

                if row_count > 0:
                    self.log.info(f"Wrote {row_count:,} rows to bulk loader files")

            finally:
                if writer is not None:
                    self._close_csv_writer(writer, text_wrapper, zip_file)

            if row_count > 0:
                self.log.debug(f"Loading from files {local_files_list}")
                rows_loaded = self.load_from_files(
                    local_files_list,
                    file_compression='GZIP',
                    table_object=table_object,
                    table_to_load=table_to_load,
                    perform_rename=perform_rename,
                    analyze_compression=analyze_compression,
                )
                if rows_loaded != row_count:
                    self.log.error(
                        f"COPY from files should have loaded {row_count:,} "
                        f"but it reports {rows_loaded:,} rows loaded"
                    )
                return row_count
            else:
                self.log.info(f"{self} had nothing to do with 0 rows found")
                return 0
