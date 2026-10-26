"""Fixtures shared by the bulk loader test modules."""
from unittest.mock import MagicMock

import pytest

from bi_etl.bulk_loaders import csv_bulk_loader_mixin, redshift_s3_csv_loader
from tests.test_bulk_loaders.bulk_loader_test_helpers import FakeBucket, FakeCsvWriter, MockTable, SA_COLUMNS


@pytest.fixture
def bucket() -> FakeBucket:
    return FakeBucket()


@pytest.fixture
def mock_table() -> MockTable:
    return MockTable(SA_COLUMNS)


@pytest.fixture
def mock_task():
    """MagicMock task for components that require an ETLTask."""
    return MagicMock()


@pytest.fixture
def fake_csv_writer(monkeypatch):
    """Replace ``CSVWriter`` with one that does not need an ETLTask. Not autouse: some tests need the real writer."""
    monkeypatch.setattr(csv_bulk_loader_mixin, 'CSVWriter', FakeCsvWriter)
    monkeypatch.setattr(redshift_s3_csv_loader, 'CSVWriter', FakeCsvWriter)
