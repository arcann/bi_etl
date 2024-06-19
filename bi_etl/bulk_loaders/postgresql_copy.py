import os.path
import tempfile
from pathlib import Path
from typing import *

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.postgresql_bulk_load_config import PostgreSQLBulkLoaderConfig
from bi_etl.components.csv_writer import CSVWriter, QUOTE_MINIMAL
from bi_etl.utility.postgresql.psycopg_helpers import psycopg_import_using_cursor

if TYPE_CHECKING:
    from bi_etl.scheduler.task import ETLTask
    from bi_etl.components.table import Table
else:
    ETLTask = None
    Table = None


class PostgreSQLCopy(BulkLoader):
    def __init__(
            self,
            config: PostgreSQLBulkLoaderConfig,
    ):
        super().__init__(
        )
        self.config = config

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
        rows_inserted = 0
        conn = None
        try:
            conn = table_object.database.bind.raw_connection()

            # conn.set_client_encoding(self.config.encoding)
            conn.execute("SET client_encoding TO UTF8")

            cursor = conn.cursor()
            for file_name in local_files:
                rows_inserted = psycopg_import_using_cursor(
                    cursor=cursor,
                    table_spec=table_object.qualified_table_name,
                    input_file_path=file_name,
                    delimiter=self.config.delimiter,
                    csv_mode=True,
                    header=self.config.header,
                    null=self.config.null,
                    encoding=self.config.encoding,
                )
                self.log.info(f"{rows_inserted} rows inserted from {file_name}")
            # Note: We need to commit here otherwise the changes are lost when we close the raw connection.
            conn.commit()
        finally:
            if conn is not None:
                conn.close()
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
        with tempfile.TemporaryDirectory(dir=self.config.temp_file_path, ignore_cleanup_errors=True) as temp_dir:
            data_file_path = os.path.join(temp_dir, f'data_{table_object.table_name}.data')

            # Save to a file first, so we can call load_from_files
            with open(data_file_path, 'w+', encoding="utf-8") as file:
                with CSVWriter(
                    parent_task,
                    file,
                    delimiter=self.config.delimiter,
                    column_names=table_object.column_names,
                    include_header=self.config.header,
                    encoding='utf-8',
                    escapechar='\\',
                    quoting=QUOTE_MINIMAL,
                    null=self.config.null,
                ) as writer:
                    for row in iterable:
                        writer.insert_row(row)

            row_count = self.load_from_files(
                [data_file_path],
                table_object=table_object,
                table_to_load=table_to_load,
                perform_rename=perform_rename,
                analyze_compression=analyze_compression,
            )
            return row_count
