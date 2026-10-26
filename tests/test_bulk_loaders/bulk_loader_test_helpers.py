"""
Fakes, stub loaders and helper functions shared by the per file type bulk loader test modules.

S3 is replaced by :class:`FakeBucket`, which records every upload and the thread that did it.
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import gzip
import os
import threading
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Callable, Iterable, Optional
from unittest.mock import MagicMock

import fastavro
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String

from bi_etl.bulk_loaders.avro_bulk_loader_mixin import AvroBulkLoaderMixin
from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.csv_bulk_loader_mixin import CsvBulkLoaderMixin
from bi_etl.bulk_loaders.parquet_bulk_loader_mixin import ParquetBulkLoaderMixin
from bi_etl.bulk_loaders.s3_bulk_loader_mixin import S3BulkLoaderMixin
from bi_etl.components.table import Table
from bi_etl.scheduler.etl_task import ETLTask

# Detect if the current run is executing via pytest
if "PYTEST_VERSION" in os.environ or "PYTEST_CURRENT_TEST" in os.environ:
    pass
else:
    raise AssertionError(
        "CRITICAL: This test suite must be run using 'pytest'. "
        "Running via 'unittest' or direct python execution will fail."
    )

ROW_COUNT = 25
CHUNK_SIZE = 10
# 25 rows in chunks of 10 rows gives files of 10, 10 and 5 rows
EXPECTED_FILE_COUNT = 3


class UploadError(OSError):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Fake S3
# ─────────────────────────────────────────────────────────────────────────────

class FakeBucket:
    """Stands in for a boto3 ``Bucket`` resource."""

    def __init__(self, existing_objects=()):
        self.existing_objects = list(existing_objects)
        self.uploads: list[SimpleNamespace] = []
        # Called with (filename, key) at the start of each upload. May raise to fail the upload.
        self.on_upload: Optional[Callable[[str, str], None]] = None
        self.objects = SimpleNamespace(filter=self._filter)

    def _filter(self, Prefix: str):
        uploaded = [
            SimpleNamespace(key=upload.key, delete=lambda upload=upload: self.uploads.remove(upload))
            for upload in self.uploads if upload.key.startswith(Prefix)
        ]
        # Existing objects are treated as being in every folder
        existing = [
            SimpleNamespace(key=obj.key, delete=lambda obj=obj: self.existing_objects.remove(obj))
            for obj in self.existing_objects
        ]
        return existing + uploaded

    def upload_file(self, filename: str, key: str):
        if self.on_upload is not None:
            self.on_upload(filename, key)
        self.uploads.append(
            SimpleNamespace(filename=filename, key=key, thread=threading.current_thread())
        )

    @property
    def uploaded_names(self) -> list[str]:
        return [os.path.basename(upload.filename) for upload in self.uploads]


def s3_config(**overrides) -> SimpleNamespace:
    values = dict(
        bucket_name='test-bucket',
        folder='base_folder',
        s3_clear_before=True,
        s3_clear_when_done=False,
        s3_clear_on_failure=False,
        session=MagicMock(),
        temp_file_path=None,
        user_id=None,
        region_name=None,
        s3_file_max_rows=None,
        analyze_compression=None,
        redshift_copy_iam_role=None,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


# ─────────────────────────────────────────────────────────────────────────────
# Fake rows, tables and CSV writer
# ─────────────────────────────────────────────────────────────────────────────

class FakeRow:
    """Row with an ``id`` and a ``name`` column."""

    def __init__(self, i: int):
        self.as_dict = {'id': i, 'name': f'name {i}'}

    def __getitem__(self, key):
        return self.as_dict[key]


class FakeTable:
    """Only the interface the loaders use from a Table."""

    qualified_table_name = 'test_schema.test_table'
    column_names = ['id', 'name']

    class _Column:
        def __init__(self, name, sa_type):
            self.name = name
            self.type = sa_type

    columns = [_Column('id', Integer()), _Column('name', String())]

    @staticmethod
    def _get_python_type(sa_type):
        return sa_type.python_type


class FakeCsvWriter:
    """Replacement for ``CSVWriter`` that does not need an ETLTask."""

    def __init__(self, parent_task, text_wrapper, **kwargs):
        self._text_wrapper = text_wrapper

    def insert_row(self, row):
        self._text_wrapper.write(f"{row['id']}\n")

    def close(self):
        pass


class KwRow:
    """Row built from keyword arguments."""

    def __init__(self, **values):
        self.as_dict = dict(values)


class KwColumn:
    def __init__(self, name, sa_type):
        self.name = name
        self.type = sa_type


class KwTable:
    """Table built from ``column_name=SQLAlchemy type`` keyword arguments."""

    def __init__(self, table_name: str, **column_types):
        self.qualified_table_name = table_name
        self.columns = [KwColumn(column_name, sa_type) for column_name, sa_type in column_types.items()]
        self.column_names = list(column_types)

    @staticmethod
    def _get_python_type(sa_type):
        return sa_type.python_type


class MockColumn:
    """Holds a column name plus its SQLAlchemy type."""

    def __init__(self, name: str, sa_type):
        self.name = name
        self.type = sa_type


class MockTable:
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

SA_COLUMNS = [
    MockColumn('id', Integer()),
    MockColumn('name', String()),
    MockColumn('score', Float()),
    MockColumn('active', Boolean()),
    MockColumn('birthday', Date()),
    MockColumn('created_at', DateTime()),
    MockColumn('amount', Numeric(precision=10, scale=2)),
]

# Rows for the columns in SA_COLUMNS
AVRO_ROWS = [
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

CSV_COLUMNS = ['id', 'name', 'value', 'flag']
CSV_ROWS = [
    {'id': '1', 'name': 'Alice', 'value': '10.5', 'flag': 'Y'},
    {'id': '2', 'name': 'Bob', 'value': '20.0', 'flag': 'N'},
    {'id': '3', 'name': 'Carol', 'value': '', 'flag': 'Y'},
]


# ─────────────────────────────────────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────────────────────────────────────

class _NoLoadMixin:
    """Gives a loader the abstract methods, both raising ``NotImplementedError``."""

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


class AvroLoaderForTests(AvroBulkLoaderMixin, BulkLoader):
    """Minimal concrete loader that exposes the Avro helpers for testing."""

    def __init__(self, chunk_size: int = 50_000):
        super().__init__()
        self._init_avro(chunk_size=chunk_size)

    load_from_iterable = _NoLoadMixin.load_from_iterable
    load_from_files = _NoLoadMixin.load_from_files


class CsvLoaderForTests(CsvBulkLoaderMixin, BulkLoader):
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

    load_from_iterable = _NoLoadMixin.load_from_iterable
    load_from_files = _NoLoadMixin.load_from_files


class ParquetLoaderForTests(ParquetBulkLoaderMixin, BulkLoader):
    """Minimal concrete loader that exposes the Parquet helpers for testing."""

    def __init__(self, chunk_size: int = 500_000):
        super().__init__()
        self._init_parquet(chunk_size=chunk_size)

    load_from_files = _NoLoadMixin.load_from_files


class Observations:
    """What ``load_from_files`` saw when it was called."""

    def __init__(self):
        self.calls = 0
        self.uploaded_names_when_called: list[str] = []
        self.s3_folder: Optional[str] = None
        self.s3_files: list[str] = []


class RecordingS3LoaderMixin:
    """Adds an S3-backed ``load_from_files`` that records what was uploaded when it was called."""

    def _init_recording(self, bucket: FakeBucket):
        self.observations = Observations()
        self.bucket = bucket

    def load_from_files(
            self,
            local_files: list,
            table_object,
            table_to_load: str | None = None,
            perform_rename: bool = False,
            file_compression: str = '',
            options: str = '',
            analyze_compression: str | None = None,
    ) -> int:
        self.observations.calls += 1
        self.observations.s3_folder, self.observations.s3_files = self._upload_files_to_s3(local_files, table_object)
        self.observations.uploaded_names_when_called = self.bucket.uploaded_names
        return ROW_COUNT


class S3AvroLoader(AvroBulkLoaderMixin, RecordingS3LoaderMixin, S3BulkLoaderMixin, BulkLoader):
    def __init__(self, bucket: FakeBucket, **config_overrides):
        super().__init__()
        self.config = s3_config(**config_overrides)
        self._init_s3(self.config)
        self._init_avro(chunk_size=CHUNK_SIZE)
        self._init_recording(bucket)


class S3CsvLoader(CsvBulkLoaderMixin, RecordingS3LoaderMixin, S3BulkLoaderMixin, BulkLoader):
    def __init__(self, bucket: FakeBucket, **config_overrides):
        super().__init__()
        self.config = s3_config(**config_overrides)
        self._init_s3(self.config)
        self._init_csv(chunk_size=CHUNK_SIZE)
        self._init_recording(bucket)


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────

def upload_threads_alive() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name.endswith(' upload')]


def read_gzip_lines(filename: str) -> list[str]:
    # Reading to the end fails if the gzip trailer was not written, i.e. the file was not closed yet
    with gzip.open(filename, 'rt', encoding='utf-8') as f:
        return f.read().splitlines()


def count_avro_rows(filename: str) -> int:
    with open(filename, 'rb') as f:
        return sum(1 for _ in fastavro.reader(f))


def strip_tz(dt):
    """Return a naive datetime regardless of whether *dt* carries tzinfo."""
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def patch_copy(loader, monkeypatch) -> list[dict]:
    """Replace the Redshift ``load_from_s3_path`` of *loader* with a recorder. Returns the list of recorded calls."""
    copies = []

    def fake_load_from_s3_path(**kwargs):
        copies.append(kwargs)
        return ROW_COUNT

    monkeypatch.setattr(loader, 'load_from_s3_path', fake_load_from_s3_path)
    return copies
