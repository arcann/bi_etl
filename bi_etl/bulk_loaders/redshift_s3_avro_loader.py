# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os.path
import os.path
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory
from typing import *

import fastavro

from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.task import ETLTask


class RedShiftS3AvroBulk(RedShiftS3Base):
    def __init__(
        self,
        config: S3_Bulk_Loader_Config,
    ):
        super().__init__(
            config=config,
        )
        if self.s3_file_max_rows is None and self.s3_files_to_generate is None:
            self.s3_file_max_rows = 50000

        # Redshift appears to count the schema as a line read
        self.lines_scanned_modifier = -1

        try:
            import snappy
            self.codec = 'snappy'
        except ImportError:
            self.codec = 'deflate'

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
                     AVRO 'auto'
                     {file_compression}  
                     {options}
               """

    def _write_to_file(
            self,
            temp_dir,
            file_number: int,
            parsed_schema,
            data_chunk: list,
            local_files_list: list,
    ):

        self.log.debug(f"Starting bulk load chunk {file_number}")
        filepath = os.path.join(temp_dir, f'data_{file_number}.avro')
        local_files_list.append(filepath)
        with open(filepath, 'wb') as avro_file:
            # avro_iterators = self.distribute(iterator, writer_pool_size)
            fastavro.writer(avro_file, parsed_schema, data_chunk, codec=self.codec)
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
                str: ['string'],
                bytes: ['bytes'],
                date: ['string'],
                datetime: ['string'],
                time: ['string'],
                timedelta: ['string'],
                bool: ['boolean'],
                int: ['long'],
                float: ['double'],
                Decimal: ['int', 'double'],
            }
            for column in table_object.columns:
                if column.type.python_type in type_map:
                    col_type = type_map[column.type.python_type]
                else:
                    col_type = ['string']

                fields.append({
                    'name': column.name,
                    'type': ["null"] + col_type,
                    'default': None,
                })

            schema = {
                "name": table_to_load,
                "type": "record",
                'fields': fields,
            }

            self.log.debug(f"schema = {schema}")

            parsed_schema = fastavro.parse_schema(schema)

            self.log.debug(f"parsed_schema = {parsed_schema}")

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
                        parsed_schema=parsed_schema,
                        data_chunk=data_chunk,
                        local_files_list=local_files_list,
                    )
                    data_chunk = list()

            # Write final chunk
            if len(data_chunk) >= 0:
                data_length += len(data_chunk)
                file_number += 1
                self._write_to_file(
                    temp_dir=temp_dir,
                    file_number=file_number,
                    parsed_schema=parsed_schema,
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
