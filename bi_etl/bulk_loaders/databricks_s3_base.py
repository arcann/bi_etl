# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.bulk_loaders.s3_bulk_loader_mixin import S3BulkLoaderMixin

if TYPE_CHECKING:
    from bi_etl.components.table import Table


class DatabricksS3Base(S3BulkLoaderMixin, BulkLoader):
    """Common base for Databricks bulk loaders that stage files on S3 and use
    ``INSERT INTO ... FROM read_files(...)`` to ingest them.

    Subclasses must implement :meth:`_get_copy_into_sql` to supply the
    format-specific ``read_files`` options and override
    :meth:`load_from_iterable` (typically by mixing in a format mixin
    such as :class:`AvroBulkLoaderMixin` or :class:`CsvBulkLoaderMixin`).
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
    ):
        """Initialise the Databricks S3 loader.

        Parameters
        ----------
        config
            :class:`~bi_etl.bulk_loaders.s3_bulk_load_config.S3_Bulk_Loader_Config` with the S3 bucket, folder
            and ``s3_file_max_rows`` settings.
        """
        super().__init__()
        self.config = config
        self._init_s3(config)
        if self.config.s3_file_max_rows is not None:
            self.rows_per_file = self.config.s3_file_max_rows

    # --- SQL generation (format-specific) ------------------------------------

    def _get_copy_into_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
    ) -> str:
        """Return the SQL statement used to load data from S3 into the table.

        Must be implemented by each format-specific subclass.
        """
        raise NotImplementedError()

    # --- Load from files -----------------------------------------------------

    def load_from_files(
            self,
            local_files: List[Union[str, Path]],
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str | None = None,
    ) -> int:
        """Upload *local_files* to S3 and execute the format-specific SQL.

        This is the common Databricks load path:

        1. Wait for the background upload of the local files to the table-specific S3 folder
           (and upload any that were not queued).
        2. Build and execute the SQL returned by :meth:`_get_copy_into_sql`.
        3. Optionally clean the S3 folder and rename the table.

        Returns the number of rows inserted as reported by the database.
        """
        table_to_load = table_to_load or table_object.qualified_table_name

        try:
            s3_full_folder, _ = self._upload_files_to_s3(local_files, table_object)

            copy_sql = self._get_copy_into_sql(
                s3_source_path=s3_full_folder,
                table_to_load=table_to_load,
            )
            self.log_with_redactions(
                log_level=logging.INFO,
                message=copy_sql,
            )

            rows_inserted = 0
            conn = None
            try:
                conn = table_object.database.bind.raw_connection()
                cursor = conn.cursor()
                cursor.execute(copy_sql)
                for result_row in cursor.fetchall():
                    rows_inserted += result_row[1]
                conn.commit()
            except Exception as e:
                self.log.error(f"COPY INTO failed: {e}")
                raise
            finally:
                if conn is not None:
                    conn.close()
        except BaseException:
            self._handle_load_failure()
            raise

        if self.s3_clear_when_done:
            self.clean_s3_folder(s3_full_folder)

        if perform_rename:
            self.rename_table(table_to_load, table_object)

        return rows_inserted
