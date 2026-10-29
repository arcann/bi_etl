# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

from bi_etl.bulk_loaders.databricks_s3_base import DatabricksS3Base
from bi_etl.bulk_loaders.parquet_bulk_loader_mixin import ParquetBulkLoaderMixin
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class DatabricksS3ParquetBulkLoader(ParquetBulkLoaderMixin, DatabricksS3Base):
    """Bulk loader for Databricks using Parquet files staged to S3.

    Rows are written to local Snappy compressed Parquet files, uploaded to S3 by a background thread as each
    file is completed, and ingested via ``INSERT INTO ... BY NAME FROM read_files(...)`` with
    ``format => 'parquet'``.

    Note: ``s3_file_max_rows`` from the config is used as the number of rows per Parquet file.
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
    ):
        """Initialise the Parquet loader.

        Parameters
        ----------
        config
            :class:`~bi_etl.bulk_loaders.s3_bulk_load_config.S3_Bulk_Loader_Config` with the S3 bucket, folder
            and ``s3_file_max_rows`` settings.
        """
        super().__init__(config=config)

        self._init_parquet()

    @property
    def needs_all_columns(self):
        """Parquet files are loaded ``BY NAME``, so a subset of the table columns is allowed.

        Returns
        -------
        bool
            Always ``False``.
        """
        return False

    def _get_copy_into_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
    ) -> str:
        """Build the ``INSERT INTO ... FROM read_files(...)`` statement for Parquet files.

        Parameters
        ----------
        s3_source_path
            Folder within the bucket that holds the uploaded files.
        table_to_load
            Qualified name of the table to insert into.

        Returns
        -------
        str
            SQL statement to execute, see :meth:`DatabricksS3Base._get_copy_into_sql`.
        """
        # Credentials are optional: the Databricks cluster's instance profile
        # or Unity Catalog storage credential typically handles S3 access.
        return (
            f"INSERT INTO {table_to_load} BY NAME\n"
            "FROM read_files(\n"
            f"  's3://{self.s3_bucket_name}/{s3_source_path}',\n"
            "  format => 'parquet',\n"
            "  schemaEvolutionMode => 'none'\n"
            ")"
        )