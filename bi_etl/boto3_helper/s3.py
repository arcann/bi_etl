"""
Created on March 28, 2022

@author: 
"""
import logging
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import *

import botocore
from botocore.exceptions import ClientError
from config_wrangler.config_templates.aws.s3_bucket import S3_Bucket

from bi_etl.database import DatabaseMetadata


# noinspection PyPep8Naming
class File_Entry(object):
    def __init__(
            self,
            content_path: str,
            full_local_path: str,
            source_path: str = None,
            s3_last_modified: datetime = None,
            s3_file_size: int = None,
            bucket_object=None,
            local_last_modified: datetime = None,
            local_file_size: int = None,
    ):
        self.content_path = content_path
        self.full_local_path = full_local_path
        self.source_path = source_path
        self.s3_last_modified = s3_last_modified
        self.s3_file_size = s3_file_size
        self.bucket_object = bucket_object
        self.local_last_modified = local_last_modified
        self.local_file_size = local_file_size

    def __str__(self):
        return self.content_path

    def __repr__(self):
        return f'{self.content_path} ({self.s3_file_size:,} {self.s3_last_modified})'

    def full_path(self, base_path):
        return os.path.join(base_path, self.content_path)

    def basename(self):
        return os.path.basename(self.content_path)


class FileFormat(Enum):
    parquet = 'P'
    csv = 'C'


