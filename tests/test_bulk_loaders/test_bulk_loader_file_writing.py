# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import csv
import gzip
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from tempfile import TemporaryDirectory
from typing import Iterable, Optional
from unittest.mock import MagicMock

import fastavro
import pytest
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.csv_bulk_loader_mixin import CsvBulkLoaderMixin
from bi_etl.components.table import Table
from bi_etl.scheduler.etl_task import ETLTask

import sys

# Detect if the current run is executing via pytest
if "PYTEST_VERSION" in os.environ or "PYTEST_CURRENT_TEST" in os.environ:
    pass
else:
    raise AssertionError(
        "CRITICAL: This test suite must be run using 'pytest'. "
        "Running via 'unittest' or direct python execution will fail."
    )

# ─────────────────────────────────────────────────────────────────────────────
# Concrete test subclasses
# ─────────────────────────────────────────────────────────────────────────────

class _TestAvroBulkLoader(AvroBulkLoaderMixin, BulkLoader):
    """Minimal concrete loader that exposes the Avro helpers for testing."""

    def __init__(self, chunk_size: int = 50_000):
        super().__init__()
        self._init_avro(chunk_size=chunk_size)

    def load_from_iterable(
            self,
            iterable: Iterable,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str | None = None,
            parent_task: Optional[ETLTask] = None,
    ) -> int:
        raise NotImplementedError()

    def load_from_files(
            self,
            local_files: list,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str | None = None,
    ) -> int:
        raise NotImplementedError()


class _TestCsvBulkLoader(CsvBulkLoaderMixin, BulkLoader):
    """Minimal concrete loader that exposes the CSV helpers for testing."""

    def __init__(
            self,
            chunk_size: int = 25_000,
            has_header: bool = True,
            delimiter: str = '|',
            null_value: str = '',
    ):
        super().__init__()
        self._init_csv(
            chunk_size=chunk_size,
            has_header=has_header,
            delimiter=delimiter,
            null_value=null_value,
        )

    def load_from_iterable(
            self,
            iterable: Iterable,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            progress_frequency: int = 10,
            analyze_compression: str | None = None,
            parent_task: Optional[ETLTask] = None,
    ) -> int:
        raise NotImplementedError()

    def load_from_files(
            self,
            local_files: list,
            table_object: Table,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str | None = None,
    ) -> int:
        raise NotImplementedError()


# ─────────────────────────────────────────────────────────────────────────────
# Mock Table (only the interface consumed by AvroBulkLoaderMixin)
# ─────────────────────────────────────────────────────────────────────────────

class _MockColumn:
    """Holds a column name plus its SQLAlchemy type."""

    def __init__(self, name: str, sa_type):
        self.name = name
        self.type = sa_type


class _MockTable:
    """Minimal table-like stand-in for bi_etl.components.table.Table."""

    def __init__(self, columns, table_name: str = 'test_schema.test_table'):
        self._columns = columns
        self.qualified_table_name = table_name
        self.column_names = [c.name for c in columns]

    @property
    def columns(self):
        return self._columns

    # noinspection method-may-be-static
    def _get_python_type(self, sa_type):
        # SQLAlchemy types expose .python_type directly
        return sa_type.python_type


# ─────────────────────────────────────────────────────────────────────────────
# Shared test data
# ─────────────────────────────────────────────────────────────────────────────

_SA_COLUMNS = [
    _MockColumn('id', Integer()),
    _MockColumn('name', String()),
    _MockColumn('score', Float()),
    _MockColumn('active', Boolean()),
    _MockColumn('birthday', Date()),
    _MockColumn('created_at', DateTime()),
    _MockColumn('amount', Numeric(precision=10, scale=2)),
]

_AVRO_ROWS = [
    {
        'id': 1,
        'name': 'Alice',
        'score': 9.5,
        'active': True,
        'birthday': date(1990, 1, 15),
        'created_at': datetime(2024, 3, 1, 12, 0, 0),
        'amount': Decimal('99.99'),
    },
    {
        'id': 2,
        'name': 'Bob',
        'score': 7.0,
        'active': False,
        'birthday': date(1985, 6, 30),
        'created_at': datetime(2024, 3, 2, 8, 30, 0),
        'amount': Decimal('1234.56'),
    },
    {
        # All nullable fields set to None
        'id': None,
        'name': 'Carol',
        'score': None,
        'active': True,
        'birthday': None,
        'created_at': None,
        'amount': None,
    },
]

_CSV_COLUMNS = ['id', 'name', 'value', 'flag']
_CSV_ROWS = [
    {'id': '1', 'name': 'Alice', 'value': '10.5', 'flag': 'Y'},
    {'id': '2', 'name': 'Bob', 'value': '20.0', 'flag': 'N'},
    {'id': '3', 'name': 'Carol', 'value': '', 'flag': 'Y'},
]


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def avro_loader():
    """Fresh loader per test so _translate_columns never leaks between tests."""
    return _TestAvroBulkLoader(chunk_size=10)


@pytest.fixture
def mock_table():
    return _MockTable(_SA_COLUMNS)


@pytest.fixture
def csv_loader():
    return _TestCsvBulkLoader(
        chunk_size=10,
        has_header=True,
        delimiter='|',
        null_value='',
    )


