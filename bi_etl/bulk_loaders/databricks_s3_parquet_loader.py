# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

from typing import Optional, Sequence

# DatabricksInsertMode is re-exported here for backwards compatibility.
from bi_etl.bulk_loaders.databricks_s3_base import DatabricksInsertMode, DatabricksS3Base
from bi_etl.bulk_loaders.parquet_bulk_loader_mixin import ParquetBulkLoaderMixin
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


__all__ = ['DatabricksInsertMode', 'DatabricksS3ParquetBulkLoader']


class DatabricksS3ParquetBulkLoader(ParquetBulkLoaderMixin, DatabricksS3Base):
    """Bulk loader for Databricks using Parquet files staged to S3.

    Rows are written to local Snappy compressed Parquet files, uploaded to S3 by a background thread as each
    file is completed, and ingested via ``INSERT INTO ... BY NAME FROM read_files(...)`` with
    ``format => 'parquet'``.

    The write mode can be changed with ``insert_mode`` to ``INSERT OVERWRITE`` or one of the
    ``INSERT INTO ... REPLACE {USING | ON | WHERE}`` selective overwrite forms.

    Note: ``s3_file_max_rows`` from the config is used as the number of rows per Parquet file.
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
            insert_mode: DatabricksInsertMode = DatabricksInsertMode.APPEND,
            by_name: bool = True,
            schema_evolution: bool = False,
            replace_using_columns: Optional[Sequence[str]] = None,
            replace_on_condition: Optional[str] = None,
            replace_where_condition: Optional[str] = None,
            target_alias: str = 't',
            source_alias: str = 's',
    ):
        """Initialise the Parquet loader.

        Parameters
        ----------
        config
            :class:`~bi_etl.bulk_loaders.s3_bulk_load_config.S3_Bulk_Loader_Config` with the S3 bucket, folder
            and ``s3_file_max_rows`` settings.
        insert_mode
            Write mode for the generated ``INSERT`` statement. Defaults to
            :attr:`DatabricksInsertMode.APPEND`.
        by_name
            Use ``BY NAME`` for the generated ``INSERT`` statement. Defaults to ``True``.
        schema_evolution
            Use ``WITH SCHEMA EVOLUTION`` for the generated ``INSERT`` statement. Defaults to ``False``.
        replace_using_columns
            Column names to match on. Required when ``insert_mode`` is
            :attr:`DatabricksInsertMode.REPLACE_USING`; ignored otherwise.
        replace_on_condition
            Boolean SQL expression referencing ``target_alias`` and ``source_alias``
            (for example ``"t.id <=> s.id"``). Required when ``insert_mode`` is
            :attr:`DatabricksInsertMode.REPLACE_ON`; ignored otherwise.
        replace_where_condition
            Boolean SQL predicate on the target table columns (for example
            ``"load_date = '2024-01-01'"``). Required when ``insert_mode`` is
            :attr:`DatabricksInsertMode.REPLACE_WHERE`; ignored otherwise.
        target_alias
            Alias for the target table used by ``REPLACE ON``. Defaults to ``'t'``.
        source_alias
            Alias for the source query used by ``REPLACE ON``. Defaults to ``'s'``.

        Raises
        ------
        ValueError
            If ``insert_mode`` is not a :class:`DatabricksInsertMode` or the parameter
            required by the selected mode is missing or empty.
        """
        super().__init__(
            config=config,
            insert_mode=insert_mode,
            by_name=by_name,
            schema_evolution=schema_evolution,
            replace_using_columns=replace_using_columns,
            replace_on_condition=replace_on_condition,
            replace_where_condition=replace_where_condition,
            target_alias=target_alias,
            source_alias=source_alias,
        )

        self._init_parquet()

    def _get_copy_into_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
    ) -> str:
        """Build the ``INSERT ... SELECT * FROM read_files(...)`` statement for Parquet files.

        See :meth:`DatabricksS3Base._build_insert_sql` for the statement forms used by each
        :class:`DatabricksInsertMode`.

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
        return self._build_insert_sql(
            s3_source_path=s3_source_path,
            table_to_load=table_to_load,
            file_format='parquet',
        )
