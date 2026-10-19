# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import logging
import os.path
from typing import *

if TYPE_CHECKING:
    from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class S3BulkLoaderMixin:
    """Mixin providing shared S3 upload and folder management for bulk loaders.

    Subclasses must call :meth:`_init_s3` from their ``__init__`` after
    ``super().__init__()`` so that ``self.log`` (set by :class:`BulkLoader`)
    is already available.
    """

    def _init_s3(self, config: S3_Bulk_Loader_Config):
        """Initialise S3 connection state.  Call from subclass ``__init__``."""
        self.s3_bucket_name = config.bucket_name
        self.s3_folder = config.folder
        self.s3_clear_before = config.s3_clear_before
        self.s3_clear_when_done = config.s3_clear_when_done
        self.session = config.session
        self.s3 = self.session.resource('s3')
        self.bucket = self.s3.Bucket(self.s3_bucket_name)

    # --- S3 folder operations ------------------------------------------------

    def s3_folder_contents(
            self,
            s3_full_folder: str,
    ):
        return [obj for obj in self.bucket.objects.filter(Prefix=s3_full_folder)]

    def clean_s3_folder(
            self,
            s3_full_folder: str,
    ):
        self.log.info(f'Cleaning S3 folder {s3_full_folder}')
        for bucket_object in self.bucket.objects.filter(Prefix=s3_full_folder):
            self.log.info(f'Removing {bucket_object}')
            bucket_object.delete()

    # --- Upload --------------------------------------------------------------

    def _post_upload_verify(self, s3_path: str):
        """Hook called after each file upload.

        Override to add post-upload verification such as eventual-consistency
        checks.  The default implementation is a no-op.
        """
        pass

    def _upload_files_to_s3(
            self,
            local_files: list,
            s3_full_folder: str,
    ) -> List[str]:
        if self.s3_clear_before:
            self.clean_s3_folder(s3_full_folder)
        else:
            folder_contents = self.s3_folder_contents(s3_full_folder)
            if folder_contents:
                raise FileExistsError(
                    'The target S3 folder is not empty and s3_clear_before = False. '
                    f'Existing contents = {folder_contents}'
                )

        s3_files = []
        total_size = 0
        for local_path in local_files:
            file_size = os.path.getsize(local_path)
            total_size += file_size
            s3_path = f'{s3_full_folder}/{os.path.basename(local_path)}'
            self.log.info(
                f"Uploading from '{local_path}' to '{self.s3_bucket_name}' "
                f"key '{s3_path}' size = {file_size:,} bytes"
            )
            s3_files.append(f's3://{self.s3_bucket_name}/{s3_path}')
            self.bucket.upload_file(str(local_path), str(s3_path))
            self._post_upload_verify(s3_path)

        self.log.info(f"Uploaded {total_size:,} bytes in total to {s3_full_folder}")
        return s3_files
