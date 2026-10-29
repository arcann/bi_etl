# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, List, Mapping, Optional, Sequence, Union

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.bulk_loaders.s3_bulk_loader_mixin import S3BulkLoaderMixin

if TYPE_CHECKING:
    from bi_etl.components.table import Table
else:
    Table = object


class DatabricksInsertMode(Enum):
    """Write mode used by the Databricks ``INSERT`` statement.

    Attributes
    ----------
    APPEND
        ``INSERT INTO`` -- append rows to the table (default).
    OVERWRITE
        ``INSERT OVERWRITE`` -- truncate the table and replace all rows.
    REPLACE_USING
        ``INSERT INTO ... REPLACE USING (cols)`` -- delete table rows whose key columns equal those of an
        incoming row, then insert the incoming rows. Requires Databricks Runtime 17.2+ (18.1+ for ``BY NAME``).
    REPLACE_ON
        ``INSERT INTO ... REPLACE ON condition`` -- delete table rows matching an incoming row under a
        user-supplied condition referencing both the target and source aliases, then insert the incoming rows.
        Requires Databricks Runtime 17.1+ (18.1+ for ``BY NAME``).
    REPLACE_WHERE
        ``INSERT INTO ... REPLACE WHERE predicate`` -- delete table rows matching a predicate on the table,
        then insert the incoming rows (all of which must satisfy the predicate).
    """
    APPEND = 'append'
    OVERWRITE = 'overwrite'
    REPLACE_USING = 'replace_using'
    REPLACE_ON = 'replace_on'
    REPLACE_WHERE = 'replace_where'


