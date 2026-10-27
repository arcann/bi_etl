"""
Tests for the S3 bulk loader configuration validation and the BulkLoader redaction support.
"""
# https://www.python.org/dev/peps/pep-0563/
from __future__ import annotations

import logging

import pytest
from pydantic import ValidationError

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.bulk_loaders.s3_bulk_load_config import S3_Bulk_Loader_Config


class TestS3FileMaxRowsValidation:
    @staticmethod
    def _config(**kwargs) -> S3_Bulk_Loader_Config:
        return S3_Bulk_Loader_Config(
            bucket_name='test-bucket',
            folder='base_folder',
            user_id='test_user',
            password_source='CONFIG_FILE',
            raw_password='not-a-real-password',
            **kwargs,
        )

    def test_default_is_none(self):
        assert self._config().s3_file_max_rows is None

    def test_none_is_allowed(self):
        assert self._config(s3_file_max_rows=None).s3_file_max_rows is None

    @pytest.mark.parametrize('value', [1, 25000])
    def test_positive_values_are_allowed(self, value):
        assert self._config(s3_file_max_rows=value).s3_file_max_rows == value

    @pytest.mark.parametrize('value', [0, -1])
    def test_zero_and_negative_values_are_rejected(self, value):
        with pytest.raises(ValidationError, match='greater than zero'):
            self._config(s3_file_max_rows=value)


class _MinimalLoader(BulkLoader):
    def load_from_iterable(self, iterable, table_object, *args, **kwargs) -> int:
        return 0


class TestRedaction:
    def test_registered_value_is_masked_in_log(self, caplog):
        loader = _MinimalLoader()
        loader.add_redact_value('secret')

        with caplog.at_level(logging.INFO):
            loader.log_with_redactions(log_level=logging.INFO, message='password=secret;')

        assert 'password=******;' in caplog.text
        assert 'secret' not in caplog.text

    def test_none_is_ignored(self, caplog):
        loader = _MinimalLoader()
        loader.add_redact_value(None)

        with caplog.at_level(logging.INFO):
            loader.log_with_redactions(log_level=logging.INFO, message='nothing to hide')

        assert loader._redact_values == set()
        assert 'nothing to hide' in caplog.text