class Boto3_S3(S3_Bucket):

    def download_file_from_s3(
            self,
            file_key: str,
            local_file_path: str,
            date_placeholder: str = None,
            date_pattern: str = '%Y-%m-%d',
    ) -> str:
        log = logging.getLogger(__name__)

        if date_placeholder:
            # Get the timestamp of the file
            s3_object = self.client.get_object(Bucket=self.bucket_name, Key=file_key)

            file_date = s3_object['LastModified']
            log.info(f"{file_key} timestamp: {file_date}")
            file_date_str = file_date.strftime(date_pattern)

            local_file_path = local_file_path.format(**{date_placeholder: file_date_str})

        done = False
        tries = 0
        while not done:
            try:
                # Download the file
                self.resource.Bucket(self.bucket_name).download_file(
                    str(file_key),
                    str(local_file_path)
                )

                return local_file_path

            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    log.error(f"The object does not exist. {self}/{file_key}")
                    raise e
                else:
                    log.error(f"Error downloading {self}/{file_key} was {e}")
                    raise e
            except OSError as e:
                if '.' in local_file_path and tries < 3:
                    local_file_path = local_file_path.replace('.', '_.')
                    log.warning(f"Got error {e} will try again with name '{local_file_path}'")
                    tries += 1
                else:
                    raise

    def scan_files_from_s3(
            self,
            key_prefixes: List[str],
            local_folder: Optional[str] = None,
    ) -> List[File_Entry]:
        log = logging.getLogger(__name__)

        file_list = list()
        local_timezone = datetime.now(timezone.utc).astimezone().tzinfo

        try:
            bucket = self.resource.Bucket(self.bucket_name)
            for key_prefix in key_prefixes:
                key_prefix = key_prefix.strip()
                if key_prefix != '':
                    log.info(f'Scanning files in key {key_prefix}')
                    for bucket_object in bucket.objects.filter(Prefix=key_prefix):
                        file_name = bucket_object.key
                        if len(file_name) > 0 and file_name[-1] not in {'/', '\\'}:
                            local_file_path = None
                            local_last_modified = None
                            local_file_size = None
                            if local_folder:
                                local_file_path = os.path.join(local_folder, file_name)
                                if os.path.exists(local_file_path):
                                    local_last_modified = datetime.fromtimestamp(
                                        os.path.getmtime(local_file_path),
                                        tz=local_timezone
                                    )
                                    local_file_size = os.path.getsize(local_file_path)

                            file_entry = File_Entry(
                                content_path=bucket_object.key,
                                full_local_path=local_file_path,
                                source_path=f'{self.bucket_name}/{bucket_object.key}',
                                s3_last_modified=bucket_object.last_modified,
                                s3_file_size=bucket_object.size,
                                bucket_object=bucket_object,
                                local_last_modified=local_last_modified,
                                local_file_size=local_file_size,
                            )

                            file_list.append(file_entry)
            return file_list

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                log.error("The object does not exist.")
                raise e
            else:
                raise e

    @staticmethod
    def download_file_list_from_s3(
            file_list: List[File_Entry]
    ):
        log = logging.getLogger(__name__)

        for file_entry in file_list:
            log.info(f'Downloading {file_entry.content_path}')
            full_dir_path = os.path.dirname(file_entry.full_local_path)
            os.makedirs(full_dir_path, exist_ok=True)
            body = file_entry.bucket_object.get()['Body']

            with open(file_entry.full_local_path, 'wb') as local_file:
                while local_file.write(body.read(amt=512)):
                    pass

    @staticmethod
    def filter_list_changed_vs_local(file_list: List[File_Entry]) -> List[File_Entry]:
        result_list = list()
        for file_entry in file_list:
            if file_entry.local_last_modified is None:
                result_list.append(file_entry)
            elif file_entry.local_last_modified < file_entry.s3_last_modified:
                result_list.append(file_entry)
            elif file_entry.local_file_size is None:
                result_list.append(file_entry)
            elif file_entry.local_file_size != file_entry.s3_file_size:
                result_list.append(file_entry)
        return result_list

    def download_files_from_s3(
            self,
            key_prefixes: List[str],
            local_folder: str,
            changed_only=True,
            return_full_list=True,
    ) -> List[File_Entry]:

        file_list = self.scan_files_from_s3(
            key_prefixes=key_prefixes,
            local_folder=local_folder,
        )

        if changed_only:
            download_file_list = Boto3_S3.filter_list_changed_vs_local(file_list)
            if not return_full_list:
                file_list = download_file_list
        else:
            download_file_list = file_list

        Boto3_S3.download_file_list_from_s3(download_file_list)

        return file_list

    def upload_file_to_s3(
            self,
            file_key: str,
            local_file_path: str,
    ):
        log = logging.getLogger(__name__)

        done = False
        tries = 0
        while not done:
            try:
                # Upload the file
                self.client.upload_file(
                    Filename=str(local_file_path),
                    Bucket=self.bucket_name,
                    Key=str(file_key),
                )
                done = True

            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    log.error("The object does not exist.")
                    raise e
                else:
                    raise e
            except OSError as e:
                if tries < 3:
                    log.warning(f"Got error {e} will try again with name '{local_file_path}'")
                    tries += 1
                else:
                    raise

    def unload_data(
            self,
            database: DatabaseMetadata,
            file_format: FileFormat = None,
            query: str = None,
            out_folder: str = None,
            filename: str = None,
            delimiter: str = None,
    ):

        log = logging.getLogger(__name__)
        counter = 0

        filename = filename.replace('\\', '/')
        fldr = out_folder.replace('\\', '/')

        sql_source = f"""
            UNLOAD ('{query}') to 's3://{self.bucket_name}/{fldr}/' 
            credentials 'aws_access_key_id={self.user_id};aws_secret_access_key={self.get_password()}'
            parallel off ALLOWOVERWRITE 
            REGION '{self.region_name}'
        """

        if file_format is FileFormat.csv:
            sql_source += f" DELIMITER '{delimiter}' CSV HEADER;"
            filenm = '000'
        elif file_format is FileFormat.parquet:
            sql_source += f" PARQUET;"
            filenm = '000.parquet'
        else:
            log.info(f"Invalid file type {file_format}. Nothing to process.")
            return

        try:
            database.execute(sql_source)

            give_up = False
            while not give_up:
                try:
                    self.client.head_object(Bucket=self.bucket_name, Key=f"{fldr}/{filenm}")
                    give_up = True
                except ClientError as e:
                    if e.response['Error']['Code'] == "404":
                        log.warning(f"{filenm} does not exist in {self.bucket_name}/{fldr}. Waiting... {counter}")
                        time.sleep(5)
                if counter > 12:
                    log.error(
                        f"{filenm} does not exist in {self.bucket_name}/{fldr}. "
                        f"This file has to be 'renamed' as {filename}. "
                        f"Already waited for a minute. Please check. Exiting."
                    )
                    give_up = True
                    exit(99)
                else:
                    counter += 1

            self.client.copy_object(Bucket=f"{self.bucket_name}", CopySource=f"{self.bucket_name}/{fldr}/{filenm}", Key=f"{filename}")
            self.client.delete_object(Bucket=f"{self.bucket_name}", Key=f"{fldr}/{filenm}")

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                log.error("The object does not exist.")
                raise e
            else:
                raise e

    def load_into_table_from_s3(
            self,
            database: DatabaseMetadata,
            table_name: str = None,
            filename: str = None,
            delimiter: str = None,
            region: str = None,
    ):
        log = logging.getLogger(__name__)

        if region is None:
            region = self.region_name
            if region is None:
                region = 'us-east-1'

        password = self.get_password()

        sql_source = f"""
            copy {table_name} from 's3://{self.bucket_name}/{filename}' 
            credentials  'aws_access_key_id={self.user_id};aws_secret_access_key={password}' 
            DELIMITER '{delimiter}' CSV NULL '' IGNOREHEADER 1
            REGION '{region}'
            ;
            commit;
            """

        try:
            database.execute(sql_source)

            log.info(f"Loaded {self.bucket_name}/{filename} into {table_name}.")

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                log.error("The object does not exist.")
                raise e
            else:
                raise e
