import logging
from pathlib import Path
from typing import *

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.bulk_loaders.s3_bulk_loader_mixin import S3BulkLoaderMixin

if TYPE_CHECKING:
    from bi_etl.components.table import Table
else:
    Table = None


class DatabricksS3AvroBulkLoader(S3BulkLoaderMixin, AvroBulkLoaderMixin, BulkLoader):
    """
    Bulk loader for Databricks using Avro files staged to S3 and COPY INTO.

    Note: s3_file_max_rows is used as the Avro chunk size
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
    ):
        super().__init__()
        self.config = config
        self._init_s3(config)
        self.s3_file_max_rows = self.config.s3_file_max_rows

        if self.s3_file_max_rows is None:
            self.s3_file_max_rows = 50000

        self._init_avro(chunk_size=self.s3_file_max_rows)

    @property
    def needs_all_columns(self):
        return False

    # --- COPY INTO SQL -----------------------------------------------------

    def _get_copy_into_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
    ) -> str:
        # Credentials are optional: the Databricks cluster's instance profile
        # or Unity Catalog storage credential typically handles S3 access.
        credentials = '--no credentials'
        s3_user_id = self.config.user_id
        if s3_user_id is not None:
            s3_password = self.config.get_password()
            self.add_redact_value(s3_password)
            credentials = (
                f"CREDENTIAL (AWS_ACCESS_KEY = '{s3_user_id}', "
                f"AWS_SECRET_KEY = '{s3_password}')"
            )

        return (
            f"COPY INTO {table_to_load}\n"
            f"FROM 's3://{self.s3_bucket_name}/{s3_source_path}'\n"
            f"{credentials}\n"
            f"FILEFORMAT = AVRO\n"
            f"COPY_OPTIONS ('mergeSchema' = 'true')"
        )

    # --- Public interface --------------------------------------------------

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
        table_to_load = table_to_load or table_object.qualified_table_name

        s3_full_folder = self._get_table_specific_folder_name(self.s3_folder, table_object)
        self._upload_files_to_s3(local_files, s3_full_folder)

        copy_sql = self._get_copy_into_sql(
            s3_source_path=s3_full_folder,
            table_to_load=table_to_load,
        )
        self.log_with_redactions(
            log_level=logging.DEBUG,
            message=copy_sql
        )

        rows_inserted = 0
        conn = None
        try:
            conn = table_object.database.bind.raw_connection()
            cursor = conn.cursor()
            cursor.execute(copy_sql)
            # COPY INTO returns rows of (fileName, num_affected_rows, num_inserted_rows)
            for result_row in cursor.fetchall():
                rows_inserted += result_row[1]
            conn.commit()
        except Exception as e:

            self.log.error(f"COPY INTO failed: {e}")
            raise
        finally:
            if conn is not None:
                conn.close()

        if self.s3_clear_when_done:
            self.clean_s3_folder(s3_full_folder)

        if perform_rename:
            self.rename_table(table_to_load, table_object)

        return rows_inserted
