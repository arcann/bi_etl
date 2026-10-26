"""
Tests for the behaviour that all S3 bulk loaders share: ``load_from_files`` waiting for the background uploads,
and cleaning (or keeping) the S3 folder when a load fails.
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.redshift_s3_json_loader import RedShiftS3JSONBulk
from bi_etl.bulk_loaders.s3_bulk_loader_mixin import S3BulkLoaderMixin
from tests.test_bulk_loaders.bulk_loader_test_helpers import (
    CHUNK_SIZE, EXPECTED_FILE_COUNT, ROW_COUNT, FakeBucket, FakeRow, FakeTable, S3AvroLoader, UploadError,
    upload_threads_alive,
)


class TestLoadFromFiles:
    @staticmethod
    def _make_files(tmp_path, count: int) -> list[str]:
        paths = []
        for n in range(count):
            path = tmp_path / f'file_{n}.avro'
            path.write_bytes(b'x' * (n + 1))
            paths.append(str(path))
        return paths

    def test_without_background_uploads_all_files_are_uploaded_by_the_caller(self, bucket, tmp_path):
        loader = S3AvroLoader(bucket)
        files = self._make_files(tmp_path, 3)

        loader.load_from_files(files, FakeTable())

        assert bucket.uploaded_names == ['file_0.avro', 'file_1.avro', 'file_2.avro']
        assert all(upload.thread is threading.current_thread() for upload in bucket.uploads)

    def test_files_that_were_not_queued_are_uploaded_once_by_load_from_files(self, bucket, tmp_path):
        loader = S3AvroLoader(bucket)
        files = self._make_files(tmp_path, 3)

        loader._begin_file_uploads(FakeTable())
        loader._queue_file_for_upload(files[0])
        loader.load_from_files(files, FakeTable())

        assert sorted(bucket.uploaded_names) == ['file_0.avro', 'file_1.avro', 'file_2.avro']
        folders = {upload.key.rsplit('/', 1)[0] for upload in bucket.uploads}
        assert folders == {loader.observations.s3_folder}

    def test_queued_uploads_are_waited_for(self, bucket, tmp_path):
        release = threading.Event()
        bucket.on_upload = lambda filename, key: release.wait(5)
        loader = S3AvroLoader(bucket)
        files = self._make_files(tmp_path, 2)

        loader._begin_file_uploads(FakeTable())
        for path in files:
            loader._queue_file_for_upload(path)
        threading.Timer(0.1, release.set).start()
        loader.load_from_files(files, FakeTable())

        assert loader.observations.uploaded_names_when_called == ['file_0.avro', 'file_1.avro']

    def test_abort_without_active_uploads_is_harmless(self, bucket):
        loader = S3AvroLoader(bucket)
        loader._abort_file_uploads()
        loader._abort_file_uploads()

    def test_hooks_do_nothing_for_loaders_that_do_not_upload(self):
        class LocalLoader(BulkLoader):
            def load_from_iterable(self, *args, **kwargs):
                raise NotImplementedError()

        loader = LocalLoader()
        with loader._file_upload_session(FakeTable()):
            loader._queue_file_for_upload('anything')


class TestClearOnFailure:
    """``s3_clear_on_failure`` decides whether the files of a failed load are removed from S3."""

    @staticmethod
    def _fail_in_copy(loader):
        def failing_load_from_files(local_files, table_object, **kwargs):
            loader._upload_files_to_s3(local_files, table_object)
            raise RuntimeError('COPY failed')

        loader.load_from_files = failing_load_from_files

    @pytest.mark.parametrize('clear_on_failure', [False, True])
    def test_failure_after_upload(self, bucket, clear_on_failure):
        loader = S3AvroLoader(bucket, s3_clear_on_failure=clear_on_failure)
        self._fail_in_copy(loader)

        with pytest.raises(RuntimeError, match='COPY failed'):
            loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert len(bucket.uploads) == (0 if clear_on_failure else EXPECTED_FILE_COUNT)

    @pytest.mark.parametrize('clear_on_failure', [False, True])
    def test_failure_while_writing(self, bucket, clear_on_failure):
        loader = S3AvroLoader(bucket, s3_clear_on_failure=clear_on_failure)
        clean_calls = []
        original_clean = loader.clean_s3_folder
        loader.clean_s3_folder = lambda s3_full_folder: (clean_calls.append(s3_full_folder), original_clean(s3_full_folder))

        def rows():
            for i in range(ROW_COUNT):
                if i == 2 * CHUNK_SIZE + 2:
                    raise KeyError('row source failed')
                yield FakeRow(i)

        with pytest.raises(KeyError, match='row source failed'):
            loader.load_from_iterable(rows(), FakeTable())

        assert not upload_threads_alive()
        # One call prepares the folder before the load. The second is the cleanup after the failure.
        assert len(clean_calls) == (2 if clear_on_failure else 1)
        if clear_on_failure:
            assert bucket.uploads == []

    def test_upload_failure_cleans_files_already_uploaded(self, bucket):
        def on_upload(filename, key):
            if len(bucket.uploads) == 1:
                raise UploadError('upload failed')

        bucket.on_upload = on_upload
        loader = S3AvroLoader(bucket, s3_clear_on_failure=True)

        with pytest.raises(UploadError, match='upload failed'):
            loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert bucket.uploads == []

    def test_successful_load_is_not_cleaned(self, bucket):
        loader = S3AvroLoader(bucket, s3_clear_on_failure=True, s3_clear_when_done=False)

        loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert len(bucket.uploads) == EXPECTED_FILE_COUNT

    def test_folder_that_was_not_empty_is_never_cleaned(self):
        existing = SimpleNamespace(key='base_folder/already_there')
        bucket = FakeBucket(existing_objects=[existing])
        loader = S3AvroLoader(bucket, s3_clear_before=False, s3_clear_on_failure=True)

        with pytest.raises(FileExistsError, match='not empty'):
            loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert bucket.existing_objects == [existing]

    def test_error_while_cleaning_does_not_hide_the_load_error(self, bucket):
        loader = S3AvroLoader(bucket, s3_clear_on_failure=True)
        self._fail_in_copy(loader)

        calls = []

        def broken_clean(s3_full_folder):
            # The first call is the preparation of the folder before the load
            calls.append(s3_full_folder)
            if len(calls) > 1:
                raise ClientError({'Error': {'Code': 'AccessDenied', 'Message': 'denied'}}, 'DeleteObject')

        loader.clean_s3_folder = broken_clean

        with pytest.raises(RuntimeError, match='COPY failed'):
            loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert len(calls) == 2


class TestS3MixinHierarchy:
    def test_redshift_base_uses_the_s3_upload_hooks(self):
        # BulkLoader has no-op versions of the hooks, so the S3 mixin has to come first
        mro = RedShiftS3JSONBulk.__mro__
        assert mro.index(S3BulkLoaderMixin) < mro.index(BulkLoader)
        assert RedShiftS3JSONBulk._queue_file_for_upload is S3BulkLoaderMixin._queue_file_for_upload
