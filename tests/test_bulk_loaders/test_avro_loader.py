"""
Tests for the Avro bulk loader mixin: schema generation, file writing, value handling and S3 upload.
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import os
import threading
import time
from datetime import date, datetime, timedelta
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import fastavro
import pytest
from sqlalchemy import Integer, Interval, JSON, String

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from tests.test_bulk_loaders.bulk_loader_test_helpers import (
    AVRO_ROWS, CHUNK_SIZE, EXPECTED_FILE_COUNT, ROW_COUNT, AvroLoaderForTests, FakeBucket, FakeRow,
    FakeTable, KwRow, KwTable, S3AvroLoader, UploadError, count_avro_rows, strip_tz, upload_threads_alive,
)


def write_avro_chunk(loader, temp_dir, file_number, parsed_schema, data_chunk, local_files_list):
    """Write already translated dicts to a numbered chunk file the same way load_from_iterable does."""
    writer = loader._start_avro_chunk(temp_dir, file_number, parsed_schema, local_files_list)
    for record in data_chunk:
        writer.write_record(record)
    loader._finish_avro_chunk(writer, file_number)


@pytest.fixture
def avro_loader():
    """Fresh loader per test so _translate_columns never leaks between tests."""
    return AvroLoaderForTests(chunk_size=10)


# noinspection bad-argument-type
class TestAvroSchemaGeneration:
    """Verify _get_avro_schema produces a structurally correct Avro schema."""

    def test_field_names_match_columns(self, avro_loader, mock_table):
        """Field names in the schema match the table's column names in order."""
        schema = avro_loader._get_avro_schema(mock_table, 'test_schema.test_table')
        assert [f['name'] for f in schema['fields']] == mock_table.column_names

    def test_all_fields_are_nullable(self, avro_loader, mock_table):
        """Every field has null as the first union member and None as default."""
        schema = avro_loader._get_avro_schema(mock_table, 'test_schema.test_table')
        for field in schema['fields']:
            assert field['type'][0] == 'null', (
                f"{field['name']}: expected null first in type union, got {field['type'][0]}"
            )
            assert field['default'] is None

    def test_integer_column_maps_to_long(self, avro_loader, mock_table):
        """Python int columns map to Avro 'long'."""
        schema = avro_loader._get_avro_schema(mock_table, 'test_schema.test_table')
        id_field = next(f for f in schema['fields'] if f['name'] == 'id')
        assert 'long' in id_field['type']

    def test_date_column_uses_int_logical_type(self, avro_loader, mock_table):
        """date columns use {type:int, logicalType:date}, not bare 'date'."""
        schema = avro_loader._get_avro_schema(mock_table, 'test_schema.test_table')
        field = next(f for f in schema['fields'] if f['name'] == 'birthday')
        logical = field['type'][1]
        assert isinstance(logical, dict), "date field should be a logical-type dict"
        assert logical.get('logicalType') == 'date'
        assert logical.get('type') == 'int'

    def test_datetime_column_uses_timestamp_millis(self, avro_loader, mock_table):
        """datetime columns use timestamp-millis logical type."""
        schema = avro_loader._get_avro_schema(mock_table, 'test_schema.test_table')
        field = next(f for f in schema['fields'] if f['name'] == 'created_at')
        logical = field['type'][1]
        assert isinstance(logical, dict)
        assert logical.get('logicalType') == 'timestamp-millis'
        assert logical.get('type') == 'long'

    def test_decimal_column_uses_bytes_decimal_with_column_precision_scale(
            self, avro_loader, mock_table
    ):
        """
        Numeric columns use the bytes+decimal logical type.
        Precision and scale come from the column's own type definition.
        """
        schema = avro_loader._get_avro_schema(mock_table, 'test_schema.test_table')
        field = next(f for f in schema['fields'] if f['name'] == 'amount')
        logical = field['type'][1]
        assert isinstance(logical, dict)
        assert logical.get('logicalType') == 'decimal'
        assert logical.get('type') == 'bytes'
        # Precision and scale come from Numeric(precision=10, scale=2)
        assert logical.get('precision') == 10
        assert logical.get('scale') == 2

    def test_schema_parses_without_error(self, avro_loader, mock_table):
        """fastavro.parse_schema must accept the generated schema without error."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        assert parsed is not None


class TestAvroWriteAndRead:
    """Write Avro chunks to a temp dir and verify the files read back correctly."""
    _ROUNDTRIP_ROWS = AVRO_ROWS

    def test_chunk_produces_readable_avro_file(self, avro_loader, mock_table):
        """a finished chunk is a file that fastavro can open and iterate."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            write_avro_chunk(
                avro_loader,
                temp_dir=tmp,
                file_number=1,
                parsed_schema=parsed,
                data_chunk=self._ROUNDTRIP_ROWS,
                local_files_list=files,
            )
            assert len(files) == 1
            assert os.path.exists(files[0])
            with open(files[0], 'rb') as f:
                rows = list(fastavro.reader(f))
        assert len(rows) == len(self._ROUNDTRIP_ROWS)

    def test_scalar_values_survive_round_trip(self, avro_loader, mock_table):
        """int, str, float, bool values come back unchanged."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            write_avro_chunk(
                avro_loader,
                temp_dir=tmp,
                file_number=1,
                parsed_schema=parsed,
                data_chunk=self._ROUNDTRIP_ROWS,
                local_files_list=files,
            )
            with open(files[0], 'rb') as f:
                rows = list(fastavro.reader(f))

        assert rows[0]['id'] == self._ROUNDTRIP_ROWS[0]['id']
        assert rows[0]['name'] == self._ROUNDTRIP_ROWS[0]['name']
        assert rows[0]['score'] == pytest.approx(self._ROUNDTRIP_ROWS[0]['score'])
        assert rows[0]['active'] == self._ROUNDTRIP_ROWS[0]['active']
        assert rows[0]['amount'] == self._ROUNDTRIP_ROWS[0]['amount']
        assert rows[1]['active'] == self._ROUNDTRIP_ROWS[1]['active']

    def test_date_value_survives_round_trip(self, avro_loader, mock_table):
        """date objects are decoded back as Python date instances."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            write_avro_chunk(
                avro_loader,
                temp_dir=tmp,
                file_number=1,
                parsed_schema=parsed,
                data_chunk=self._ROUNDTRIP_ROWS,
                local_files_list=files,
            )
            with open(files[0], 'rb') as f:
                rows = list(fastavro.reader(f))

        assert isinstance(rows[0]['birthday'], date)
        assert rows[0]['birthday'] == date(1990, 1, 15)
        assert rows[1]['birthday'] == date(1985, 6, 30)

    def test_datetime_value_survives_round_trip(self, avro_loader, mock_table):
        """
        datetime objects are decoded with the correct UTC-normalised value.
        fastavro returns timezone-aware datetimes for timestamp-millis; we strip
        tzinfo before comparing.
        """
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            write_avro_chunk(
                avro_loader,
                temp_dir=tmp,
                file_number=1,
                parsed_schema=parsed,
                data_chunk=self._ROUNDTRIP_ROWS,
                local_files_list=files,
            )
            with open(files[0], 'rb') as f:
                rows = list(fastavro.reader(f))

        assert strip_tz(rows[0]['created_at']) == datetime(2024, 3, 1, 12, 0, 0)
        assert strip_tz(rows[1]['created_at']) == datetime(2024, 3, 2, 8, 30, 0)

    def test_null_values_are_preserved(self, avro_loader, mock_table):
        """Nullable fields written as None come back as None."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            write_avro_chunk(
                avro_loader,
                temp_dir=tmp,
                file_number=1,
                parsed_schema=parsed,
                data_chunk=self._ROUNDTRIP_ROWS,
                local_files_list=files,
            )
            with open(files[0], 'rb') as f:
                rows = list(fastavro.reader(f))

        carol = rows[2]
        assert carol['id'] is None
        assert carol['score'] is None
        assert carol['birthday'] is None
        assert carol['created_at'] is None

    def test_multiple_chunks_produce_distinct_files(self, avro_loader, mock_table):
        """Each chunk appends a unique file path."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            for i, row in enumerate(self._ROUNDTRIP_ROWS):
                write_avro_chunk(
                    avro_loader,
                    temp_dir=tmp,
                    file_number=i + 1,
                    parsed_schema=parsed,
                    data_chunk=[row],
                    local_files_list=files,
                )
            assert len(files) == 3
            assert len(set(files)) == 3  # all paths are distinct
            for path in files:
                assert os.path.exists(path)


