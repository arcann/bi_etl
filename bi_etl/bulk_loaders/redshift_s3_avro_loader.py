# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import textwrap

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.redshift_s3_base import RedShiftS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class RedShiftS3AvroBulk(AvroBulkLoaderMixin, RedShiftS3Base):
    """
    Bulk loader for Redshift using Avro files staged to S3 and ``COPY ... AVRO 'auto'``.

    Note: ``s3_file_max_rows`` is used as the Avro chunk size (default 50,000 rows per file).
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
        if self.s3_file_max_rows is None:
            self.s3_file_max_rows = 50000

        # Redshift appears to count the schema as a line read
        self.lines_scanned_modifier = -1

        self._init_avro(chunk_size=self.s3_file_max_rows)

    @property
    def needs_all_columns(self):
        """
        Always ``False``. ``AVRO 'auto'`` maps fields to columns by name, so a subset of columns can be loaded.
        """
        return False

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str | None = None,
            options: str = '',
    ):
        """
        Build the Avro ``COPY`` statement.

        Parameters
        ----------
        s3_source_path:
            Path of the S3 folder (within the bucket) containing the files to load.
        table_to_load:
            Qualified name of the table to load.
        file_compression:
            Compression option text to add to the statement (e.g. ``GZIP``).
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
            {base_copy} --AVRO specific Options:
            AVRO 'auto'
            {file_compression}  
            {self._get_compression_option_str(analyze_compression)}
            {options}; commit;
            """
            )
