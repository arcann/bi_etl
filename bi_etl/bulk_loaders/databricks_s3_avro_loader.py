from pathlib import Path
from tempfile import TemporaryDirectory
from typing import *

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.bulk_loaders.s3_bulk_loader_mixin import S3BulkLoaderMixin
from bi_etl.timer import Timer

if TYPE_CHECKING:
    from bi_etl.scheduler.etl_task import ETLTask
    from bi_etl.components.table import Table
else:
    ETLTask = None
    Table = None


class DatabricksS3AvroBulkLoader(BulkLoader, S3BulkLoaderMixin, AvroBulkLoaderMixin):
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

        if self.s3_file_max_rows is None and self.config.s3_files_to_generate is None:
            self.s3_file_max_rows = 50000

        self._init_avro()

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
            table_to_load: str = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str = None,
    ) -> int:
        table_to_load = table_to_load or table_object.qualified_table_name

        s3_full_folder = self._get_table_specific_folder_name(self.s3_folder, table_object)
        self._upload_files_to_s3(local_files, s3_full_folder)

        copy_sql = self._get_copy_into_sql(
            s3_source_path=s3_full_folder,
            table_to_load=table_to_load,
        )
        self.log.debug(copy_sql)

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

    def load_from_iterable(
            self,
            iterable: Iterable,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str = None,
            parent_task: Optional[ETLTask] = None,
    ) -> int:
        table_to_load = table_to_load or table_object.qualified_table_name

        with TemporaryDirectory(
                dir=self.config.temp_file_path,
                ignore_cleanup_errors=True,
        ) as temp_dir:
            parsed_schema = self._parse_avro_schema(table_object, table_to_load)

            file_number = 0
            data_length = 0
            local_files_list = []
            data_chunk = []

            progress_timer = Timer()
            for row_number, row in enumerate(iterable):
                data_chunk.append(row)

                if len(data_chunk) >= self.s3_file_max_rows:
                    data_length += len(data_chunk)
                    file_number += 1
                    self._write_avro_chunk(
                        temp_dir=temp_dir,
                        file_number=file_number,
                        parsed_schema=parsed_schema,
                        data_chunk=data_chunk,
                        local_files_list=local_files_list,
                    )
                    data_chunk = []

                if progress_frequency is not None:
                    if 0 < progress_frequency < progress_timer.seconds_elapsed:
                        self.log.info(f"Wrote row {row_number:,}")
                        progress_timer.reset()

            # Write final chunk
            if data_chunk:
                data_length += len(data_chunk)
                file_number += 1
                self._write_avro_chunk(
                    temp_dir=temp_dir,
                    file_number=file_number,
                    parsed_schema=parsed_schema,
                    data_chunk=data_chunk,
                    local_files_list=local_files_list,
                )

            if data_length > 0:
                self.log.debug(f"Loading from files {local_files_list}")
                rows_loaded = self.load_from_files(
                    local_files_list,
                    table_object=table_object,
                    table_to_load=table_to_load,
                    perform_rename=perform_rename,
                    analyze_compression=analyze_compression,
                )
                if rows_loaded != data_length:
                    self.log.error(
                        f"COPY INTO should have loaded {data_length:,} "
                        f"but reports {rows_loaded:,} rows loaded"
                    )
                return data_length
            else:
                self.log.info(f"{self} had nothing to do with 0 rows found")
                return 0
