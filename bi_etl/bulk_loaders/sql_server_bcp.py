import os
import tempfile
import typing

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.components.csv_writer import CSVWriter, QUOTE_MINIMAL
from bi_etl.components.table import Table
from bi_etl.scheduler.task import ETLTask
from bi_etl.utility.bcp_helpers import create_bcp_format_file, run_bcp, BCPError


class SQLServerBCP(BulkLoader):
    def __init__(self,
                 config: BIConfigParser,
                 bcp_encoding: str = 'utf-8',
                 ):
        super().__init__(config=config)
        self.delimiter = '\013'
        self._bcp_encoding = bcp_encoding

    def load_from_files(
            self,
            local_files: list,  # First file in list must be the format file
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str = None,
    ):
        format_file_path = None
        for file_name in local_files:
            # First file should be the format file
            if format_file_path is None:
                format_file_path = file_name
            else:
                try:
                    rows_inserted = run_bcp(
                        config=self.config,
                        table_name=table_object.qualified_table_name,
                        database_bind=table_object.database.bind,
                        file_path=file_name,
                        format_file_path=format_file_path,
                        start_line=1,
                        delimiter=self.delimiter,
                    )
                    self.log.info(f"{rows_inserted} rows inserted from {file_name}")
                except BCPError:
                    self.log.error(table_object.qualified_table_name, file_name)
                    raise
        if perform_rename:
            self.rename_table(table_to_load, table_object)

    def load_from_iterator(
            self,
            iterator: typing.Iterator,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str = None,
            parent_task: typing.Optional[ETLTask] = None,
    ) -> int:
        row_count = 0
        with tempfile.TemporaryDirectory() as temp_dir:
            format_file_path = os.path.join(temp_dir, f'data_{table_object.table_name}.fmt')
            data_file_path = os.path.join(temp_dir, f'data_{table_object.table_name}.data')

            create_bcp_format_file(
                table_object,
                format_file_path,
                delimiter=f'\\{ord(self.delimiter):03o}',
                row_terminator='\\n'
            )

            with CSVWriter(
                parent_task,
                data_file_path,
                delimiter=self.delimiter,
                column_names=table_object.column_names,
                include_header=False,
                encoding='utf-8',
                escapechar='\\',
                quoting=QUOTE_MINIMAL,
            ) as target_file:
                for row in iterator:
                    row_count += 1
                    target_file.insert_row(row)

            self.load_from_files(
                [format_file_path, data_file_path],
                file_compression='GZIP',
                table_object=table_object,
                table_to_load=table_to_load,
                perform_rename=perform_rename,
                analyze_compression=analyze_compression,
            )
            return row_count
