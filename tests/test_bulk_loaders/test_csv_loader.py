"""
Tests for the CSV bulk loader mixin and the Redshift CSV loader: file writing and S3 upload.
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import csv
import gzip
import os
import threading
from tempfile import TemporaryDirectory

import pytest

from bi_etl.bulk_loaders.redshift_s3_csv_loader import RedShiftS3CSVBulk
from tests.test_bulk_loaders.bulk_loader_test_helpers import (
    CHUNK_SIZE, CSV_COLUMNS, CSV_ROWS, ROW_COUNT, CsvLoaderForTests, FakeRow, FakeTable, S3CsvLoader,
    patch_copy, read_gzip_lines, s3_config, upload_threads_alive,
)


@pytest.fixture
def csv_loader():
    return CsvLoaderForTests(
        chunk_size=10,
        has_header=True,
        delimiter='|',
        null_value='',
    )


class TestCsvWriteAndRead:
    """
    Write gzip CSV chunks via _open_csv_writer and verify the files.

    We write rows via the underlying csv.DictWriter (returned by
    writer.get_writer()) rather than going through CSVWriter.insert_row, which
    depends on ETLTask-backed statistics tracking.  This lets us isolate the
    file-format and compression mechanics from the ETL runtime.
    """

    @staticmethod
    def _write_rows_to_file(
            loader: CsvLoaderForTests,
            column_names: list[str],
            rows: list[dict],
            filepath: str,
            task=None,
    ) -> None:
        """Write *rows* to a gzip CSV file via the loader's helper methods."""
        writer, text_wrapper, zip_file = loader._open_csv_writer(
            filepath=filepath,
            column_names=column_names,
            parent_task=task,
        )
        try:
            csv_writer = writer.get_writer()
            if loader.has_header:
                csv_writer.writeheader()
            for row in rows:
                csv_writer.writerow(row)
        finally:
            loader._close_csv_writer(writer, text_wrapper, zip_file)

    @staticmethod
    def _read_rows_from_file(
            filepath: str,
            delimiter: str,
    ) -> list[dict]:
        """Read rows from a gzip CSV file as a list of dicts."""
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            return list(csv.DictReader(f, delimiter=delimiter))

    def test_row_count_matches(self, csv_loader, mock_task):
        """The number of rows read back equals the number written."""
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(csv_loader, CSV_COLUMNS, CSV_ROWS, path, mock_task)
            result = self._read_rows_from_file(path, csv_loader.csv_delimiter)
        assert len(result) == len(CSV_ROWS)

    def test_string_values_survive_round_trip(self, csv_loader, mock_task):
        """All string field values come back unchanged."""
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(csv_loader, CSV_COLUMNS, CSV_ROWS, path, mock_task)
            result = self._read_rows_from_file(path, csv_loader.csv_delimiter)
        assert result[0] == {'id': '1', 'name': 'Alice', 'value': '10.5', 'flag': 'Y'}
        assert result[1] == {'id': '2', 'name': 'Bob', 'value': '20.0', 'flag': 'N'}
        assert result[2]['name'] == 'Carol'

    def test_header_row_contains_column_names(self, csv_loader, mock_task):
        """When has_header=True the first line of the file is the column header."""
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(csv_loader, CSV_COLUMNS, CSV_ROWS, path, mock_task)
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                first_line = f.readline().strip()
        assert first_line == csv_loader.csv_delimiter.join(CSV_COLUMNS)

    def test_no_header_row_when_disabled(self, mock_task):
        """When has_header=False the first line of the file is a data row."""
        loader = CsvLoaderForTests(has_header=False, delimiter='|')
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            writer, text_wrapper, zip_file = loader._open_csv_writer(
                filepath=path,
                column_names=CSV_COLUMNS,
                parent_task=mock_task,
            )
            try:
                writer.get_writer().writerow(CSV_ROWS[0])
            finally:
                loader._close_csv_writer(writer, text_wrapper, zip_file)

            with gzip.open(path, 'rt', encoding='utf-8') as f:
                first_line = f.readline().strip()

        # Header column names should not appear as the first line
        assert first_line not in ('|'.join(CSV_COLUMNS),)
        # Data values from the first row should be present
        assert '1' in first_line
        assert 'Alice' in first_line

    def test_custom_delimiter_appears_in_file(self, mock_task):
        """The configured delimiter is used as the column separator."""
        loader = CsvLoaderForTests(delimiter=',')
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(loader, CSV_COLUMNS, CSV_ROWS[:1], path, mock_task)
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                header_line = f.readline().strip()
        assert header_line == ','.join(CSV_COLUMNS)

    def test_output_is_valid_gzip(self, csv_loader, mock_task):
        """Written files carry the standard gzip magic bytes (1F 8B)."""
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(csv_loader, CSV_COLUMNS, CSV_ROWS, path, mock_task)
            with open(path, 'rb') as f:
                magic = f.read(2)
        assert magic == b'\x1f\x8b', "File does not start with gzip magic bytes"

    def test_multiple_chunk_files_are_independent(self, csv_loader, mock_task):
        """Two chunks written to different file paths are each fully readable."""
        with TemporaryDirectory() as tmp:
            paths = [
                os.path.join(tmp, f'data_{i}.csv.gz')
                for i in range(2)
            ]
            batch = [CSV_ROWS[:2], CSV_ROWS[2:]]
            for path, rows in zip(paths, batch):
                self._write_rows_to_file(csv_loader, CSV_COLUMNS, rows, path, mock_task)

            result_0 = self._read_rows_from_file(paths[0], csv_loader.csv_delimiter)
            result_1 = self._read_rows_from_file(paths[1], csv_loader.csv_delimiter)

        assert len(result_0) == 2
        assert len(result_1) == 1
        assert result_0[0]['name'] == 'Alice'
        assert result_1[0]['name'] == 'Carol'


