# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

from bi_etl.bulk_loaders.csv_bulk_loader_mixin import CsvBulkLoaderMixin
from bi_etl.bulk_loaders.databricks_s3_base import DatabricksS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class DatabricksS3CsvBulkLoader(CsvBulkLoaderMixin, DatabricksS3Base):
    """Bulk loader for Databricks using gzipped CSV files staged to S3.

    Rows are written to local gzipped CSV files, uploaded to S3, and ingested
    via ``INSERT INTO ... FROM read_files(...)`` with ``format => 'csv'``.

    When *has_header* is ``True`` (the default), the ``BY NAME`` clause is
    used so column order does not need to match the target table.  When
    ``False``, columns must appear in table order and :attr:`needs_all_columns`
    returns ``True``.

    Note: ``s3_file_max_rows`` from the config is used as the CSV chunk size.
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
            has_header: bool = True,
            delimiter: str = '|',
            null_value: str = '',
    ):
        super().__init__(config=config)

        chunk_size = self.s3_file_max_rows if self.s3_file_max_rows is not None else 25000
        self.s3_file_max_rows = chunk_size  # normalise for consistency

        self._init_csv(
            chunk_size=chunk_size,
            has_header=has_header,
            delimiter=delimiter,
            null_value=null_value,
        )

    @property
    def needs_all_columns(self):
        # With headers, BY NAME mapping allows a subset of columns.
        # Without headers, all columns must be present in table order.
        return not self.has_header

    # --- COPY INTO SQL -------------------------------------------------------

    def _get_copy_into_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
    ) -> str:
        header_opt = 'true' if self.has_header else 'false'
        by_name = ' BY NAME' if self.has_header else ''
        return (
            f"INSERT INTO {table_to_load}{by_name}\n"
            "FROM read_files(\n"
            f"  's3://{self.s3_bucket_name}/{s3_source_path}',\n"
            "  format => 'csv',\n"
            f"  header => '{header_opt}',\n"
            f"  delimiter => '{self.csv_delimiter}',\n"
            f"  nullValue => '{self.null_value}',\n"
            "  schemaEvolutionMode => 'none'\n"
            ")"
        )