class StubAvroLoader(AvroBulkLoaderMixin, BulkLoader):
    def __init__(self):
        super().__init__()
        self.config = SimpleNamespace(temp_file_path=None)
        self._init_avro(rows_per_file=10)
        self.loaded_rows: list[dict] = []

    def load_from_files(self, local_files, table_object, **kwargs) -> int:
        # The files are only available until the load finishes
        self.loaded_rows = []
        for local_file in local_files:
            with open(local_file, 'rb') as f:
                self.loaded_rows.extend(fastavro.reader(f))
        return len(self.loaded_rows)


class TestAvroNulls:
    def test_none_values_are_loaded_as_null(self):
        loader = StubAvroLoader()
        table = KwTable(
            'tbl',
            id=Integer(),
            name=String(),
            duration=Interval(),
            attributes=JSON(),
        )
        row = KwRow(id=1, name=None, duration=None, attributes=None)

        assert loader.load_from_iterable([row], table) == 1

        assert loader.loaded_rows == [{'id': 1, 'name': None, 'duration': None, 'attributes': None}]

    def test_values_are_still_translated(self):
        loader = StubAvroLoader()
        table = KwTable('tbl', id=Integer(), duration=Interval(), attributes=JSON())
        row = KwRow(id=1, duration=timedelta(minutes=2), attributes={'a': 1})

        loader.load_from_iterable([row], table)

        assert loader.loaded_rows[0]['duration'] == 120
        assert loader.loaded_rows[0]['attributes'] == '{"a": 1}'

    def test_column_missing_from_row_is_loaded_as_null(self):
        loader = StubAvroLoader()
        table = KwTable('tbl', id=Integer(), duration=Interval())

        loader.load_from_iterable([KwRow(id=1)], table)

        assert loader.loaded_rows == [{'id': 1, 'duration': None}]