@pytest.mark.usefixtures('fake_csv_writer')
class TestCsvUpload:
    def test_every_file_uploaded_by_background_thread_before_load(self, bucket):
        rows_uploaded = []
        bucket.on_upload = lambda filename, key: rows_uploaded.extend(read_gzip_lines(filename))
        loader = S3CsvLoader(bucket)

        loaded = loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert loaded == ROW_COUNT
        assert bucket.uploaded_names == ['data_0.csv.gz', 'data_1.csv.gz', 'data_2.csv.gz']
        # Each file was complete (closed) when it was uploaded, and no row was lost or repeated
        assert rows_uploaded == [str(i) for i in range(ROW_COUNT)]
        assert all(upload.thread is not threading.current_thread() for upload in bucket.uploads)
        assert loader.observations.uploaded_names_when_called == bucket.uploaded_names
        assert not upload_threads_alive()

    def test_upload_starts_while_later_files_are_still_being_written(self, bucket):
        first_uploaded = threading.Event()
        bucket.on_upload = lambda filename, key: first_uploaded.set()
        loader = S3CsvLoader(bucket)

        def rows():
            for i in range(ROW_COUNT):
                if i == CHUNK_SIZE + 1:
                    # The first file is closed, the second is being written
                    assert first_uploaded.wait(5), 'first file was not uploaded while rows were still being written'
                    assert loader.observations.calls == 0
                yield FakeRow(i)

        assert loader.load_from_iterable(rows(), FakeTable()) == ROW_COUNT

    def test_error_while_writing_aborts_uploads(self, bucket):
        loader = S3CsvLoader(bucket)

        def rows():
            for i in range(ROW_COUNT):
                if i == 2 * CHUNK_SIZE + 2:
                    raise KeyError('row source failed')
                yield FakeRow(i)

        with pytest.raises(KeyError, match='row source failed'):
            loader.load_from_iterable(rows(), FakeTable())

        assert loader.observations.calls == 0
        # The file that was still being written when the error happened is never uploaded
        assert 'data_2.csv.gz' not in bucket.uploaded_names
        assert not upload_threads_alive()


@pytest.mark.usefixtures('fake_csv_writer')
class TestRedshiftCsvUpload:
    def test_files_uploaded_before_copy(self, bucket, monkeypatch):
        rows_uploaded = []
        bucket.on_upload = lambda filename, key: rows_uploaded.extend(read_gzip_lines(filename))
        loader = RedShiftS3CSVBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        loaded = loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert loaded == ROW_COUNT
        assert bucket.uploaded_names == ['data_0.csv.gz', 'data_1.csv.gz', 'data_2.csv.gz']
        assert rows_uploaded == [str(i) for i in range(ROW_COUNT)]
        assert all(upload.thread is not threading.current_thread() for upload in bucket.uploads)
        assert len(copies) == 1
        assert not upload_threads_alive()

    def test_default_max_rows(self):
        assert RedShiftS3CSVBulk(s3_config()).s3_file_max_rows == 25000

    def test_upload_starts_while_rows_are_still_being_written(self, bucket, monkeypatch):
        first_uploaded = threading.Event()
        bucket.on_upload = lambda filename, key: first_uploaded.set()
        loader = RedShiftS3CSVBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        def rows():
            for i in range(ROW_COUNT):
                if i == CHUNK_SIZE + 1:
                    assert first_uploaded.wait(5), 'first file was not uploaded while rows were still being written'
                    assert not copies
                yield FakeRow(i)

        assert loader.load_from_iterable(rows(), FakeTable()) == ROW_COUNT

    def test_empty_iterable(self, bucket, monkeypatch):
        loader = RedShiftS3CSVBulk(s3_config(s3_file_max_rows=CHUNK_SIZE))
        loader.bucket = bucket
        copies = patch_copy(loader, monkeypatch)

        assert loader.load_from_iterable(iter([]), FakeTable()) == 0
        assert not copies
        assert bucket.uploads == []
        assert not upload_threads_alive()
