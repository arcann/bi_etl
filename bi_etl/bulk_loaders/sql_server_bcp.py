import os
import re
import tempfile
from typing import *

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.components.table import Table
from bi_etl.scheduler.task import ETLTask
from bi_etl.utility.bcp_helpers import create_bcp_format_file, run_bcp, BCPError, BCP_Config


class SQLServerBCP(BulkLoader):
    def __init__(
        self,
        bcp_config: BCP_Config,
        bcp_encoding: str = 'utf-8',
    ):
        super().__init__()
        self.bcp_config = bcp_config
        self.delimiter = '\013'
        self._bcp_encoding = bcp_encoding

    @staticmethod
    def multiple_replace_safe(string, rep_dict):
        if string == '':
            return '\000'
        # noinspection PyTypeChecker
        pattern = re.compile("|".join([re.escape(k) for k in sorted(rep_dict, key=len, reverse=True)]), flags=re.DOTALL)
        return pattern.sub(lambda x: rep_dict[x.group(0)], string)

    def load_from_files(
            self,
            local_files: list,  # First file in list must be the format file
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str = None,
    ) -> int:
        rows_inserted = 0
        format_file_path = None
        for file_name in local_files:
            # First file should be the format file
            if format_file_path is None:
                format_file_path = file_name
            else:
                try:
                    rows_inserted = run_bcp(
                        config=self.bcp_config,
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
        return rows_inserted

    @staticmethod
    def value_for_bcp(column_value):
        if column_value is None:
            return ''
        else:
            column_value = str(column_value)
            # Line delimiter default is \r\n, so we'll replace that with just \n
            column_value = column_value.replace('\r\n', '\n')
            if column_value == '':
                # ASCII null should be for an empty string
                column_value = '\000'
            return column_value

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
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            format_file_path = os.path.join(temp_dir, f'data_{table_object.table_name}.fmt')
            data_file_path = os.path.join(temp_dir, f'data_{table_object.table_name}.data')

            create_bcp_format_file(
                table_object,
                format_file_path,
                delimiter=f'\\{ord(self.delimiter):03o}',
                row_terminator='\\r\\n'
            )

            with open(data_file_path, 'w+', encoding="utf-8") as file:
                for row in iterable:
                    line = self.delimiter.join([self.value_for_bcp(row[col_name]) for col_name in table_object.columns])
                    file.write(line + '\n')

            # with CSVWriter(
                # parent_task,
                # data_file_path,
                # delimiter=self.delimiter,
                # column_names=table_object.column_names,
                # include_header=False,
                # encoding='utf-8',
                # escapechar='\\',
                # doublequote=False,
                # quotechar='\000',
                # quoting=QUOTE_NONE,
            # ) as target_file:
                # for row in iterator:
                    # row_count += 1
                    # target_file.insert_row(row)

            row_count = self.load_from_files(
                [format_file_path, data_file_path],
                table_object=table_object,
                table_to_load=table_to_load,
                perform_rename=perform_rename,
                analyze_compression=analyze_compression,
            )
            return row_count
