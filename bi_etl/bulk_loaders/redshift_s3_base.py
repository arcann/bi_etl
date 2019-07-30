# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations
import os.path
import textwrap
import typing

import boto3
import keyring
import sqlalchemy

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.conversions import strip

if typing.TYPE_CHECKING:
    from bi_etl.scheduler.task import ETLTask
    from bi_etl.components.table import Table


class RedShiftS3Base(BulkLoader):
    def __init__(self,
                 config: BIConfigParser,
                 s3_user_id: typing.Optional[str] = None,
                 s3_keyring_password_section: typing.Optional[str] = None,
                 s3_bucket_name: typing.Optional[str] = None,
                 s3_folder: typing.Optional[str] = None,
                 s3_files_to_generate: typing.Optional[int] = None,
                 ):
        super().__init__(
            config=config
        )
        self.s3_user_id = s3_user_id or self.config.get('s3_bulk', 'user_id')
        self.s3_keyring_password_section = s3_keyring_password_section or self.config.get('s3_bulk', 'keyring_password_section', fallback='s3')
        self.s3_bucket_name = s3_bucket_name or self.config.get('s3_bulk', 'bucket_name')
        self.s3_folder = s3_folder or self.config.get('s3_bulk', 's3_folder')
        self.s3_files_to_generate = s3_files_to_generate or self.config.getint('s3_bulk', 's3_files_to_generate')
        self.s3_clear_before = True
        self.s3_clear_when_done = True
        self.analyze_compression = None
        self.s3_password = keyring.get_password(self.s3_keyring_password_section, self.s3_user_id)
        assert self.s3_password is not None, f'Password for s3 {self.s3_keyring_password_section} {self.s3_user_id} not found in keyring'
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

        # Upload the files
        for file_number, local_path in enumerate(local_files):
            s3_path = f'{s3_full_folder}/{os.path.basename(local_path)}'
            self.log.info(f"Uploading from '{local_path}' to {self.s3_bucket_name}' key '{s3_path}' ")
            self.bucket.upload_file(
                local_path,
                s3_path,
            )

    def _run_copy_sql(
            self,
            copy_sql: str,
            s3_full_folder: str,
            table_object: Table,
    ):
        copy_sql = textwrap.dedent(copy_sql)
        sql_safe_pw = copy_sql.replace(self.s3_password, '*' * 8)
        self.log.debug(sql_safe_pw)

        try:
            table_object.execute(copy_sql)
        except sqlalchemy.exc.SQLAlchemyError as e:
            # noinspection PyBroadException
            try:
                results = table_object.execute(
                    """
                    SELECT TOP 1 *
                    FROM stl_load_errors
                    ORDER BY starttime DESC
                    """
                )
                for row in results:
                    self.log.error('!' * 80)
                    filename = strip(row.filename)
                    colname = strip(row.colname)
                    c_type = strip(row.type)
                    col_length = strip(row.col_length)
                    self.log.error(f'{filename} had an error at line {row.line_number} '
                                   f'with column {colname} {c_type} {col_length}'
                                   f'character pos {row.position}')
                    self.log.error(f'raw_field_value ={row.raw_field_value}')
                    self.log.error(f'err_reason and code={row.err_reason} {row.err_code}')
                    self.log.error(f'raw_line={row.raw_line}')
                    self.log.error('!' * 80)
            except Exception as e2:
                self.log.error(f'Error {e2} when getting stl_load_errors contents')
            # Ensure we don't leak the password
            if hasattr(e, 'statement'):
                e.statement = e.statement.replace(self.s3_password, '*' * 8)
            raise

        # Commit added to avoid VACUUM inside any transaction
        table_object.execute(f"COMMIT; VACUUM {table_object.qualified_table_name};")

        if self.s3_clear_when_done:
            self.clean_s3_folder(s3_full_folder)

    def load_from_files(
        self,
        local_files: list,
        table_object: Table,
        table_to_load: str = None,
        perform_rename: bool = False,
        file_compression: str = '',
        options: str = '',
        analyze_compression: str = None,
    ):
        raise NotImplementedError()

    def load_from_iterator(
        self,
        iterator: typing.Iterator,
        table_object: Table,
        table_to_load: str = None,
        perform_rename: bool = False,
        progress_frequency: int = 10,
        analyze_compression: str = None,
        parent_task: typing.Optional[ETLTask] = None,
    ):

        raise NotImplementedError()

    def load_table_from_cache(
            self,
            table_object: Table,
            table_to_load: str = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str = None,
    ):
        self.load_from_iterator(
            iterator=table_object.cache_iterator(),
            table_object=table_object,
            analyze_compression=analyze_compression,
        )
        if perform_rename:
            old_name = table_object.qualified_table_name + '_old'
            table_object.execute(f'DROP TABLE IF EXISTS {old_name} CASCADE')
            table_object.execute(f'ALTER TABLE {table_object.qualified_table_name} RENAME TO {old_name}')
            table_object.execute(f'ALTER TABLE {table_to_load} RENAME TO {table_object.qualified_table_name}')
