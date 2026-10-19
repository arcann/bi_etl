# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import textwrap

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class RedShiftS3AvroBulk(AvroBulkLoaderMixin, RedShiftS3Base):
    def __init__(
        self,
        config: S3_Bulk_Loader_Config,
    ):
        super().__init__(
            config=config,
        )
        if self.s3_file_max_rows is None:
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
            analyze_compression: str | None = None,
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