class DatabricksS3Base(S3BulkLoaderMixin, BulkLoader):
    """Common base for Databricks bulk loaders that stage files on S3 and use
    ``INSERT ... SELECT * FROM read_files(...)`` to ingest them.

    The write mode can be changed with ``insert_mode`` to ``INSERT OVERWRITE`` or one of the
    ``INSERT INTO ... REPLACE {USING | ON | WHERE}`` selective overwrite forms.

    Subclasses must implement :meth:`_get_copy_into_sql` (typically by calling
    :meth:`_build_insert_sql` with the format-specific ``read_files`` options) and override
    :meth:`load_from_iterable` (typically by mixing in a format mixin
    such as :class:`AvroBulkLoaderMixin` or :class:`CsvBulkLoaderMixin`).
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
        """Initialise the Databricks S3 loader.

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
        super().__init__()
        self.config = config
        self._init_s3(config)
        if self.config.s3_file_max_rows is not None:
            self.rows_per_file = self.config.s3_file_max_rows

        if not isinstance(insert_mode, DatabricksInsertMode):
            raise ValueError(f"insert_mode must be a DatabricksInsertMode, got {insert_mode!r}")

        if insert_mode == DatabricksInsertMode.REPLACE_USING:
            if isinstance(replace_using_columns, str) or not replace_using_columns:
                raise ValueError(
                    "replace_using_columns must be a non-empty sequence of column names "
                    "when insert_mode is REPLACE_USING"
                )
        elif insert_mode == DatabricksInsertMode.REPLACE_ON:
            if not replace_on_condition:
                raise ValueError("replace_on_condition is required when insert_mode is REPLACE_ON")
            if not target_alias or not source_alias:
                raise ValueError("target_alias and source_alias are required when insert_mode is REPLACE_ON")
        elif insert_mode == DatabricksInsertMode.REPLACE_WHERE:
            if not replace_where_condition:
                raise ValueError("replace_where_condition is required when insert_mode is REPLACE_WHERE")

        self.insert_mode = insert_mode
        self.by_name = by_name
        self.schema_evolution = schema_evolution
        self.replace_using_columns = list(replace_using_columns) if replace_using_columns else None
        self.replace_on_condition = replace_on_condition
        self.replace_where_condition = replace_where_condition
        self.target_alias = target_alias
        self.source_alias = source_alias

    @property
    def needs_all_columns(self):
        """Whether rows must contain every table column.

        Returns
        -------
        bool
            ``False`` when loading ``BY NAME`` (a subset of the table columns is allowed),
            ``True`` when columns are matched by position.
        """
        return not self.by_name

    # --- SQL generation -------------------------------------------------------

    @staticmethod
    def _quote_identifier(name: str) -> str:
        """Quote a column name with backticks for Databricks SQL.

        Parameters
        ----------
        name
            Unquoted column name.

        Returns
        -------
        str
            Backtick quoted identifier with embedded backticks escaped.
        """
        escaped = name.replace('`', '``')
        return f"`{escaped}`"

    def _build_read_files_query(
            self,
            s3_source_path: str,
            file_format: str,
            format_options: Optional[Mapping[str, str]] = None,
    ) -> str:
        """Build the ``SELECT * FROM read_files(...)`` source query.

        Parameters
        ----------
        s3_source_path
            Folder within the bucket that holds the uploaded files.
        file_format
            Value for the ``format`` option (for example ``'parquet'``, ``'csv'`` or ``'avro'``).
        format_options
            Additional format-specific ``read_files`` options, rendered in order as
            ``key => 'value'``. Values are inserted as-is inside single quotes.

        Returns
        -------
        str
            The source query.
        """
        # Credentials are optional: the Databricks cluster's instance profile
        # or Unity Catalog storage credential typically handles S3 access.
        options = [
            f"  's3://{self.s3_bucket_name}/{s3_source_path}'",
            f"  format => '{file_format}'",
        ]
        for key, value in (format_options or {}).items():
            options.append(f"  {key} => '{value}'")
        # schemaEvolutionMode => 'none' prevents the extra column for recovered data
        # which can create conflicts mapping to the table.
        options.append("  schemaEvolutionMode => 'none'")
        return "SELECT * FROM read_files(\n" + ",\n".join(options) + "\n)"

    def _build_insert_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_format: str,
            format_options: Optional[Mapping[str, str]] = None,
    ) -> str:
        """Build the full ``INSERT ... SELECT * FROM read_files(...)`` statement.

        The statement form depends on :attr:`insert_mode`:

        * ``APPEND``: ``INSERT INTO tbl BY NAME SELECT ...``
        * ``OVERWRITE``: ``INSERT OVERWRITE tbl BY NAME SELECT ...``
        * ``REPLACE_USING``: ``INSERT INTO tbl BY NAME REPLACE USING (cols) SELECT ...``
        * ``REPLACE_ON``: ``INSERT INTO tbl AS t BY NAME REPLACE ON cond (SELECT ...) AS s``
        * ``REPLACE_WHERE``: ``INSERT INTO tbl BY NAME REPLACE WHERE pred SELECT ...``

        ``BY NAME`` is included when :attr:`by_name` is ``True`` and ``WITH SCHEMA EVOLUTION``
        is added after ``INSERT`` when :attr:`schema_evolution` is ``True``.

        Parameters
        ----------
        s3_source_path
            Folder within the bucket that holds the uploaded files.
        table_to_load
            Qualified name of the table to insert into.
        file_format
            Value for the ``read_files`` ``format`` option.
        format_options
            Additional format-specific ``read_files`` options, see :meth:`_build_read_files_query`.

        Returns
        -------
        str
            SQL statement to execute.

        Raises
        ------
        ValueError
            If :attr:`insert_mode` is not supported.
        """
        source_query = self._build_read_files_query(
            s3_source_path=s3_source_path,
            file_format=file_format,
            format_options=format_options,
        )

        mode = self.insert_mode
        insert_kw = 'INSERT WITH SCHEMA EVOLUTION' if self.schema_evolution else 'INSERT'
        write_kw = 'OVERWRITE' if mode == DatabricksInsertMode.OVERWRITE else 'INTO'
        by_name_sql = ' BY NAME' if self.by_name else ''
        target_alias_sql = f" AS {self.target_alias}" if mode == DatabricksInsertMode.REPLACE_ON else ''
        header = f"{insert_kw} {write_kw} {table_to_load}{target_alias_sql}{by_name_sql}"

        if mode in (DatabricksInsertMode.APPEND, DatabricksInsertMode.OVERWRITE):
            return f"{header}\n{source_query}"

        if mode == DatabricksInsertMode.REPLACE_USING:
            using_cols = ', '.join(self._quote_identifier(c) for c in self.replace_using_columns)
            return f"{header}\nREPLACE USING ({using_cols})\n{source_query}"

        if mode == DatabricksInsertMode.REPLACE_ON:
            return (
                f"{header}\n"
                f"REPLACE ON ({self.replace_on_condition})\n"
                f"({source_query}) AS {self.source_alias}"
            )

        if mode == DatabricksInsertMode.REPLACE_WHERE:
            return f"{header}\nREPLACE WHERE {self.replace_where_condition}\n{source_query}"

        raise ValueError(f"Unsupported insert_mode {mode!r}")

    def _get_copy_into_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
    ) -> str:
        """Return the SQL statement used to load data from S3 into the table.

        Must be implemented by each format-specific subclass, typically by calling
        :meth:`_build_insert_sql`.

        Parameters
        ----------
        s3_source_path
            Folder within the bucket that holds the uploaded files.
        table_to_load
            Qualified name of the table to insert into.

        Returns
        -------
        str
            SQL statement to execute.

        Raises
        ------
        NotImplementedError
            Always, in this base class.
        """
        raise NotImplementedError()

    # --- Load from files -----------------------------------------------------

    def load_from_files(
            self,
            local_files: List[Union[str, Path]],
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str | None = None,
    ) -> int:
        """Upload *local_files* to S3 and execute the format-specific SQL.

        This is the common Databricks load path:

        1. Wait for the background upload of the local files to the table-specific S3 folder
           (and upload any that were not queued).
        2. Build and execute the SQL returned by :meth:`_get_copy_into_sql`.
        3. Optionally clean the S3 folder and rename the table.

        Returns the number of rows inserted as reported by the database.
        """
        table_to_load = table_to_load or table_object.qualified_table_name

        try:
            s3_full_folder, _ = self._upload_files_to_s3(local_files, table_object)

            copy_sql = self._get_copy_into_sql(
                s3_source_path=s3_full_folder,
                table_to_load=table_to_load,
            )
            self.log_with_redactions(
                log_level=logging.INFO,
                message=copy_sql,
            )

            rows_inserted = 0
            conn = None
            try:
                conn = table_object.database.bind.raw_connection()
                cursor = conn.cursor()
                cursor.execute(copy_sql)
                for result_row in cursor.fetchall():
                    rows_inserted += result_row[1]
                conn.commit()
            except Exception as e:
                self.log.error(f"COPY INTO failed: {e}")
                raise
            finally:
                if conn is not None:
                    conn.close()
        except BaseException:
            self._handle_load_failure()
            raise

        if self.s3_clear_when_done:
            self.clean_s3_folder(s3_full_folder)

        if perform_rename:
            self.rename_table(table_to_load, table_object)

        return rows_inserted