@pytest.fixture
def mock_task():
    """MagicMock task for components that require an ETLTask."""
    return MagicMock()


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _strip_tz(dt):
    """Return a naive datetime regardless of whether *dt* carries tzinfo."""
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


# ─────────────────────────────────────────────────────────────────────────────
# Avro: schema generation tests
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# Avro: write-and-read-back tests
# ─────────────────────────────────────────────────────────────────────────────

# noinspection bad-argument-type
class TestAvroWriteAndRead:
    """Write Avro chunks to a temp dir and verify the files read back correctly."""
    _ROUNDTRIP_ROWS = _AVRO_ROWS

    def test_chunk_produces_readable_avro_file(self, avro_loader, mock_table):
        """_write_avro_chunk creates a file that fastavro can open and iterate."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            avro_loader._write_avro_chunk(
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
            avro_loader._write_avro_chunk(
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
            avro_loader._write_avro_chunk(
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
            avro_loader._write_avro_chunk(
                temp_dir=tmp,
                file_number=1,
                parsed_schema=parsed,
                data_chunk=self._ROUNDTRIP_ROWS,
                local_files_list=files,
            )
            with open(files[0], 'rb') as f:
                rows = list(fastavro.reader(f))

        assert _strip_tz(rows[0]['created_at']) == datetime(2024, 3, 1, 12, 0, 0)
        assert _strip_tz(rows[1]['created_at']) == datetime(2024, 3, 2, 8, 30, 0)

    def test_null_values_are_preserved(self, avro_loader, mock_table):
        """Nullable fields written as None come back as None."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            avro_loader._write_avro_chunk(
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
        """Each _write_avro_chunk call appends a unique file path."""
        parsed = avro_loader._parse_avro_schema(mock_table, 'test_schema.test_table')
        with TemporaryDirectory() as tmp:
            files: list = []
            for i, row in enumerate(self._ROUNDTRIP_ROWS):
                avro_loader._write_avro_chunk(
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


# ─────────────────────────────────────────────────────────────────────────────
# CSV: write-and-read-back tests
# ─────────────────────────────────────────────────────────────────────────────

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
            loader: _TestCsvBulkLoader,
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
            self._write_rows_to_file(csv_loader, _CSV_COLUMNS, _CSV_ROWS, path, mock_task)
            result = self._read_rows_from_file(path, csv_loader.csv_delimiter)
        assert len(result) == len(_CSV_ROWS)

    def test_string_values_survive_round_trip(self, csv_loader, mock_task):
        """All string field values come back unchanged."""
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(csv_loader, _CSV_COLUMNS, _CSV_ROWS, path, mock_task)
            result = self._read_rows_from_file(path, csv_loader.csv_delimiter)
        assert result[0] == {'id': '1', 'name': 'Alice', 'value': '10.5', 'flag': 'Y'}
        assert result[1] == {'id': '2', 'name': 'Bob', 'value': '20.0', 'flag': 'N'}
        assert result[2]['name'] == 'Carol'

    def test_header_row_contains_column_names(self, csv_loader, mock_task):
        """When has_header=True the first line of the file is the column header."""
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(csv_loader, _CSV_COLUMNS, _CSV_ROWS, path, mock_task)
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                first_line = f.readline().strip()
        assert first_line == csv_loader.csv_delimiter.join(_CSV_COLUMNS)

    def test_no_header_row_when_disabled(self, mock_task):
        """When has_header=False the first line of the file is a data row."""
        loader = _TestCsvBulkLoader(has_header=False, delimiter='|')
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            writer, text_wrapper, zip_file = loader._open_csv_writer(
                filepath=path,
                column_names=_CSV_COLUMNS,
                parent_task=mock_task,
            )
            try:
                writer.get_writer().writerow(_CSV_ROWS[0])
            finally:
                loader._close_csv_writer(writer, text_wrapper, zip_file)

            with gzip.open(path, 'rt', encoding='utf-8') as f:
                first_line = f.readline().strip()

        # Header column names should not appear as the first line
        assert first_line not in ('|'.join(_CSV_COLUMNS),)
        # Data values from the first row should be present
        assert '1' in first_line
        assert 'Alice' in first_line

    def test_custom_delimiter_appears_in_file(self, mock_task):
        """The configured delimiter is used as the column separator."""
        loader = _TestCsvBulkLoader(delimiter=',')
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(loader, _CSV_COLUMNS, _CSV_ROWS[:1], path, mock_task)
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                header_line = f.readline().strip()
        assert header_line == ','.join(_CSV_COLUMNS)

    def test_output_is_valid_gzip(self, csv_loader, mock_task):
        """Written files carry the standard gzip magic bytes (1F 8B)."""
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'data.csv.gz')
            self._write_rows_to_file(csv_loader, _CSV_COLUMNS, _CSV_ROWS, path, mock_task)
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
            batch = [_CSV_ROWS[:2], _CSV_ROWS[2:]]
            for path, rows in zip(paths, batch):
                self._write_rows_to_file(csv_loader, _CSV_COLUMNS, rows, path, mock_task)

            result_0 = self._read_rows_from_file(paths[0], csv_loader.csv_delimiter)
            result_1 = self._read_rows_from_file(paths[1], csv_loader.csv_delimiter)

        assert len(result_0) == 2
        assert len(result_1) == 1
        assert result_0[0]['name'] == 'Alice'
        assert result_1[0]['name'] == 'Carol'
