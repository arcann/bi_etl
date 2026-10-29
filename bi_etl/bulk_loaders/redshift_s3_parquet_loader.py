# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import textwrap

from bi_etl.bulk_loaders.parquet_bulk_loader_mixin import ParquetBulkLoaderMixin
from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class RedShiftS3ParquetBulk(ParquetBulkLoaderMixin, RedShiftS3Base):
    """
    Bulk loader for Redshift using Parquet files staged to S3 and ``COPY ... FORMAT PARQUET``.

    Note: ``s3_file_max_rows`` is used as the number of rows per Parquet file.
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
    ):
        """
        Parameters
        ----------
        config:
            :class:`~bi_etl.bulk_loaders.s3_bulk_load_config.S3_Bulk_Loader_Config`
            with the S3 and Redshift settings.
        """
        super().__init__(
            config=config,
        )

        self._init_parquet()
        self.lines_scanned_modifier = 0

    @property
    def needs_all_columns(self):
        """
        Always ``False``. Parquet columns are mapped to table columns by name.
        """
        return False

    def _get_region_specifier(self) -> str:
        """
        Called by _get_base_copy to get the region specifier in the COPY statement
        """
        if self.s3_region is not None:
            return '-- AWS does not support region for PARQUET'
        else:
            return '--No region (and not supported for PARQUET)'

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str = None,
            options: str = '',
    ):
        """
        Build the Parquet ``COPY`` statement.

        Parameters
        ----------
        s3_source_path:
            Path of the S3 folder (within the bucket) containing the files to load.
        table_to_load:
            Qualified name of the table to load.
        file_compression:
            Compression option text to add to the statement.
        analyze_compression:
            ``COMPUPDATE`` setting. Defaults to the configured ``analyze_compression``.
        options:
            Additional ``COPY`` options to append.

        Returns
        -------
        str
            The SQL text.
        """
        base_copy = self._get_base_copy(
            s3_source_path=s3_source_path,
            table_to_load=table_to_load,
        )

        return textwrap.dedent(
            f"""\
            {base_copy} --PARQUET specific Options:
            FORMAT PARQUET
            {file_compression}  
            {self._get_compression_option_str(analyze_compression)}
            {options}; commit;
            """
            )
