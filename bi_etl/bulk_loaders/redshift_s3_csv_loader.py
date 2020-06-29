# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import gzip
import io
import os.path
import typing
from tempfile import TemporaryDirectory

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.components.csv_writer import CSVWriter, QUOTE_MINIMAL
from bi_etl.timer import Timer

if typing.TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.task import ETLTask


class RedShiftS3CSVBulk(RedShiftS3Base):
    def __init__(self,
                 config: BIConfigParser,
                 config_section: str = 's3_bulk',
                 s3_user_id: typing.Optional[str] = None,
                 s3_keyring_password_section: typing.Optional[str] = None,
                 s3_bucket_name: typing.Optional[str] = None,
                 s3_folder: typing.Optional[str] = None,
                 s3_files_to_generate: typing.Optional[int] = None,
                 ):
        super().__init__(
            config=config,
            config_section=config_section,
            s3_user_id=s3_user_id,
            s3_keyring_password_section=s3_keyring_password_section,
            s3_bucket_name=s3_bucket_name,
            s3_folder=s3_folder,
            s3_files_to_generate=s3_files_to_generate,
        )
        self.s3_file_delimiter = '|'
        self.null_value = ''
        self.s3_clear_before = True
        self.s3_clear_when_done = True
        self.analyze_compression = None

    def load_from_files(
            self,
            local_files: list,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str = None,
            has_header: bool = True,
    ):
        s3_full_folder = self._get_table_specific_folder_name(self.s3_folder, table_object)
        self._upload_files_to_s3(local_files, s3_full_folder)

        analyze_compression = analyze_compression or self.analyze_compression
        if analyze_compression:
            options += f' COMPUPDATE {self.analyze_compression} '

        table_to_load = table_to_load or table_object.qualified_table_name

        if has_header:
            header_cmd = 'IGNOREHEADER 1'
        else:
            header_cmd = ''

        copy_sql = f"""\
                    COPY {table_to_load} 
                         FROM 's3://{self.s3_bucket_name}/{s3_full_folder}'
                         CSV 
                         delimiter '{self.s3_file_delimiter}'
                         null '{self.null_value}' 
                         credentials 'aws_access_key_id={self.s3_user_id};aws_secret_access_key={self.s3_password}'
                         {header_cmd} 
                         {file_compression}
                         {options}; commit;
                    """

        self._run_copy_sql(
            copy_sql=copy_sql,
            s3_full_folder=s3_full_folder,
            table_object=table_object,
        )

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
        with TemporaryDirectory() as temp_dir:
            writer_pool_size = self.s3_files_to_generate
            local_files = []
            zip_pool = []
            text_wrapper_pool = []
            writer_pool = []
            try:
                for file_number in range(writer_pool_size):
                    filepath = os.path.join(temp_dir, f'data_{file_number}.csv.gz')
                    local_files.append(filepath)
                    zip_file = gzip.open(filepath, 'wb')
                    text_wrapper = io.TextIOWrapper(zip_file, encoding='utf-8')
                    writer = CSVWriter(
                            parent_task,
                            text_wrapper,
                            delimiter=self.s3_file_delimiter,
                            column_names=table_object.column_names,
                            include_header=True,
                            encoding='utf-8',
                            escapechar='\\',
                            quoting=QUOTE_MINIMAL,
                            )
                    text_wrapper_pool.append(text_wrapper)
                    zip_pool.append(zip_file)
                    writer_pool.append(writer)

                progress_timer = Timer()
                for row_number, row in enumerate(iterator):
                    row_count += 1
                    writer = writer_pool[row_number % writer_pool_size]
                    writer.insert(row)
                    if progress_frequency is not None:
                        # noinspection PyTypeChecker
                        if 0 < progress_frequency < progress_timer.seconds_elapsed:
                            self.log.info(f"Wrote row {row_number:,}")
                            progress_timer.reset()
                self.log.info(f"Wrote {row_number:,} rows to bulk loader file")

            finally:
                for writer in writer_pool:
                    writer.close()

                for text_wrapper in text_wrapper_pool:
                    text_wrapper.close()

                for zip_file in zip_pool:
                    zip_file.close()

            self.load_from_files(
                local_files,
                file_compression='GZIP',
                table_object=table_object,
                table_to_load=table_to_load,
                perform_rename=perform_rename,
                analyze_compression=analyze_compression,
            )
            return row_count
