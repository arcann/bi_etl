# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os.path
import textwrap
import time
from pathlib import Path
from typing import *

import boto3
import sqlalchemy

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.bulk_loader_exception import BulkLoaderException
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
from bi_etl.conversions import strip
from bi_etl.utility import quote_delimited_list

if TYPE_CHECKING:
    from bi_etl.scheduler.task import ETLTask
    from bi_etl.components.table import Table


class RedShiftS3Base(BulkLoader):
    def __init__(self,
                 config: S3_Bulk_Loader_Config,
                 ):
        super().__init__(
        )
        self.config = config
        self.s3_user_id = self.config.user_id
        self.s3_region = self.config.region_name
        self.s3_bucket_name = self.config.bucket_name
        self.s3_folder = self.config.folder
        self.s3_files_to_generate = self.config.s3_files_to_generate
        self.s3_clear_before = self.config.s3_clear_before
        self.s3_clear_when_done = self.config.s3_clear_when_done
        self.analyze_compression = self.config.analyze_compression
        self.s3_password = self.config.get_password()
        self.session = boto3.session.Session(
            aws_access_key_id=self.s3_user_id,
            aws_secret_access_key=self.s3_password
        )
        try:
            identity = self.session.client('sts').get_caller_identity()
            self.log.info(f'Account ID = {identity["Account"]}')
            self.log.info(f'Account ARN = {identity["Arn"]}')
            self.log.info(f"Canonical  user = {self.session.client('s3').list_buckets()['Owner']}")
        except Exception as e:
            self.log.warning(e)
        self.s3 = self.session.resource('s3')
        self.bucket = self.s3.Bucket(self.s3_bucket_name)

    def s3_folder_contents(
            self,
            s3_full_folder,
    ):
        return [bucket_object for bucket_object in self.bucket.objects.filter(Prefix=s3_full_folder)]

    def clean_s3_folder(
            self,
            s3_full_folder,
    ):
        self.log.info(f'Cleaning S3 folder {s3_full_folder}')
        for bucket_object in self.bucket.objects.filter(Prefix=s3_full_folder):
            self.log.info(f'Removing {bucket_object}')
            bucket_object.delete()

    def _upload_files_to_s3(
            self,
            local_files: list,
            s3_full_folder: str,
    ):
        if self.s3_clear_before:
            self.clean_s3_folder(s3_full_folder)
        else:
            folder_contents = self.s3_folder_contents(s3_full_folder)
            if folder_contents:
                raise FileExistsError('The target S3 folder is not empty and s3_clear_before = False.'
                                      f'Existing contents = {folder_contents}')

        s3_files = list()
        # Upload the files
        for file_number, local_path in enumerate(local_files):
            s3_path = f'{s3_full_folder}/{os.path.basename(local_path)}'
            self.log.info(f"Uploading from '{local_path}' to {self.s3_bucket_name}' key '{s3_path}' ")
            s3_files.append(f's3://{self.s3_bucket_name}/{s3_path}')
            self.bucket.upload_file(
                str(local_path),
                str(s3_path),
            )

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
                        self.log.info(f'{key} is not available for loading. 3 minute wait is over. FATAL. {t_end}')
                        response = False
                    else:
                        self.log.info(f'{key} is probably not finished syncing among AWS S3 nodes, we will retry again after 5 second. {time.time()}')
                        time.sleep(5)
                        response = self.bucket.Object(s3_path).get()
        return s3_files

    def _run_copy_sql(
            self,
            copy_sql: str,
            s3_full_folder: str,
            table_object: Table,
            file_list: Optional[list] = None,
    ):
        copy_sql = textwrap.dedent(copy_sql)
        sql_safe_pw = copy_sql.replace(self.s3_password, '*' * 8)
        self.log.debug(sql_safe_pw)

        keep_trying = True
        wait_seconds = 15
        t_end = time.time() + wait_seconds
        while keep_trying:
            try:
                table_object.execute(copy_sql)
                keep_trying = False
            except sqlalchemy.exc.SQLAlchemyError as e:
                self.log.error('!' * 80)
                self.log.error(f'!! Details for {e} below:')
                self.log.error('!' * 80)

                bulk_loader_exception = BulkLoaderException(e, password=self.s3_password)

                if file_list is not None:
                    top_size = f'{len(file_list)}'
                    where = f"WHERE filename in ({quote_delimited_list(file_list)})"
                else:
                    top_size = "1"
                    where = ''
                sql = f"""
                    SELECT TOP {top_size} *
                    FROM stl_load_errors
                    {where}
                    ORDER BY starttime DESC
                    """
                self.log.error(f'Checking stl_load_errors with\n{sql}')
                try:
                    results = table_object.execute(sql)
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
                    self.log.error(f'!!!! stl_load_errors row: {rows_found} !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
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

                if 'S3ServiceException' in str(e):
                    if time.time() > t_end:
                        self.log.info(f'{wait_seconds} seconds wait is over. File cannot be loaded. {t_end}')
                        keep_trying = False
                    self.log.info(f'Will retry in 5 seconds file copy after S3ServiceException failure - {e}')
                    time.sleep(5)
                else:
                    raise bulk_loader_exception

        # TODO: Consider removing this commit the called should do that.
        #       However, requires extensive testing
        table_object.execute(f"COMMIT;")

    def get_copy_sql(
            self,
            s3_source_path: str,
            table_to_load: str,
            file_compression: str = '',
            analyze_compression: str = None,
            options: str = '',
    ):
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
    ):
        tries = 0
        done = False

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

        while not done:
            try:
                self._run_copy_sql(
                    copy_sql=copy_sql,
                    s3_full_folder=s3_source_path,
                    table_object=table_object,
                    file_list=file_list,
                )
                if perform_rename:
                    self.rename_table(table_to_load, table_object)
                done = True
            except sqlalchemy.exc.SQLAlchemyError as e:
                tries += 1
                if 'S3ServiceException' in str(e):
                    if tries >= 3:
                        self.log.info(f'Still failed after {tries} tries. File cannot be loaded.')
                        raise
                    self.log.info(f'Re-upload files to S3 to resolve {e} in 5 seconds')
                    time.sleep(5)
                else:
                    raise

    def load_from_files(
            self,
            local_files: List[Union[str, Path]],
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str = None,
    ):
        s3_full_folder = self._get_table_specific_folder_name(self.s3_folder, table_object)
        file_list = self._upload_files_to_s3(local_files, s3_full_folder)

        self.load_from_s3_path(
            s3_source_path=s3_full_folder,
            file_list=file_list,
            table_object=table_object,
            table_to_load=table_to_load,
            perform_rename=perform_rename,
            file_compression=file_compression,
            options=options,
            analyze_compression=analyze_compression,
        )
        if self.s3_clear_when_done:
            self.clean_s3_folder(s3_full_folder)

    def load_from_iterator(
        self,
        iterator: Iterator,
        table_object: Table,
        table_to_load: str = None,
        perform_rename: bool = False,
        progress_frequency: int = 10,
        analyze_compression: bool = None,
        parent_task: Optional[ETLTask] = None,
    ):

        raise NotImplementedError()

    def load_table_from_cache(
            self,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str = None,
    ) -> int:
        row_count = self.load_from_iterator(
            iterator=table_object.cache_iterator(),
            table_object=table_object,
            analyze_compression=analyze_compression,
        )
        if perform_rename:
            old_name = table_object.qualified_table_name + '_old'
            table_object.execute(f'DROP TABLE IF EXISTS {old_name} CASCADE')
            table_object.execute(f'ALTER TABLE {table_object.qualified_table_name} RENAME TO {old_name}')
            table_object.execute(f'ALTER TABLE {table_to_load} RENAME TO {table_object.qualified_table_name}')
        return row_count
