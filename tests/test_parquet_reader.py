from pathlib import Path

import pyarrow
import pyarrow.dataset
import pyarrow.parquet
import pytest

from bi_etl.components.parquet_reader import ParquetReader
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
            'id': [1, 2, 3, 4],
            'name': ['Alice', 'Bob', 'Carol', None],
            'score': [1.5, 2.5, None, 4.5],
        }
    )


@pytest.fixture
def parquet_file(tmp_path: Path, sample_table: pyarrow.Table) -> Path:
    path = tmp_path / 'sample.parquet'
    pyarrow.parquet.write_table(sample_table, path)
    return path


@pytest.fixture
def hive_dir(tmp_path: Path, sample_table: pyarrow.Table) -> Path:
    path = tmp_path / 'hive'
    pyarrow.parquet.write_to_dataset(
        sample_table.append_column('region', pyarrow.array(['east', 'east', 'west', 'west'])),
        path,
        partition_cols=['region'],
    )
    return path


def test_is_pyarrow_dataset_reader(task, parquet_file):
    with ParquetReader(task, parquet_file) as src:
        assert isinstance(src, PyArrowDatasetReader)
        assert src.pyarrow_format == 'parquet'


def test_read_all_rows(task, parquet_file):
    with ParquetReader(task, parquet_file) as src:
        assert src.column_names == ['id', 'name', 'score']
        rows = list(src)
        assert src.rows_read == 4

    assert [row['id'] for row in rows] == [1, 2, 3, 4]
    assert [row['name'] for row in rows] == ['Alice', 'Bob', 'Carol', None]
    assert [row['score'] for row in rows] == [1.5, 2.5, None, 4.5]


def test_source_as_str(task, parquet_file):
    with ParquetReader(task, str(parquet_file)) as src:
        assert len(list(src)) == 4


def test_source_list_of_files(task, tmp_path, sample_table):
    paths = []
    for i in range(2):
        path = tmp_path / f'part_{i}.parquet'
        pyarrow.parquet.write_table(sample_table, path)
        paths.append(path)

    with ParquetReader(task, paths) as src:
        assert len(list(src)) == 8


def test_source_directory(task, tmp_path, sample_table):
    data_dir = tmp_path / 'dataset'
    data_dir.mkdir()
    for i in range(3):
        pyarrow.parquet.write_table(sample_table, data_dir / f'part_{i}.parquet')

    with ParquetReader(task, data_dir) as src:
        assert len(list(src)) == 12


def test_columns_projection(task, parquet_file):
    with ParquetReader(task, parquet_file, columns=['name', 'id']) as src:
        assert src.column_names == ['name', 'id']
        rows = list(src)

    assert rows[0].as_dict == {'name': 'Alice', 'id': 1}
    assert 'score' not in rows[0].as_dict


def test_columns_as_str_raises(task, parquet_file):
    with pytest.raises(TypeError):
        ParquetReader(task, parquet_file, columns='id')


def test_unknown_column_raises(task, parquet_file):
    src = ParquetReader(task, parquet_file, columns=['not_a_column'])
    with pytest.raises((KeyError, ValueError, pyarrow.ArrowInvalid)):
        _ = src.column_names
    src.close()


def test_filters_expression(task, parquet_file):
    expression = pyarrow.dataset.field('id') > 2
    with ParquetReader(task, parquet_file, filters=expression) as src:
        rows = list(src)

    assert [row['id'] for row in rows] == [3, 4]


def test_filters_dnf_and(task, parquet_file):
    with ParquetReader(task, parquet_file, filters=[('id', '>', 1), ('id', '<', 4)]) as src:
        rows = list(src)

    assert [row['id'] for row in rows] == [2, 3]


def test_filters_dnf_or(task, parquet_file):
    with ParquetReader(task, parquet_file, filters=[[('id', '=', 1)], [('name', 'in', ['Bob'])]]) as src:
        rows = list(src)

    assert [row['id'] for row in rows] == [1, 2]


def test_filter_on_column_not_projected(task, parquet_file):
    with ParquetReader(task, parquet_file, columns=['name'], filters=[('id', '=', 2)]) as src:
        rows = list(src)

    assert [row.as_dict for row in rows] == [{'name': 'Bob'}]


def test_filters_none_expression_property(task, parquet_file):
    with ParquetReader(task, parquet_file) as src:
        assert src.filter_expression is None


def test_where_combines_with_filters(task, parquet_file):
    with ParquetReader(task, parquet_file, filters=[('id', '>', 1)]) as src:
        rows = list(src.where(criteria_dict={'name': 'Alice'}))
        assert rows == []
        rows = list(src.where(criteria_dict={'name': 'Bob'}))

    assert [row['id'] for row in rows] == [2]


def test_where_none_and_list_values(task, parquet_file):
    with ParquetReader(task, parquet_file) as src:
        null_rows = list(src.where(criteria_dict={'name': None}))
        in_rows = list(src.where(criteria_dict={'id': [1, 3]}))
        multi_rows = list(src.where(criteria_dict={'id': [1, 2, 3], 'name': 'Carol'}))

    assert [row['id'] for row in null_rows] == [4]
    assert [row['id'] for row in in_rows] == [1, 3]
    assert [row['id'] for row in multi_rows] == [3]


def test_hive_partitioning_default(task, hive_dir):
    with ParquetReader(task, hive_dir) as src:
        assert 'region' in src.column_names
        rows = list(src.where(criteria_dict={'region': 'west'}))

    assert sorted(row['id'] for row in rows) == [3, 4]
    assert all(row['region'] == 'west' for row in rows)


def test_partitioning_disabled(task, hive_dir):
    with ParquetReader(task, hive_dir, partitioning=None) as src:
        assert 'region' not in src.column_names
        assert len(list(src)) == 4


def test_batch_size(task, tmp_path):
    table = pyarrow.table({'id': list(range(25))})
    path = tmp_path / 'batches.parquet'
    pyarrow.parquet.write_table(table, path)

    with ParquetReader(task, path, batch_size=7) as src:
        assert [row['id'] for row in src] == list(range(25))


@pytest.mark.parametrize('batch_size', [0, -1])
def test_invalid_batch_size_raises(task, parquet_file, batch_size):
    with pytest.raises(ValueError):
        ParquetReader(task, parquet_file, batch_size=batch_size)


def test_use_threads_false(task, parquet_file):
    with ParquetReader(task, parquet_file, use_threads=False) as src:
        assert len(list(src)) == 4


def test_explicit_schema(task, parquet_file):
    schema = pyarrow.schema(
        [
            pyarrow.field('id', pyarrow.int64()),
            pyarrow.field('name', pyarrow.string()),
            pyarrow.field('score', pyarrow.float64()),
            pyarrow.field('extra', pyarrow.string()),
        ]
    )
    with ParquetReader(task, parquet_file, schema=schema) as src:
        assert src.column_names == ['id', 'name', 'score', 'extra']
        assert all(row['extra'] is None for row in src)


def test_empty_file(task, tmp_path, sample_table):
    path = tmp_path / 'empty.parquet'
    pyarrow.parquet.write_table(sample_table.slice(0, 0), path)

    with ParquetReader(task, path) as src:
        assert src.column_names == ['id', 'name', 'score']
        assert list(src) == []


def test_max_rows(task, parquet_file):
    with ParquetReader(task, parquet_file, max_rows=2) as src:
        assert [row['id'] for row in src] == [1, 2]


def test_missing_source_raises(task, tmp_path):
    src = ParquetReader(task, tmp_path / 'does_not_exist.parquet')
    with pytest.raises(OSError):
        _ = src.column_names
    src.close()
