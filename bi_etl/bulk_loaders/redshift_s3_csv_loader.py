# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import gzip
import io
import os.path
import time
import typing
from tempfile import TemporaryDirectory

import sqlalchemy

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
                 s3_clear_when_done: bool = True,
                 has_header: bool = True,
                 ):
        super().__init__(
            config=config,
            config_section=config_section,
            s3_user_id=s3_user_id,
            s3_keyring_password_section=s3_keyring_password_section,
            s3_bucket_name=s3_bucket_name,
            s3_folder=s3_folder,
            s3_files_to_generate=s3_files_to_generate,
            s3_clear_when_done=s3_clear_when_done,
        )
        self.s3_file_delimiter = '|'
        self.null_value = ''
        self.s3_clear_when_done = False
        self.analyze_compression = None
        self.has_header = has_header

    def __reduce_ex__(self, protocol):
        return (
            # A callable object that will be called to create the initial version of the object.
            self.__class__,

            # A tuple of arguments for the callable object. An empty tuple must be given if the callable does not accept any argument
            (
                self.config,
                self.config_section,
                self.s3_user_id,
                self.s3_keyring_password_section,
                self.s3_bucket_name,
                self.s3_folder,
                self.s3_files_to_generate,
                self.s3_clear_when_done,
                self.has_header,
            ),

            # Optionally, the object’s state, which will be passed to the object’s __setstate__() method as previously described.
            # If the object has no such method then, the value must be a dictionary and it will be added to the object’s __dict__ attribute.
            None,

            # Optionally, an iterator (and not a sequence) yielding successive items.
            # These items will be appended to the object either using obj.append(item) or, in batch, using obj.extend(list_of_items).

            # Optionally, an iterator (not a sequence) yielding successive key-value pairs.
            # These items will be stored to the object using obj[key] = value

            # PROTOCOL 5+ only
            # Optionally, a callable with a (obj, state) signature.
            # This callable allows the user to programmatically control the state-updating behavior of a specific object,
            # instead of using obj’s static __setstate__() method.
            # If not None, this callable will have priority over obj’s __setstate__().
        )

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str = None,
            options: str = '',
    ):
        if self.has_header:
            header_option = 'IGNOREHEADER 1'
        else:
            header_option = ''

        analyze_compression = analyze_compression or self.analyze_compression
        if analyze_compression:
            options += f' COMPUPDATE {self.analyze_compression} '

        if self.s3_region is not None:
            region_option = f"region '{self.s3_region}'"

        else:
            region_option = ''

        return f"""\
                COPY {table_to_load} 
                     FROM 's3://{self.s3_bucket_name}/{s3_source_path}'
                     CSV 
                     delimiter '{self.s3_file_delimiter}'
                     null '{self.null_value}' 
                     credentials 'aws_access_key_id={self.s3_user_id};aws_secret_access_key={self.s3_password}'
                     {region_option}
                     {header_option} 
                     {file_compression}
                     {options}; commit;
                """

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
                            include_header=self.has_header,
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
                    writer.insert_row(row)
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
