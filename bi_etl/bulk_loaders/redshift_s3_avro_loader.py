# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import textwrap
from tempfile import TemporaryDirectory
from typing import *

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config

if TYPE_CHECKING:
    from bi_etl.components.table import Table
    from bi_etl.scheduler.etl_task import ETLTask


class RedShiftS3AvroBulk(RedShiftS3Base, AvroBulkLoaderMixin):
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

        self._init_avro()

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
        base_copy = self._get_base_copy(
            s3_source_path=s3_source_path,
            table_to_load=table_to_load,
        )

        return textwrap.dedent(f"""\
            {base_copy} --AVRO specific Options:
            AVRO 'auto'
            {file_compression}  
            {self._get_compression_option_str(analyze_compression)}
            {options}; commit;
            """)

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
            parsed_schema = self._parse_avro_schema(table_object, table_to_load)

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
                    self._write_avro_chunk(
                        temp_dir=temp_dir,
                        file_number=file_number,
                        parsed_schema=parsed_schema,
                        data_chunk=data_chunk,
                        local_files_list=local_files_list,
                    )
                    data_chunk = list()

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
                    f"COPY from files should have loaded {data_length:,} "
                    f"but it reports {rows_loaded:,} rows loaded"
                )
            return data_length
