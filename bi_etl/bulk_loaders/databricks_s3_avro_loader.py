from typing import *

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.databricks_s3_base import DatabricksS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config

if TYPE_CHECKING:
    pass
else:
    Table = None


class DatabricksS3AvroBulkLoader(AvroBulkLoaderMixin, DatabricksS3Base):
    """
    Bulk loader for Databricks using Avro files staged to S3 and COPY INTO.

    Note: s3_file_max_rows is used as the Avro rows_per_file, if provided.
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
    ):
        """Initialise the Avro loader.

        Parameters
        ----------
        config
            :class:`~bi_etl.bulk_loaders.s3_bulk_load_config.S3_Bulk_Loader_Config`
            with the S3 bucket, folder and ``s3_file_max_rows`` settings.
        """
        super().__init__(config=config)

        self._init_avro()

    @property
    def needs_all_columns(self):
        """Avro files are loaded ``BY NAME``, so a subset of the table columns is allowed.

        Returns
        -------
        bool
            Always ``False``.
        """
        return False

    # --- COPY INTO SQL -----------------------------------------------------

    def _get_copy_into_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
    ) -> str:
        """Build the ``INSERT INTO ... FROM read_files(...)`` statement for Avro files.

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
            "FROM read_files("
            f"  's3://{self.s3_bucket_name}/{s3_source_path}',\n"
            "  format => 'avro',\n"
            "  schemaEvolutionMode => 'none'\n"
            ")"
        )
        # Note: EvolutionMode => 'none' prevents the extra column for recovered data which can create conflicts mapping to the table
    # load_from_files is inherited from DatabricksS3Base
