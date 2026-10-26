from pathlib import Path

import pyarrow
import pyarrow.csv
import pyarrow.parquet
import pytest

from bi_etl.components.pyarrow_dataset_reader import PyArrowDatasetReader
from bi_etl.scheduler.etl_task import ETLTask
from tests.config_for_tests import build_config


@pytest.fixture
def task() -> ETLTask:
    return ETLTask(config=build_config())


@pytest.fixture
def sample_table() -> pyarrow.Table:
    return pyarrow.table(
        {
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol'],
            'score': [1.5, 2.5, None],
        }
    )


@pytest.fixture
def parquet_file(tmp_path: Path, sample_table: pyarrow.Table) -> Path:
    path = tmp_path / 'sample.parquet'
    pyarrow.parquet.write_table(sample_table, path)
    return path


def test_column_names_from_parquet(task, parquet_file):
    with PyArrowDatasetReader(task, parquet_file, pyarrow_format='parquet') as src:
        assert src.column_names == ['id', 'name', 'score']


def test_iterate_parquet_rows(task, parquet_file):
    with PyArrowDatasetReader(task, parquet_file, pyarrow_format='parquet') as src:
        rows = list(src)
        assert src.rows_read == 3

    assert [row['id'] for row in rows] == [1, 2, 3]
    assert [row['name'] for row in rows] == ['Alice', 'Bob', 'Carol']
    assert [row['score'] for row in rows] == [1.5, 2.5, None]


def test_source_as_str(task, parquet_file):
    with PyArrowDatasetReader(task, str(parquet_file), pyarrow_format='parquet') as src:
        assert len(list(src)) == 3


def test_format_defaults_to_parquet(task, parquet_file):
    with PyArrowDatasetReader(task, parquet_file) as src:
        assert len(list(src)) == 3


def test_source_list_of_files(task, tmp_path, sample_table):
    paths = []
    for i in range(2):
        path = tmp_path / f'part_{i}.parquet'
        pyarrow.parquet.write_table(sample_table, path)
        paths.append(path)

    with PyArrowDatasetReader(task, paths, pyarrow_format='parquet') as src:
        rows = list(src)

    assert len(rows) == 6
    assert [row['id'] for row in rows] == [1, 2, 3, 1, 2, 3]


def test_source_directory(task, tmp_path, sample_table):
    data_dir = tmp_path / 'dataset'
    data_dir.mkdir()
    for i in range(3):
        pyarrow.parquet.write_table(sample_table, data_dir / f'part_{i}.parquet')

    with PyArrowDatasetReader(task, data_dir, pyarrow_format='parquet') as src:
        rows = list(src)

    assert len(rows) == 9


def test_csv_format(task, tmp_path, sample_table):
    path = tmp_path / 'sample.csv'
    pyarrow.csv.write_csv(sample_table, path)

    with PyArrowDatasetReader(task, path, pyarrow_format='csv') as src:
        assert src.column_names == ['id', 'name', 'score']
        rows = list(src)

    assert [row['name'] for row in rows] == ['Alice', 'Bob', 'Carol']
    assert [row['id'] for row in rows] == [1, 2, 3]


def test_explicit_schema_overrides_inference(task, parquet_file):
    schema = pyarrow.schema(
        [
            pyarrow.field('id', pyarrow.int64()),
            pyarrow.field('name', pyarrow.string()),
            pyarrow.field('score', pyarrow.float64()),
            pyarrow.field('extra', pyarrow.string()),
        ]
    )
    with PyArrowDatasetReader(task, parquet_file, schema=schema, pyarrow_format='parquet') as src:
        assert src.column_names == ['id', 'name', 'score', 'extra']
        rows = list(src)

    assert len(rows) == 3
    assert all(row['extra'] is None for row in rows)


def test_empty_dataset(task, tmp_path, sample_table):
    path = tmp_path / 'empty.parquet'
    pyarrow.parquet.write_table(sample_table.slice(0, 0), path)

    with PyArrowDatasetReader(task, path, pyarrow_format='parquet') as src:
        assert src.column_names == ['id', 'name', 'score']
        assert list(src) == []
        assert src.rows_read == 0


def test_multiple_record_batches(task, tmp_path):
    table = pyarrow.table({'id': list(range(25))})
    path = tmp_path / 'batches.parquet'
    pyarrow.parquet.write_table(table, path, row_group_size=10)

    with PyArrowDatasetReader(task, path, pyarrow_format='parquet') as src:
        rows = list(src)

    assert [row['id'] for row in rows] == list(range(25))


def test_where_criteria_dict(task, parquet_file):
    with PyArrowDatasetReader(task, parquet_file, pyarrow_format='parquet') as src:
        rows = list(src.where(criteria_dict={'name': 'Bob'}))

    assert len(rows) == 1
    assert rows[0]['id'] == 2


def test_where_criteria_dict_none_and_list(task, tmp_path):
    table = pyarrow.table({'id': [1, 2, 3], 'name': ['Alice', None, 'Carol']})
    path = tmp_path / 'nulls.parquet'
    pyarrow.parquet.write_table(table, path)

    with PyArrowDatasetReader(task, path, pyarrow_format='parquet') as src:
        assert [row['id'] for row in src.where(criteria_dict={'name': None})] == [2]
        assert [row['id'] for row in src.where(criteria_dict={'id': [1, 3]})] == [1, 3]


def test_batch_to_value_lists(sample_table):
    batch = sample_table.to_batches()[0]

    assert list(PyArrowDatasetReader._batch_to_value_lists(batch)) == [
        [1, 'Alice', 1.5],
        [2, 'Bob', 2.5],
        [3, 'Carol', None],
    ]


def test_batch_to_value_lists_keeps_duplicate_column_names():
    batch = pyarrow.record_batch([pyarrow.array([1, 2]), pyarrow.array([3, 4])], names=['a', 'a'])

    assert list(PyArrowDatasetReader._batch_to_value_lists(batch)) == [[1, 3], [2, 4]]


def test_batch_to_value_lists_no_columns():
    batch = pyarrow.table({'a': [1, 2, 3]}).select([]).to_batches()[0]

    assert list(PyArrowDatasetReader._batch_to_value_lists(batch)) == [[], [], []]


def test_rows_are_mutable(task, parquet_file):
    with PyArrowDatasetReader(task, parquet_file, pyarrow_format='parquet') as src:
        row = next(iter(src))
        row['id'] = 99
        row['new_column'] = 'x'

    assert row['id'] == 99
    assert row['new_column'] == 'x'


def test_max_rows(task, parquet_file):
    with PyArrowDatasetReader(task, parquet_file, pyarrow_format='parquet', max_rows=2) as src:
        rows = list(src)

    assert [row['id'] for row in rows] == [1, 2]


def test_kwargs_set_as_attributes(task, parquet_file):
    with PyArrowDatasetReader(
        task, parquet_file, pyarrow_format='parquet', log_first_row=False
    ) as src:
        assert src.log_first_row is False


def test_logical_name(task, parquet_file):
    with PyArrowDatasetReader(
        task, parquet_file, pyarrow_format='parquet', logical_name='my_source'
    ) as src:
        assert src.logical_name == 'my_source'


def test_missing_source_raises(task, tmp_path):
    src = PyArrowDatasetReader(task, tmp_path / 'does_not_exist.parquet', pyarrow_format='parquet')
    with pytest.raises(OSError):
        _ = src.column_names
    src.close()
