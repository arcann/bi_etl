# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import logging
import textwrap
import time
from pathlib import Path
from typing import *

import sqlalchemy
from sqlalchemy import text

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.bulk_loader_exception import BulkLoaderException
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.bulk_loaders.s3_bulk_loader_mixin import S3BulkLoaderMixin
from bi_etl.conversions import strip

if TYPE_CHECKING:
    from bi_etl.components.table import Table


class RedShiftS3Base(S3BulkLoaderMixin, BulkLoader):
    """
    Common base for Redshift bulk loaders that stage files on S3 and load them with ``COPY``.

    Subclasses must implement :meth:`get_copy_sql` to supply the format specific ``COPY`` options and
    :meth:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader.load_from_iterable` (typically by mixing in a format mixin).

    .. note::

       :class:`~bi_etl.bulk_loaders.s3_bulk_loader_mixin.S3BulkLoaderMixin` is listed before
       :class:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader` so that its file upload hooks replace the no-op versions.
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
        super().__init__()
        self.config = config
        self._init_s3(config)
        self.s3_user_id = self.config.user_id
        self.s3_region = self.config.region_name
        self.s3_file_max_rows = self.config.s3_file_max_rows
        self.analyze_compression = self.config.analyze_compression
        self.redshift_copy_iam_role = self.config.redshift_copy_iam_role
        try:
            identity = self.session.client('sts').get_caller_identity()
            self.log.info(f'Account ID = {identity["Account"]}')
            self.log.info(f'Account ARN = {identity["Arn"]}')
            self.log.info(f"Canonical  user = {self.session.client('s3').list_buckets()['Owner']}")
        except Exception as e:
            self.log.warning(e)

        self.non_recoverable_error_matches = [
            'The S3 bucket addressed by the query is in a different region from this cluster.',
            'Access denied',
            'The AWS Access Key Id you provided does not exist in our records.'
        ]
        self.lines_scanned_modifier = 0

    @property
    def s3_password(self):
        """
        The S3 password from the config. It is registered for redaction in log messages.
        """
        password = self.config.get_password()
        self.add_redact_value(password)
        return password

    def _post_upload_verify(self, s3_path: str):
        """Wait for uploaded file to be available in S3 (eventual consistency)."""
        response = None
        t_end = time.time() + 60 * 3
        while response is None:
            key = s3_path
            objs = list(self.bucket.objects.filter(Prefix=key))
            if len(objs) > 0 and objs[0].key == key:
                # self.log.info(f'{key} exists. {t_end}')
                response = True
            else:
                if time.time() > t_end:
                    raise RuntimeError(f'{key} is not available for loading. 3 minute wait is over. FATAL. {t_end}')
                else:
                    self.log.info(
                        f'{key} is probably not finished syncing among AWS S3 nodes, we will retry again after 5 second. {time.time()}'
                        )
                    time.sleep(5)
                    response = self.bucket.Object(s3_path).get()

    def _get_error_details(
            self,
            connection: sqlalchemy.engine.base.Connection | None,
            exception: sqlalchemy.exc.SQLAlchemyError,
            s3_source_path: str,
    ) -> BulkLoaderException:
        """
        Collect the details of a failed ``COPY`` from Redshift's ``stl_load_errors`` table and log them.

        Parameters
        ----------
        connection:
            Connection that ran the ``COPY``. ``None`` if the failure happened while connecting.
        exception:
            The error raised by the ``COPY``.
        s3_source_path:
            S3 path used by the ``COPY``. Used to find the error rows when ``pg_last_copy_id()`` is not available.

        Returns
        -------
        :class:`~bi_etl.bulk_loaders.bulk_loader_exception.BulkLoaderException`
            Exception holding the original error and any ``stl_load_errors`` details found.
        """
        bulk_loader_exception = BulkLoaderException(exception, password=self.s3_password)

        # early exit for cases where we failed while making a connection
        if connection is None:
            return bulk_loader_exception

        self.log.debug(f'Getting pg_last_copy_id')

        pg_last_copy_id_res = connection.execute(text("select pg_last_copy_id() as id"))
        pg_last_copy_id_row = next(pg_last_copy_id_res)
        pg_last_copy_id = pg_last_copy_id_row.id

        self.log.error(f'pg_last_copy_id = {pg_last_copy_id}')

        if pg_last_copy_id != -1:
            sql = """
                  SELECT *
                  FROM stl_load_errors
                  WHERE query = PG_LAST_COPY_ID()
                  ORDER BY
                      starttime DESC
                  """
        else:
            self.log.error(f"Unable to use pg_last_copy_id().  Seems to only work on successful COPY.")
            sql = f"""
                    SELECT TOP 1 *
                    FROM stl_load_errors
                    WHERE filename like '%{s3_source_path}%'
                    ORDER BY starttime DESC
                   """

        self.log.error(f'Checking stl_load_errors with\n{sql}')
        try:
            results = connection.execute(text(sql))
        except Exception as e2:
            bulk_loader_exception.add_error(f'Error {e2} when getting stl_load_errors contents')
            results = []
        rows_found = 0
        for row in results:
            rows_found += 1
            filename = strip(row.filename)
            column_name = strip(row.colname)
            c_type = strip(row.type)
            col_length = strip(row.col_length)
            err_reason = str(row.err_reason).strip()
            self.log.error(
                f'!!!! stl_load_errors row: {rows_found} !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
                )
            self.log.error(f'{filename} had an error')
            self.log.error(f'stl_load_errors.err_reason={err_reason}')
            self.log.error(f'stl_load_errors.err_code={row.err_code}')
            self.log.error(f'stl_load_errors.error with column = {column_name} {c_type} {col_length}')
            self.log.error(f'stl_load_errors.raw_field_value = "{str(row.raw_field_value).strip()}"')
            self.log.error(f'stl_load_errors.line number = {row.line_number}')
            self.log.error(f'stl_load_errors.character pos = {row.position}')
            self.log.error(f'stl_load_errors.raw_line={row.raw_line}')
            self.log.error('-' * 80)
            bulk_loader_exception.add_error(f'{column_name} {err_reason}')
        if rows_found == 0:
            bulk_loader_exception.add_error('No records found in stl_load_errors matching file list')
        self.log.error(f'{rows_found} rows found in stl_load_errors for file list')

        return bulk_loader_exception

    def _run_copy_sql(
            self,
            copy_sql: str,
            table_object: Table,
            s3_source_path: str,
    ) -> int:
        """
        Execute a ``COPY`` statement, retrying for up to 15 seconds on recoverable S3 errors.

        Parameters
        ----------
        copy_sql:
            The ``COPY`` statement to run.
        table_object:
            Table being loaded. Provides the database connection.
        s3_source_path:
            S3 path being loaded. Used when reporting errors.

        Returns
        -------
        int
            Number of rows loaded according to ``stl_load_commits``, or -1 if the count could not be determined.

        Raises
        ------
        :class:`~bi_etl.bulk_loaders.bulk_loader_exception.BulkLoaderException`
            If the ``COPY`` fails and cannot be retried.
        """
        copy_sql = textwrap.dedent(copy_sql)

        keep_trying = True
        wait_seconds = 15
        t_end = time.time() + wait_seconds
        connection = None
        rows_loaded = None

        while keep_trying:

            try:
                connection = table_object.connection()
                connection.execute(text(copy_sql))
                # Load worked we can stop looping
                keep_trying = False
                connection.execute(text("COMMIT;"))
            except sqlalchemy.exc.SQLAlchemyError as e:
                if connection is not None:
                    try:
                        connection.close()
                    except Exception as e:
                        pass
                # Check if the error is non-recoverable
                self.log_with_redactions(
                    log_level=logging.INFO,
                    message=copy_sql,
                )
                self.log.error('!' * 80)
                self.log_with_redactions(
                    log_level=logging.ERROR,
                    message=f'!! Details for {e} below:'
                )
                self.log.error('!' * 80)

                bulk_loader_exception = self._get_error_details(
                    connection=connection,
                    exception=e,
                    s3_source_path=s3_source_path,
                )

                if 'S3ServiceException' in str(e):
                    if any(error in str(e) for error in self.non_recoverable_error_matches):
                        self.log_with_redactions(
                            log_level=logging.ERROR,
                            message=f"Cannot recover from this error - {e}"
                        )
                        keep_trying = False
                    elif time.time() > t_end:
                        self.log.info(
                            f'{wait_seconds} seconds recovery wait time exceeded. File cannot be loaded. {t_end}'
                        )
                        keep_trying = False

                    if keep_trying:
                        self.log_with_redactions(
                            log_level=logging.ERROR,
                            message=f'Will retry in 5 seconds file copy after S3ServiceException failure - {e}'
                        )
                        time.sleep(5)
                    else:
                        raise bulk_loader_exception from None
                else:
                    raise bulk_loader_exception from None

        if connection is not None:
            sql = f"""
            SELECT SUM(lines_scanned) AS lines_scanned, COUNT(DISTINCT filename) AS file_cnt
            FROM stl_load_commits
            WHERE query = PG_LAST_COPY_ID()
            """
            # Default to -1 rows to indicate error
            rows_loaded = -1
            try:
                results = connection.execute(text(sql))
                for row in results:
                    lines_scanned = row.lines_scanned
                    file_cnt = row.file_cnt
                    if self.lines_scanned_modifier == 0:
                        rows_loaded = lines_scanned
                    else:
                        rows_loaded = lines_scanned + (self.lines_scanned_modifier * file_cnt)
            except Exception as e:
                self.log_with_redactions(
                    log_level=logging.WARNING,
                    message=f"Error getting row count: {e}"
                )
            connection.close()

        return rows_loaded

    def _get_region_specifier(self) -> str:
        """
        Called by _get_base_copy to get the region specifier in the COPY statement.
        Some sub-classes will need to override (e.g. PARQUET)
        """
        if self.s3_region is not None:
            return f"region '{self.s3_region}'"
        else:
            return '--No region'

    def _get_base_copy(
            self,
            s3_source_path: str,
            table_to_load: str,
    ):
        """
        Build the format independent start of the ``COPY`` statement.

        Includes the source, credentials, IAM role and region clauses.

        Parameters
        ----------
        s3_source_path:
            Path of the S3 folder (within the bucket) to load from.
        table_to_load:
            Qualified name of the table to load.

        Returns
        -------
        str
            The first part of the ``COPY`` statement.
        """
        region_option = self._get_region_specifier()

        if self.redshift_copy_iam_role is not None:
            role_option = f"IAM_ROLE '{self.redshift_copy_iam_role}'"
        else:
            role_option = '--No role'

        if self.s3_user_id is not None:
            credentials_option = f"CREDENTIALS 'aws_access_key_id={self.s3_user_id};aws_secret_access_key={self.s3_password}'"
        else:
            credentials_option = '--No credentials'

        return textwrap.dedent(
            f"""\
            COPY {table_to_load} 
                 FROM 's3://{self.s3_bucket_name}/{s3_source_path}'
                 {credentials_option}
                 {role_option}
                 {region_option}
            """
            )

    def _get_compression_option_str(
            self,
            analyze_compression: str | None = None,
    ) -> str:
        """
        Build the ``COMPUPDATE`` clause of the ``COPY`` statement.

        Parameters
        ----------
        analyze_compression:
            ``COMPUPDATE`` setting. Defaults to the configured ``analyze_compression``.

        Returns
        -------
        str
            The clause, or a SQL comment if compression analysis is not requested.
        """
        analyze_compression = analyze_compression or self.analyze_compression
        if analyze_compression:
            return f"COMPUPDATE {analyze_compression}"
        else:
            return '--No COMPUPDATE'

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str = None,
            options: str = '',
    ):
        """
        Build the format specific ``COPY`` statement. Must be implemented by each subclass.

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
        raise NotImplementedError()

    def load_from_s3_path(
            self,
            s3_source_path: str,
            table_object: Table,
            table_to_load: str = None,
            s3_source_path_is_absolute: bool = True,
            file_list: Optional[List[str]] = None,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str = None,
            perform_rename: bool = False,
    ) -> int:
        """
        Load files that are already in S3 into the table with ``COPY``.

        Parameters
        ----------
        s3_source_path:
            S3 folder (or file prefix) to load from.
        table_object:
            Table being loaded.
        table_to_load:
            Name of the table (or temp table) to load into. Defaults to ``table_object.qualified_table_name``.
        s3_source_path_is_absolute:
            If ``False``, ``s3_source_path`` is relative to the configured S3 folder.
        file_list:
            Names of the files being loaded. Not used by the ``COPY`` itself.
        file_compression:
            Compression option text to add to the statement (e.g. ``GZIP``).
        options:
            Additional ``COPY`` options to append.
        analyze_compression:
            ``COMPUPDATE`` setting. Defaults to the configured ``analyze_compression``.
        perform_rename:
            If ``True``, rename ``table_to_load`` over the original table after the load.

        Returns
        -------
        int
            Number of rows loaded.
        """
        if not s3_source_path_is_absolute:
            s3_source_path = f'{self.s3_folder}/{s3_source_path}'

        table_to_load = table_to_load or table_object.qualified_table_name

        copy_sql = self.get_copy_sql(
            s3_source_path=s3_source_path,
            table_to_load=table_to_load,
            file_compression=file_compression,
            analyze_compression=analyze_compression,
            options=options,
        )
        rows_loaded = self._run_copy_sql(
            copy_sql=copy_sql,
            table_object=table_object,
            s3_source_path=s3_source_path,
        )
        if perform_rename:
            self.rename_table(table_to_load, table_object)
        return rows_loaded

    def load_from_files(
            self,
            local_files: List[Union[str, Path]],
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str = None,
    ) -> int:
        """
        Wait for the uploads of *local_files* to S3 (uploading any that were not queued) and ``COPY`` them
        into the table.

        See :meth:`~bi_etl.bulk_loaders.s3_bulk_loader_mixin.S3BulkLoaderMixin._upload_files_to_s3`.

        Parameters
        ----------
        local_files:
            Local files to load.
        table_object:
            Table being loaded.
        table_to_load:
            Name of the table (or temp table) to load into. Defaults to ``table_object.qualified_table_name``.
        perform_rename:
            If ``True``, rename ``table_to_load`` over the original table after the load.
        file_compression:
            Compression option text to add to the statement (e.g. ``GZIP``).
        options:
            Additional ``COPY`` options to append.
        analyze_compression:
            ``COMPUPDATE`` setting. Defaults to the configured ``analyze_compression``.

        Returns
        -------
        int
            Number of rows loaded.
        """
        try:
            s3_full_folder, file_list = self._upload_files_to_s3(local_files, table_object)

            rows_loaded = self.load_from_s3_path(
                s3_source_path=s3_full_folder,
                file_list=file_list,
                table_object=table_object,
                table_to_load=table_to_load,
                perform_rename=perform_rename,
                file_compression=file_compression,
                options=options,
                analyze_compression=analyze_compression,
            )
        except BaseException:
            self._handle_load_failure()
            raise
        if self.s3_clear_when_done:
            self.clean_s3_folder(s3_full_folder)

        return rows_loaded

    def load_table_from_cache(
            self,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str | None = None,
    ) -> int:
        """
        Load the rows in the cache of *table_object* with :meth:`load_from_iterable`.

        Parameters
        ----------
        table_object:
            Table whose cache is loaded.
        table_to_load:
            Name of the table (or temp table) used when renaming.
        perform_rename:
            If ``True``, rename ``table_to_load`` over the original table (keeping the original as ``_old``).
        progress_frequency:
            Seconds between progress log messages.
        analyze_compression:
            ``COMPUPDATE`` setting. Defaults to the configured ``analyze_compression``.

        Returns
        -------
        int
            Number of rows loaded.
        """
        row_count = self.load_from_iterable(
            iterable=table_object.cache_iterable(),
            table_object=table_object,
            table_to_load=table_to_load,
            analyze_compression=analyze_compression,
        )
        if perform_rename:
            old_name = table_object.qualified_table_name + '_old'
            table_object.execute(f'DROP TABLE IF EXISTS {old_name} CASCADE')
            table_object.execute(f'ALTER TABLE {table_object.qualified_table_name} RENAME TO {old_name}')
            table_object.execute(f'ALTER TABLE {table_to_load} RENAME TO {table_object.qualified_table_name}')
        return row_count
