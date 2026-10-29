# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import gzip
import io
import os.path
import os.path
import textwrap
from tempfile import TemporaryDirectory
from typing import *

from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.components.row.row import Row
from bi_etl.timer import Timer
from bi_etl.utility.json import json_dumps

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.etl_task import ETLTask


class RedShiftS3JSONBulk(RedShiftS3Base):
    """
    Bulk loader for Redshift using gzipped JSON files staged to S3 and ``COPY ... JSON 'auto'``.

    Note: ``s3_file_max_rows`` is used as the number of rows per JSON file
    Each file is queued for upload as soon as it is complete.
    """
    DEFAULT_ROWS_PER_FILE = 25_000

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
            ):
        """
        Parameters
        ----------
        config:
            :class:`~bi_etl.bulk_loaders.s3_bulk_load_config.S3_Bulk_Loader_Config`
            with the S3 and Redshift settings.
        """
        super().__init__(
            config=config,
        )

    @property
    def needs_all_columns(self):
        """
        Always ``False``. ``JSON 'auto'`` maps keys to columns by name, so a subset of columns can be loaded.
        """
        return False

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str | None = None,
            options: str = '',
    ):
        """
        Build the JSON ``COPY`` statement.

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

        return textwrap.dedent(
            f"""\
            {base_copy} --JSON specific Options:                      
            JSON 'auto'
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
        Write rows from *iterable* to local gzipped JSON files of at most ``rows_per_file`` rows each,
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
            Optional parent task (not used).

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
            text_wrapper = None
            zip_file = None
            row_count = 0
            current_row_number = 0
            try:
                progress_timer = Timer()
                for row in iterable:
                    row_count += 1
                    if text_wrapper is None or current_row_number >= self.rows_per_file:
                        if text_wrapper is not None:
                            file_number += 1
                            text_wrapper.close()
                            zip_file.close()
                            self._queue_file_for_upload(local_files[-1])

                        current_row_number = 0
                        filepath = os.path.join(temp_dir, f'data_{file_number}.json.gz')
                        local_files.append(filepath)
                        zip_file = gzip.open(filepath, 'wb')
                        # noinspection PyTypeChecker
                        text_wrapper = io.TextIOWrapper(zip_file, encoding='utf-8')
                    current_row_number += 1
                    json_content = json_dumps(row.as_dict)
                    if json_content is not None:
                        text_wrapper.write(json_content)
                    text_wrapper.write("\n")
                    if progress_frequency is not None:
                        # noinspection PyTypeChecker
                        if 0 < progress_frequency < progress_timer.seconds_elapsed:
                            self.log.info(f"Wrote row {row_count:,}")
                            progress_timer.reset()
                self.log.info(f"Wrote {row_count:,} rows to bulk loader file")

            finally:
                if text_wrapper is not None:
                    text_wrapper.close()
                    zip_file.close()

            if row_count > 0:
                # Only reached when the loop completed, so the last file is complete
                self._queue_file_for_upload(local_files[-1])
                self.load_from_files(
                    local_files,
                    file_compression='GZIP',
                    table_object=table_object,
                    table_to_load=table_to_load,
                    perform_rename=perform_rename,
                    analyze_compression=analyze_compression,
                )
            else:
                self.log.info(f"{self} had nothing to do with 0 rows found")

            return row_count
