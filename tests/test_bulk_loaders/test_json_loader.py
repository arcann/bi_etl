"""
Tests for the Redshift JSON loader: file writing and S3 upload.
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from bi_etl.bulk_loaders.redshift_s3_json_loader import RedShiftS3JSONBulk
from tests.test_bulk_loaders.bulk_loader_test_helpers import (
    CHUNK_SIZE, ROW_COUNT, FakeRow, FakeTable, patch_copy, read_gzip_lines, s3_config, upload_threads_alive,
)


class TestRedshiftJsonUpload:
    def test_files_uploaded_before_copy(self, bucket, monkeypatch):
        rows_uploaded = []
        bucket.on_upload = lambda filename, key: rows_uploaded.extend(read_gzip_lines(filename))
        loader = RedShiftS3JSONBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        loaded = loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert loaded == ROW_COUNT
        assert bucket.uploaded_names == ['data_0.json.gz', 'data_1.json.gz', 'data_2.json.gz']
        assert len(rows_uploaded) == ROW_COUNT
        assert all(upload.thread is not threading.current_thread() for upload in bucket.uploads)
        assert len(copies) == 1
        folder = copies[0]['s3_source_path']
        assert sorted(copies[0]['file_list']) == [
            f's3://test-bucket/{folder}/data_0.json.gz',
            f's3://test-bucket/{folder}/data_1.json.gz',
            f's3://test-bucket/{folder}/data_2.json.gz',
        ]
        assert not upload_threads_alive()

    def test_files_are_written_under_configured_temp_file_path(self, bucket, monkeypatch, tmp_path):
        written_files = []
        bucket.on_upload = lambda filename, key: written_files.append(Path(filename))
        loader = RedShiftS3JSONBulk(s3_config(s3_file_max_rows=CHUNK_SIZE, temp_file_path=tmp_path))
        loader.bucket = bucket
        patch_copy(loader, monkeypatch)

        loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert len(written_files) == 3
        assert all(tmp_path in file.parents for file in written_files)
        # The temporary directory is removed after the load
        assert list(tmp_path.iterdir()) == []

    def test_default_max_rows(self):
        assert RedShiftS3JSONBulk(s3_config()).s3_file_max_rows == 25000

    def test_upload_starts_while_rows_are_still_being_written(self, bucket, monkeypatch):
        first_uploaded = threading.Event()
        bucket.on_upload = lambda filename, key: first_uploaded.set()
        loader = RedShiftS3JSONBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        def rows():
            for i in range(ROW_COUNT):
                if i == CHUNK_SIZE + 1:
                    assert first_uploaded.wait(5), 'first file was not uploaded while rows were still being written'
                    assert not copies
                yield FakeRow(i)

        assert loader.load_from_iterable(rows(), FakeTable()) == ROW_COUNT

    def test_error_while_writing_aborts_uploads(self, bucket, monkeypatch):
        loader = RedShiftS3JSONBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        def rows():
            for i in range(ROW_COUNT):
                if i == 2 * CHUNK_SIZE + 2:
                    raise KeyError('row source failed')
                yield FakeRow(i)

        with pytest.raises(KeyError, match='row source failed'):
            loader.load_from_iterable(rows(), FakeTable())

        assert not copies
        assert 'data_2.json.gz' not in bucket.uploaded_names
        assert not upload_threads_alive()

    def test_empty_iterable(self, bucket, monkeypatch):
        loader = RedShiftS3JSONBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        assert loader.load_from_iterable(iter([]), FakeTable()) == 0
        assert not copies
        assert bucket.uploads == []
        assert not upload_threads_alive()
