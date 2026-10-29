# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

from typing import Optional, Sequence

from bi_etl.bulk_loaders.csv_bulk_loader_mixin import CsvBulkLoaderMixin
from bi_etl.bulk_loaders.databricks_s3_base import DatabricksInsertMode, DatabricksS3Base
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class DatabricksS3CsvBulkLoader(CsvBulkLoaderMixin, DatabricksS3Base):
    """Bulk loader for Databricks using gzipped CSV files staged to S3.

    Rows are written to local gzipped CSV files, uploaded to S3, and ingested
    via ``INSERT INTO ... SELECT * FROM read_files(...)`` with ``format => 'csv'``.

    The write mode can be changed with ``insert_mode`` to ``INSERT OVERWRITE`` or one of the
    ``INSERT INTO ... REPLACE {USING | ON | WHERE}`` selective overwrite forms.

    By default ``by_name`` follows *has_header*: with a header the ``BY NAME`` clause is
    used so column order does not need to match the target table.  Without a header,
    columns must appear in table order and :attr:`needs_all_columns` returns ``True``.

    Note: ``s3_file_max_rows`` from the config is used as the CSV file_max_rows, if provided.
    """

    def __init__(
            self,
            config: S3_Bulk_Loader_Config,
            has_header: bool = True,
            delimiter: str = '|',
            null_value: str = '',
            insert_mode: DatabricksInsertMode = DatabricksInsertMode.APPEND,
            by_name: Optional[bool] = None,
            schema_evolution: bool = False,
            replace_using_columns: Optional[Sequence[str]] = None,
            replace_on_condition: Optional[str] = None,
            replace_where_condition: Optional[str] = None,
            target_alias: str = 't',
            source_alias: str = 's',
    ):
        """Initialise the CSV loader.

        Parameters
        ----------
        config
            :class:`~bi_etl.bulk_loaders.s3_bulk_load_config.S3_Bulk_Loader_Config` with the S3 bucket, folder
            and ``s3_file_max_rows`` settings.
        has_header
            Whether to write (and read) a header line in each file.
        delimiter
            Field delimiter used in the files.
        null_value
            Text that represents a null value in the files.
        insert_mode
            Write mode for the generated ``INSERT`` statement. Defaults to
            :attr:`DatabricksInsertMode.APPEND`.
        by_name
            Use ``BY NAME`` for the generated ``INSERT`` statement. Defaults to ``None``,
            which means the value of *has_header*. Cannot be ``True`` when *has_header* is ``False``.
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
            If ``by_name`` is ``True`` without a header, ``insert_mode`` is not a
            :class:`DatabricksInsertMode`, or the parameter required by the selected mode is missing or empty.
        """
        if by_name is None:
            by_name = has_header
        elif by_name and not has_header:
            raise ValueError("by_name=True requires has_header=True for CSV files")

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

        self._init_csv(
            has_header=has_header,
            delimiter=delimiter,
            null_value=null_value,
        )

    # needs_all_columns is inherited from DatabricksS3Base

    # --- COPY INTO SQL -------------------------------------------------------

    def _get_copy_into_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
    ) -> str:
        """Build the ``INSERT ... SELECT * FROM read_files(...)`` statement for CSV files.

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
            file_format='csv',
            format_options={
                'header': 'true' if self.has_header else 'false',
                'delimiter': self.csv_delimiter,
                'nullValue': self.null_value,
            },
        )
