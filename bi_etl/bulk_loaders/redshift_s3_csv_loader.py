# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import gzip
import io
import os.path
import textwrap
from typing import *
from tempfile import TemporaryDirectory

from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.components.csv_writer import CSVWriter, QUOTE_MINIMAL
from bi_etl.components.row.row import Row
from bi_etl.timer import Timer

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.etl_task import ETLTask


class RedShiftS3CSVBulk(RedShiftS3Base):
    """
    Bulk loader for Redshift using gzipped CSV files staged to S3 and ``COPY ... FORMAT CSV``.

    Note: ``s3_file_max_rows`` is used as the number of rows per CSV file (default 25,000).
    Each file is queued for upload as soon as it is complete.
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
            has_header: bool = True,
            s3_file_delimiter: str = '|',
            null_value: str = '',
            ):
        """
        Parameters
        ----------
        config:
            :class:`~bi_etl.bulk_loaders.s3_bulk_load_config.S3_Bulk_Loader_Config`
            with the S3 and Redshift settings.
        has_header:
            Whether each file starts with a header line (skipped by the ``COPY``).
        s3_file_delimiter:
            Field delimiter used in the files.
        null_value:
            Text that represents a null value in the files.
        """
        super().__init__(
            config=config,
        )
        self.s3_file_delimiter = s3_file_delimiter
        if self.s3_file_max_rows is None:
            self.s3_file_max_rows = 25000
        self.null_value = null_value
        self.has_header = has_header
        if self.has_header:
            # Note: This is per file so the row count will be = rows_scanned - (lines_scanned_modifier * len(file_list))
            self.lines_scanned_modifier = -1

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str = None,
            options: str = '',
    ):
        """
        Build the CSV ``COPY`` statement.

        Parameters
        ----------
        s3_source_path:
            Path of the S3 folder (within the bucket) containing the files to load.
        table_to_load:
            Qualified name of the table to load.
        file_compression:
            Compression option text to add to the statement (e.g. ``GZIP``).
        analyze_compression:
            ``COMPUPDATE`` setting. Defaults to the configured ``analyze_compression``.
        options:
            Additional ``COPY`` options to append.

        Returns
        -------
        str
            The SQL text.
        """
        base_copy = self._get_base_copy(
            s3_source_path=s3_source_path,
            table_to_load=table_to_load,
        )

        if self.has_header:
            header_option = 'IGNOREHEADER 1'
        else:
            header_option = ''

        return textwrap.dedent(
            f"""\
            {base_copy} --CSV specific Options:
            FORMAT CSV
            DELIMITER '{self.s3_file_delimiter}'
            NULL '{self.null_value}' 
            {header_option} 
            {file_compression}
            {self._get_compression_option_str(analyze_compression)}
            {options}; commit;
            """
            )

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
        Write rows from *iterable* to local gzipped CSV files of at most ``s3_file_max_rows`` rows each,
        and load them with :meth:`load_from_files`.

        Each file is queued for upload (see :meth:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader._queue_file_for_upload`)
        as soon as it is closed, so :meth:`load_from_files` only has to wait for the uploads still in progress.

        Parameters
        ----------
        iterable:
            Source of :class:`~bi_etl.components.row.row.Row` objects to load.
        table_object:
            Table being loaded.
        table_to_load:
            Name of the table (or temp table) to load into. Defaults to ``table_object.qualified_table_name``.
        perform_rename:
            If ``True``, rename ``table_to_load`` over the original table after the load.
        progress_frequency:
            Seconds between progress log messages. Pass ``None`` to disable.
        analyze_compression:
            ``COMPUPDATE`` setting. Defaults to the configured ``analyze_compression``.
        parent_task:
            Optional parent task, forwarded to :class:`~bi_etl.components.csv_writer.CSVWriter`.

        Returns
        -------
        int
            Number of rows written.
        """
        with TemporaryDirectory(
                dir=self.config.temp_file_path,
                ignore_cleanup_errors=True,
        ) as temp_dir, self._file_upload_session(table_object):
            local_files = []
            file_number = 0
            current_file = None
            text_wrapper = None
            zip_file = None
            row_number = 0
            current_row_number = 0
            try:
                progress_timer = Timer()
                for row in iterable:
                    row_number += 1
                    if current_file is None or current_row_number >= self.s3_file_max_rows:
                        if current_file is not None:
                            file_number += 1
                            current_file.close()
                            text_wrapper.close()
                            zip_file.close()
                            self._queue_file_for_upload(local_files[-1])

                        current_row_number = 0
                        filepath = os.path.join(temp_dir, f'data_{file_number}.csv.gz')
                        local_files.append(filepath)
                        zip_file = gzip.open(filepath, 'wb')
                        # noinspection PyTypeChecker
                        text_wrapper = io.TextIOWrapper(zip_file, encoding='utf-8')
                        current_file = CSVWriter(
                            parent_task,
                            text_wrapper,
                            delimiter=self.s3_file_delimiter,
                            column_names=table_object.column_names,
                            include_header=self.has_header,
                            encoding='utf-8',
                            escapechar='\\',
                            quoting=QUOTE_MINIMAL,
                        )
                    current_row_number += 1
                    current_file.insert_row(row)
                    if progress_frequency is not None:
                        # noinspection PyTypeChecker
                        if 0 < progress_frequency < progress_timer.seconds_elapsed:
                            self.log.info(f"Wrote row {row_number:,}")
                            progress_timer.reset()
                self.log.info(f"Wrote {row_number:,} rows to bulk loader file")

            finally:
                if current_file is not None:
                    current_file.close()
                    text_wrapper.close()
                    zip_file.close()

            if row_number > 0:
                # Only reached when the loop completed, so the last file is complete
                self._queue_file_for_upload(local_files[-1])
                rows_loaded = self.load_from_files(
                    local_files,
                    file_compression='GZIP',
                    table_object=table_object,
                    table_to_load=table_to_load,
                    perform_rename=perform_rename,
                    analyze_compression=analyze_compression,
                )
                if rows_loaded != row_number:
                    self.log.error(
                        f"COPY from files should have loaded {row_number:,} but it reports {rows_loaded:,} rows loaded"
                        )
            else:
                self.log.info(f"{self} had nothing to do with 0 rows found")
            return row_number