class TestAvroEmptyIterable:
    def test_empty_iterable_loads_nothing(self):
        loader = StubAvroLoader()
        table = KwTable('tbl', id=Integer())

        assert loader.load_from_iterable([], table) == 0

        assert loader.rows_seen == 0
        assert loader.loaded_rows == []


class TestAvroLoaderReuse:
    def test_translations_do_not_carry_over_to_the_next_table(self):
        loader = StubAvroLoader()
        first = KwTable('first', id=Integer(), duration=Interval())
        loader.load_from_iterable([KwRow(id=1, duration=timedelta(seconds=5))], first)
        assert loader.loaded_rows[0]['duration'] == 5

        # 'duration' is now a plain integer, so the timedelta conversion must not be applied to it
        second = KwTable('second', id=Integer(), duration=Integer())
        loader.load_from_iterable([KwRow(id=2, duration=7)], second)

        assert loader.loaded_rows == [{'id': 2, 'duration': 7}]
        assert loader._translate_columns == {}


class TestAvroUpload:
    def test_every_file_uploaded_by_background_thread_before_load(self, bucket):
        rows_uploaded = []
        bucket.on_upload = lambda filename, key: rows_uploaded.append(count_avro_rows(filename))
        loader = S3AvroLoader(bucket)

        loaded = loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        assert loaded == ROW_COUNT
        assert bucket.uploaded_names == ['data_1.avro', 'data_2.avro', 'data_3.avro']
        assert rows_uploaded == [CHUNK_SIZE, CHUNK_SIZE, ROW_COUNT - 2 * CHUNK_SIZE]
        assert all(upload.thread is not threading.current_thread() for upload in bucket.uploads)
        assert loader.observations.calls == 1
        # Nothing was left for load_from_files to upload itself
        assert loader.observations.uploaded_names_when_called == bucket.uploaded_names
        assert not upload_threads_alive()

    def test_uploads_use_one_folder_and_load_gets_the_matching_urls(self, bucket):
        loader = S3AvroLoader(bucket)
        loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())

        folder = loader.observations.s3_folder
        assert folder.startswith('base_folder/test_schema_test_table_')
        assert [upload.key for upload in bucket.uploads] == [
            f'{folder}/data_{n}.avro' for n in range(1, EXPECTED_FILE_COUNT + 1)
        ]
        assert loader.observations.s3_files == [
            f's3://test-bucket/{folder}/data_{n}.avro' for n in range(1, EXPECTED_FILE_COUNT + 1)
        ]

    def test_upload_starts_while_later_files_are_still_being_written(self, bucket):
        two_uploaded = threading.Event()

        def on_upload(filename, key):
            if len(bucket.uploads) >= 1:
                # This is the second upload, the first is already recorded
                two_uploaded.set()

        bucket.on_upload = on_upload
        loader = S3AvroLoader(bucket)

        def rows():
            for i in range(ROW_COUNT):
                if i == 2 * CHUNK_SIZE:
                    # Two files are complete. The third file has not been started.
                    assert two_uploaded.wait(5), 'files were not uploaded while rows were still being written'
                    assert loader.observations.calls == 0
                yield FakeRow(i)

        assert loader.load_from_iterable(rows(), FakeTable()) == ROW_COUNT

    def test_upload_failure_stops_writing_files(self, bucket):
        failed = threading.Event()

        def on_upload(filename, key):
            failed.set()
            raise UploadError('upload failed')

        bucket.on_upload = on_upload
        loader = S3AvroLoader(bucket)
        rows_read = []

        def rows():
            for i in range(10 * CHUNK_SIZE):
                if i == 2 * CHUNK_SIZE:
                    assert failed.wait(5)
                    # Let the upload thread record its failure
                    time.sleep(0.2)
                rows_read.append(i)
                yield FakeRow(i)

        with pytest.raises(UploadError, match='upload failed'):
            loader.load_from_iterable(rows(), FakeTable())

        # The failure was seen when the third file was queued, so no later rows were read
        assert len(rows_read) <= 3 * CHUNK_SIZE
        assert loader.observations.calls == 0
        assert not upload_threads_alive()

    def test_error_while_writing_aborts_uploads(self, bucket):
        loader = S3AvroLoader(bucket)

        def rows():
            for i in range(ROW_COUNT):
                if i == 2 * CHUNK_SIZE + 2:
                    raise KeyError('row source failed')
                yield FakeRow(i)

        with pytest.raises(KeyError, match='row source failed'):
            loader.load_from_iterable(rows(), FakeTable())

        assert loader.observations.calls == 0
        assert len(bucket.uploads) <= 2
        assert loader._file_uploader is None
        assert not upload_threads_alive()

    def test_non_empty_s3_folder_fails_before_any_rows_are_read(self):
        bucket = FakeBucket(existing_objects=[SimpleNamespace(key='base_folder/already_there')])
        loader = S3AvroLoader(bucket, s3_clear_before=False)
        rows_read = []

        def rows():
            for i in range(ROW_COUNT):
                rows_read.append(i)
                yield FakeRow(i)

        with pytest.raises(FileExistsError, match='not empty'):
            loader.load_from_iterable(rows(), FakeTable())

        assert rows_read == []
        assert bucket.uploads == []
        assert not upload_threads_alive()

    def test_loader_is_reusable_after_a_load(self, bucket):
        loader = S3AvroLoader(bucket)
        loader.load_from_iterable((FakeRow(i) for i in range(ROW_COUNT)), FakeTable())
        first_folder = loader.observations.s3_folder
        loader.load_from_iterable((FakeRow(i) for i in range(CHUNK_SIZE)), FakeTable())

        assert loader.observations.s3_folder != first_folder
        assert len(bucket.uploads) == EXPECTED_FILE_COUNT + 1
