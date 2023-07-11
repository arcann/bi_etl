# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os.path
import os.path
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory
from typing import *

import pyarrow as pa
import pyarrow.parquet as pq

from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.task import ETLTask


class RedShiftS3ParquetBulk(RedShiftS3Base):
    def __init__(
        self,
        config: S3_Bulk_Loader_Config,
    ):
        super().__init__(
            config=config,
        )

        if self.s3_file_max_rows is None and self.s3_files_to_generate is None:
            self.s3_file_max_rows = 2_000_000

        self.lines_scanned_modifier = 0

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
                     FORMAT PARQUET
                     {file_compression}  
                     {options}
               """

    def _write_to_file(
            self,
            temp_dir,
            file_number: int,
            schema: pa.Schema,
            data_chunk: list,
            local_files_list: list,
    ):
        self.log.debug(f"Starting bulk load chunk {file_number}")
        # TODO: Redshift will recognize and uncompress these file types
        #   .gz
        #   .snappy
        #   .bz2
        filepath = os.path.join(temp_dir, f'data_{file_number}.parquet.snappy')
        local_files_list.append(filepath)
        table = pa.Table.from_pylist(data_chunk, schema=schema)
        pq.write_table(table, filepath, compression='SNAPPY')
        self.log.debug(f"Closed bulk load chunk {file_number}: {filepath}")

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

        with TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            # Generate schema from table
            fields = list()
            type_map = {
                str: pa.string(),
                bytes: pa.large_binary(),
                date: pa.date32(),
                datetime: pa.date64(),
                time: pa.time64('us'),
                timedelta: pa.month_day_nano_interval(),
                bool: pa.bool_(),
                int: pa.int64(),
                float: pa.float64(),
            }
            for column in table_object.columns:
                if column.type.python_type in type_map:
                    col_type = type_map[column.type.python_type]
                else:
                    if column.type.python_type == Decimal:
                        col_type = pa.decimal128(
                            column.type.precision,
                            column.type.scale,
                        )
                    else:
                        col_type = pa.string()

                fields.append(
                    pa.field(
                        column.name,
                        col_type,
                        True,  # Nullable
                    )
                )

            schema = pa.schema(fields)

            self.log.debug(f"schema = {schema}")

            file_number = 0
            data_length = 0
            local_files_list = list()

            # Note: Tried using this method to chunk the list, but it didn't work with the
            # gevent based threading used by insert_row with bulk loader
            # for data_chunk in more_itertools.chunked(iterator, self.s3_file_max_rows):

            data_chunk = list()
            for row in iterable:
                data_chunk.append(row)

                if len(data_chunk) >= self.s3_file_max_rows:
                    data_length += len(data_chunk)
                    file_number += 1
                    self._write_to_file(
                        temp_dir=temp_dir,
                        file_number=file_number,
                        schema=schema,
                        data_chunk=data_chunk,
                        local_files_list=local_files_list,
                    )
                    # TODO: We could start uploading the files to S3 with a gevent "thread" here
                    data_chunk = list()

            # Write final chunk
            if len(data_chunk) >= 0:
                data_length += len(data_chunk)
                file_number += 1
                self._write_to_file(
                    temp_dir=temp_dir,
                    file_number=file_number,
                    schema=schema,
                    data_chunk=data_chunk,
                    local_files_list=local_files_list,
                )

            self.log.debug(f"Loading from files {local_files_list}")
            rows_loaded = self.load_from_files(
                local_files_list,
                table_object=table_object,
                table_to_load=table_to_load,
                perform_rename=perform_rename,
                analyze_compression=analyze_compression,
            )
            if rows_loaded != data_length:
                self.log.error(f"COPY from files should have loaded {data_length:,} but it reports {rows_loaded:,} rows loaded")
            else:
                self.log.info(f"{self} had nothing to do with 0 rows found")
            return data_length
