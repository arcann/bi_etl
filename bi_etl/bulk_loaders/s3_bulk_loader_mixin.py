# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import functools
import logging
import os.path
from pathlib import Path
from typing import *

from botocore.exceptions import BotoCoreError, ClientError

from bi_etl.bulk_loaders.file_uploader import FileUploader

if TYPE_CHECKING:
    from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config
    from bi_etl.components.table import Table


class S3BulkLoaderMixin:
    """Mixin providing shared S3 upload and folder management for bulk loaders.

    Subclasses must call :meth:`_init_s3` from their ``__init__`` after
    ``super().__init__()`` so that ``self.log`` (set by :class:`BulkLoader`)
    is already available.

    The mixin overrides the file upload hooks of :class:`~bi_etl.bulk_loaders.bulk_loader.BulkLoader`,
    so it must be listed *before* :class:`BulkLoader` in the bases of a concrete loader.
    Files that the format mixins finish writing are then uploaded on a background thread,
    and :meth:`_upload_files_to_s3` (called from ``load_from_files``) only has to wait for the remainder.
    """

    def _init_s3(self, config: S3_Bulk_Loader_Config):
        """Initialise S3 connection state.  Call from subclass ``__init__``."""
        self.s3_bucket_name = config.bucket_name
        self.s3_folder = config.folder
        self.s3_clear_before = config.s3_clear_before
        self.s3_clear_when_done = config.s3_clear_when_done
        self.s3_clear_on_failure = config.s3_clear_on_failure
        self.session = config.session
        self.s3 = self.session.resource('s3')
        self.bucket = self.s3.Bucket(self.s3_bucket_name)
        self._file_uploader: FileUploader | None = None
        self._upload_s3_folder: str | None = None
        self._failure_s3_folder: str | None = None

    # --- S3 folder operations ------------------------------------------------

    def s3_folder_contents(
            self,
            s3_full_folder: str,
    ):
        """
        List the objects in the bucket whose keys start with *s3_full_folder*.

        Parameters
        ----------
        s3_full_folder:
            Key prefix of the folder.

        Returns
        -------
        list
            The matching S3 objects.
        """
        return [obj for obj in self.bucket.objects.filter(Prefix=s3_full_folder)]

    def clean_s3_folder(
            self,
            s3_full_folder: str,
    ):
        """
        Delete every object in the bucket whose key starts with *s3_full_folder*.

        Parameters
        ----------
        s3_full_folder:
            Key prefix of the folder to empty.
        """
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

    def _prepare_s3_folder(self, s3_full_folder: str):
        """Clear *s3_full_folder*, or fail if it is not empty and ``s3_clear_before`` is False."""
        if self.s3_clear_before:
            self.clean_s3_folder(s3_full_folder)
        else:
            folder_contents = self.s3_folder_contents(s3_full_folder)
            if folder_contents:
                raise FileExistsError(
                    'The target S3 folder is not empty and s3_clear_before = False. '
                    f'Existing contents = {folder_contents}'
                )

    def _upload_file_to_s3(self, local_path: str | Path, s3_full_folder: str):
        """Upload one file into *s3_full_folder* and run :meth:`_post_upload_verify` on it."""
        s3_path = f'{s3_full_folder}/{os.path.basename(local_path)}'
        self.log.info(
            f"Uploading from '{local_path}' to '{self.s3_bucket_name}' "
            f"key '{s3_path}' size = {os.path.getsize(local_path):,} bytes"
        )
        self.bucket.upload_file(str(local_path), str(s3_path))
        self._post_upload_verify(s3_path)

    # --- Background upload ----------------------------------------------------
    # Overrides of the BulkLoader hooks. Uploading while the rest of the files are still being written
    # means the upload time is mostly hidden behind the writing time.

    def _begin_file_uploads(self, table_object: Table):
        """
        Choose the S3 folder for this load, prepare it, and start the upload thread.

        Parameters
        ----------
        table_object:
            The table being loaded.
        """
        self._abort_file_uploads()
        self._failure_s3_folder = None
        s3_full_folder = self._get_table_specific_folder_name(self.s3_folder, table_object)
        # Prepared here, on the calling thread, so that a non-empty folder fails the load before any rows are written.
        self._prepare_s3_folder(s3_full_folder)
        # Set only after the folder is prepared, so that a folder we refused to use is never cleaned on failure.
        self._failure_s3_folder = s3_full_folder
        self._upload_s3_folder = s3_full_folder
        # The upload thread is the only user of self.bucket until _upload_files_to_s3 or
        # _abort_file_uploads has joined it, as boto3 resources are not safe to share between threads.
        self._file_uploader = FileUploader(
            functools.partial(self._upload_file_to_s3, s3_full_folder=s3_full_folder),
            name=f'{self.__class__.__name__} upload',
        )

    def _queue_file_for_upload(self, local_file: str | Path):
        """
        Queue a finished file for upload by the background thread.

        Parameters
        ----------
        local_file:
            Path of the finished file.
        """
        if self._file_uploader is not None:
            self._file_uploader.submit(local_file)

    def _abort_file_uploads(self):
        """Stop the upload thread, if one is running, without uploading the files still queued."""
        uploader = self._file_uploader
        self._file_uploader = None
        self._upload_s3_folder = None
        if uploader is not None:
            uploader.abort()

    def _handle_load_failure(self):
        """
        Empty the S3 folder of the failed load if ``s3_clear_on_failure`` is True.

        Otherwise the files are left in S3 for debugging. Safe to call more than once. A problem while
        cleaning is logged rather than raised so that it does not hide the error that caused the failure.
        """
        s3_full_folder = self._failure_s3_folder
        self._failure_s3_folder = None
        if s3_full_folder is None:
            return
        if not self.s3_clear_on_failure:
            self.log.info(
                f"Load failed. Leaving S3 folder '{s3_full_folder}' in place for debugging "
                f"(s3_clear_on_failure = False)"
            )
            return
        try:
            self.clean_s3_folder(s3_full_folder)
        except (BotoCoreError, ClientError):
            self.log.exception(f"Could not clean S3 folder '{s3_full_folder}' after the load failed")

    def _upload_files_to_s3(
            self,
            local_files: list,
            table_object: Table,
    ) -> Tuple[str, List[str]]:
        """
        Make sure every file in *local_files* is in S3.

        Waits for the uploads queued by :meth:`_queue_file_for_upload` to finish and uploads any file
        in *local_files* that was not queued. When no uploads were started by :meth:`_begin_file_uploads`
        (e.g. :meth:`load_from_files` was called directly), all of the files are uploaded here.

        Parameters
        ----------
        local_files:
            Every file that is part of the load.
        table_object:
            The table being loaded. Used to name the S3 folder when no background upload is active.

        Returns
        -------
        tuple of (str, list of str)
            The S3 folder the files are in, and the ``s3://`` URL of each file in *local_files*.
        """
        uploader = self._file_uploader
        s3_full_folder = self._upload_s3_folder
        self._file_uploader = None
        self._upload_s3_folder = None

        if uploader is None:
            s3_full_folder = self._get_table_specific_folder_name(self.s3_folder, table_object)
            self._prepare_s3_folder(s3_full_folder)
            self._failure_s3_folder = s3_full_folder
            already_uploaded = set()
        else:
            already_uploaded = set(uploader.finish())

        s3_files = []
        total_size = 0
        for local_path in local_files:
            if str(local_path) not in already_uploaded:
                self._upload_file_to_s3(local_path, s3_full_folder)
            total_size += os.path.getsize(local_path)
            s3_files.append(f's3://{self.s3_bucket_name}/{s3_full_folder}/{os.path.basename(local_path)}')

        self.log.info(f"Uploaded {total_size:,} bytes in total to {s3_full_folder}")
        return s3_full_folder, s3_files
