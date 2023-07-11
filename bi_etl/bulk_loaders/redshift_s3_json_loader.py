# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import gzip
import io
import json
import os.path
import os.path
from typing import *
from datetime import datetime
from tempfile import TemporaryDirectory

from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.timer import Timer

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.task import ETLTask


class RedShiftS3JSONBulk(RedShiftS3Base):
    def __init__(self,
                 config: S3_Bulk_Loader_Config,
                 ):
        super().__init__(
            config=config,
        )

    @property
    def needs_all_columns(self):
        return False

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str = None,
            options: str = '',
    ):
        analyze_compression = analyze_compression or self.analyze_compression
        if analyze_compression:
            options += f' COMPUPDATE {self.analyze_compression} '

        return f"""\
                COPY {table_to_load} FROM 's3://{self.s3_bucket_name}/{s3_source_path}'                      
                     credentials 'aws_access_key_id={self.s3_user_id};aws_secret_access_key={self.s3_password}'
                     JSON 'auto'
                     {file_compression}  
                     {options}
               """

    @staticmethod
    def json_serializer(value):
        if isinstance(value, datetime):
            return str(value)
        else:
            # raise ValueError(f'No json_serializer support for {repr(value)}')
            str(value)

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
        row_count = 0
        with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            local_files = []
            zip_pool = []
            text_wrapper_pool = []

            writer_pool_size = self.s3_files_to_generate

            for file_number in range(writer_pool_size):
                filepath = os.path.join(temp_dir, f'data_{file_number}.json.gz')
                local_files.append(filepath)
                zip_file = gzip.open(filepath, 'wb')
                # noinspection PyTypeChecker
                text_wrapper = io.TextIOWrapper(zip_file, encoding='utf-8')
                text_wrapper_pool.append(text_wrapper)
                zip_pool.append(zip_file)

            progress_timer = Timer()
            for row_number, row in enumerate(iterable):
                row_count += 1
                text_wrapper = text_wrapper_pool[row_number % writer_pool_size]
                text_wrapper.write(json.dumps(row.as_dict, default=self.json_serializer))
                text_wrapper.write("\n")
                if progress_frequency is not None:
                    # noinspection PyTypeChecker
                    if 0 < progress_frequency < progress_timer.seconds_elapsed:
                        self.log.info(f"Wrote row {row_number:,}")
                        progress_timer.reset()

            for text_wrapper in text_wrapper_pool:
                text_wrapper.close()

            for zip_file in zip_pool:
                zip_file.close()

            if row_count > 0:
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
