"""
Benchmark of the ways to turn pyarrow record batches into Python rows, as done by
:class:`~bi_etl.components.pyarrow_dataset_reader.PyArrowDatasetReader`.

NOT part of the regular pytest suite (the file name does not match ``test*.py``).
Requires :mod:`pandas` (not a bi_etl dependency). Run from ``packages/bi_etl``::

    uv run python -m tests.performance.bench_parquet_row_conversion
    uv run python -m tests.performance.bench_parquet_row_conversion --rows 2000000 --repeats 5
    uv run python -m tests.performance.bench_parquet_row_conversion --batch-sizes 1000 10000 131072
    uv run python -m tests.performance.bench_parquet_row_conversion --include-read

The strategies compared (each is a generator of rows from one :class:`pyarrow.RecordBatch`):

``to_pylist``
    ``batch.to_pylist()``: a list of ``dict`` per batch. This is what the reader uses today.
``to_pandas+itertuples``
    ``batch.to_pandas().itertuples(index=False, name=None)``: a plain ``tuple`` per row.
``to_pydict+zip``
    ``zip(*batch.to_pydict().values())``: a plain ``tuple`` per row, without pandas. Not one of the
    originally requested strategies; included because it is the obvious non-pandas tuple alternative.

Note that the tuple strategies do not carry the column names with each row, while ``to_pylist`` does.
A consumer that needs a ``dict`` or :class:`~bi_etl.components.row.row.Row` has to add the names back
(``zip(columns, row)``), which is not measured here.

The table has an integer id, a float, a date and nine string columns of 3 to 15 random characters,
some of the strings are null. The data is written to a real Parquet file and read back with
:meth:`pyarrow.dataset.Dataset.scanner`. By default the record batches are read before the clock starts so that
only the conversion and iteration is timed. Use ``--include-read`` to time the file read as well.

Validation
----------
Before any timing, every strategy is run once and **every** row is compared with the generated data.
Each timed run additionally checks the row count and a sample of rows (first, last, and random ones).
Any mismatch raises :class:`AssertionError`. Values are normalized before comparing because pandas turns
integer, float and null values into numpy scalars and ``NaN``: see :func:`normalize`.
"""
import argparse
import datetime
import gc
import logging
import math
import random
import statistics
import string
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence

import pyarrow as pa
import pyarrow.dataset
import pyarrow.parquet as pq

STRING_COLUMN_COUNT = 9
MIN_STRING_LENGTH = 3
MAX_STRING_LENGTH = 15
NULL_EVERY = 7
BASE_DATE = datetime.date(2020, 1, 1)
DEFAULT_PYARROW_BATCH_SIZE = 131_072
SAMPLE_COUNT = 20

COLUMN_NAMES = ['id', 'amount', 'day'] + [f'str_{i}' for i in range(1, STRING_COLUMN_COUNT + 1)]

RowTuple = tuple
RowSource = Callable[[], Iterable[pa.RecordBatch]]
Strategy = Callable[[pa.RecordBatch], Iterator]


def make_columns(count: int, seed: int = 1234) -> dict[str, list]:
    """
    Generate the column data for the benchmark table.

    Parameters
    ----------
    count
        Number of rows.
    seed
        Seed for the random generator, so that every run sees the same data.

    Returns
    -------
    dict
        Column name to list of values, in :data:`COLUMN_NAMES` order. ``id`` is the row number,
        ``amount`` is ``id * 0.25``, ``day`` cycles through 365 days, and every :data:`NULL_EVERY` th value
        of ``str_1`` is None.
    """
    rng = random.Random(seed)
    alphabet = string.ascii_letters + string.digits
    columns: dict[str, list] = {
        'id': list(range(count)),
        'amount': [i * 0.25 for i in range(count)],
        'day': [BASE_DATE + datetime.timedelta(days=i % 365) for i in range(count)],
    }
    for n in range(1, STRING_COLUMN_COUNT + 1):
        columns[f'str_{n}'] = [
            ''.join(rng.choices(alphabet, k=rng.randint(MIN_STRING_LENGTH, MAX_STRING_LENGTH)))
            for _ in range(count)
        ]
    columns['str_1'] = [None if i % NULL_EVERY == 0 else v for i, v in enumerate(columns['str_1'])]
    return columns


def write_parquet(columns: dict[str, list], path: Path, row_group_size: int = 100_000) -> None:
    """
    Write *columns* to a Parquet file.

    Parameters
    ----------
    columns
        See :func:`make_columns`.
    path
        File to create.
    row_group_size
        Rows per row group.
    """
    table = pa.table(
        {
            name: pa.array(values, type=pa.date32()) if name == 'day' else pa.array(values)
            for name, values in columns.items()
        }
    )
    pq.write_table(table, path, row_group_size=row_group_size)


def normalize(value):
    """
    Convert a value from any strategy to the plain Python value that ``to_pylist`` produces.

    pandas returns numpy scalars, ``pandas.Timestamp`` for dates and ``NaN`` or ``None`` for nulls.

    Parameters
    ----------
    value
        A single cell value.

    Returns
    -------
    object
        None for any null, otherwise a plain Python ``int``, ``float``, ``str`` or :class:`datetime.date`.
    """
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, 'to_pydatetime'):  # pandas.Timestamp (and NaT, which is falsy for isnull)
        return None if value != value else value.date()
    if hasattr(value, 'item'):  # numpy scalar
        return normalize(value.item())
    return value


def to_tuple(row, columns: Sequence[str] = COLUMN_NAMES) -> RowTuple:
    """
    Convert a row from any strategy (``dict`` or ``tuple``) to a tuple of normalized values.

    Parameters
    ----------
    row
        Row as produced by a :data:`Strategy`.
    columns
        Column names in tuple order. Used to order the values when *row* is a dict.

    Returns
    -------
    tuple
    """
    if isinstance(row, dict):
        return tuple(normalize(row[c]) for c in columns)
    return tuple(normalize(v) for v in row)


def strategy_to_pylist(batch: pa.RecordBatch) -> Iterator[dict]:
    """Rows as ``dict`` using :meth:`pyarrow.RecordBatch.to_pylist`."""
    yield from batch.to_pylist()


def strategy_pandas_itertuples(batch: pa.RecordBatch) -> Iterator[tuple]:
    """Rows as ``tuple`` using :meth:`pyarrow.RecordBatch.to_pandas` then ``DataFrame.itertuples``."""
    yield from batch.to_pandas().itertuples(index=False, name=None)


def strategy_pydict_zip(batch: pa.RecordBatch) -> Iterator[tuple]:
    """Rows as ``tuple`` using :meth:`pyarrow.RecordBatch.to_pydict` and ``zip``."""
    yield from zip(*batch.to_pydict().values())


STRATEGIES: dict[str, Strategy] = {
    'to_pylist': strategy_to_pylist,
    'to_pandas+itertuples': strategy_pandas_itertuples,
    'to_pydict+zip': strategy_pydict_zip,
}


def build_row_source(path: Path, batch_size: int, include_read: bool) -> RowSource:
    """
    Build the callable that supplies the record batches for a run.

    Parameters
    ----------
    path
        Parquet file to read.
    batch_size
        Maximum rows per record batch.
    include_read
        If True each call re-reads the file, so the read is inside the timing.
        If False the batches are read once now and every call returns the same list.

    Returns
    -------
    callable
        Zero argument callable returning an iterable of :class:`pyarrow.RecordBatch`.
    """
    dataset = pyarrow.dataset.dataset(path, format='parquet')

    def read() -> Iterable[pa.RecordBatch]:
        return dataset.scanner(batch_size=batch_size, use_threads=True).to_batches()

    if include_read:
        return read
    batches = list(read())
    return lambda: batches


def pick_sample_indexes(count: int, seed: int = 99) -> list[int]:
    """
    Choose the row positions that every timed run checks: the first, the last and random ones.

    Parameters
    ----------
    count
        Number of rows in the table.
    seed
        Seed for the random generator.

    Returns
    -------
    list of int
        Sorted, unique row positions.
    """
    rng = random.Random(seed)
    picks = {0, count - 1}
    picks.update(rng.randrange(count) for _ in range(min(SAMPLE_COUNT, count)))
    return sorted(picks)


def expected_row(columns: dict[str, list], index: int) -> RowTuple:
    """Return row *index* of the generated data as a tuple in :data:`COLUMN_NAMES` order."""
    return tuple(columns[c][index] for c in COLUMN_NAMES)


def consume(
        strategy: Strategy,
        get_batches: RowSource,
        sample_indexes: Sequence[int],
) -> tuple[int, dict[int, object]]:
    """
    Run *strategy* over every batch, counting rows and keeping the sampled rows. This is the timed work.

    Parameters
    ----------
    strategy
        Row conversion strategy.
    get_batches
        Supplies the record batches.
    sample_indexes
        Row positions to keep.

    Returns
    -------
    tuple
        The number of rows seen, and a dict of sampled row position to the (un-normalized) row.
    """
    wanted = set(sample_indexes)
    samples: dict[int, object] = {}
    count = 0
    for batch in get_batches():
        for row in strategy(batch):
            if count in wanted:
                samples[count] = row
            count += 1
    return count, samples


def check_samples(
        name: str,
        count: int,
        samples: dict[int, object],
        columns: dict[str, list],
        expected_count: int,
        sample_indexes: Sequence[int],
) -> None:
    """
    Validate the row count and the sampled rows of one run.

    Parameters
    ----------
    name
        Strategy name, for the error message.
    count
        Rows returned by the strategy.
    samples
        Sampled row position to row, from :func:`consume`.
    columns
        The generated data, see :func:`make_columns`.
    expected_count
        Number of rows that should have been returned.
    sample_indexes
        The row positions that should be in *samples*.

    Raises
    ------
    AssertionError
        If the count is wrong, a sample is missing, or a sampled row's values are wrong.
    """
    if count != expected_count:
        raise AssertionError(f'{name}: returned {count:,} rows, expected {expected_count:,}')
    for index in sample_indexes:
        if index not in samples:
            raise AssertionError(f'{name}: sample row {index:,} was not returned')
        actual = to_tuple(samples[index])
        expected = expected_row(columns, index)
        if actual != expected:
            raise AssertionError(f'{name}: row {index:,} is {actual!r}, expected {expected!r}')


def validate_all_rows(
        name: str,
        strategy: Strategy,
        get_batches: RowSource,
        columns: dict[str, list],
) -> None:
    """
    Compare **every** row returned by *strategy* with the generated data, in order. Not timed.

    Parameters
    ----------
    name
        Strategy name, for the error message.
    strategy
        Row conversion strategy.
    get_batches
        Supplies the record batches.
    columns
        The generated data, see :func:`make_columns`.

    Raises
    ------
    AssertionError
        On the first row that differs, or if the row count differs.
    """
    expected_rows = zip(*(columns[c] for c in COLUMN_NAMES))
    count = 0
    for batch in get_batches():
        for row in strategy(batch):
            expected = next(expected_rows, None)
            if expected is None:
                raise AssertionError(f'{name}: returned more than the {len(columns["id"]):,} rows expected')
            actual = to_tuple(row)
            if actual != expected:
                raise AssertionError(f'{name}: row {count:,} is {actual!r}, expected {expected!r}')
            count += 1
    if count != len(columns['id']):
        raise AssertionError(f'{name}: returned {count:,} rows, expected {len(columns["id"]):,}')


@dataclass
class Result:
    """Timings of one strategy at one batch size. All times are in seconds."""
    strategy: str
    batch_size: int
    rows: int
    times: list[float]

    @property
    def median(self) -> float:
        """Median elapsed time of the runs."""
        return statistics.median(self.times)

    @property
    def stdev(self) -> float:
        """Standard deviation of the elapsed times (0 for a single run)."""
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0

    @property
    def rows_per_second(self) -> float:
        """Rows per second at the median time."""
        return self.rows / self.median


def run_strategy(
        name: str,
        strategy: Strategy,
        get_batches: RowSource,
        columns: dict[str, list],
        sample_indexes: Sequence[int],
        batch_size: int,
        repeats: int,
) -> Result:
    """
    Time *strategy* *repeats* times, validating the row count and sample rows of every run.

    Parameters
    ----------
    name
        Strategy name.
    strategy
        Row conversion strategy.
    get_batches
        Supplies the record batches.
    columns
        The generated data, see :func:`make_columns`.
    sample_indexes
        Row positions to validate.
    batch_size
        Batch size, only recorded in the result.
    repeats
        Number of timed runs.

    Returns
    -------
    Result

    Raises
    ------
    AssertionError
        If any run returns the wrong rows.
    """
    expected_count = len(columns['id'])
    times = []
    for _ in range(repeats):
        gc.collect()
        start = time.perf_counter()
        count, samples = consume(strategy, get_batches, sample_indexes)
        times.append(time.perf_counter() - start)
        check_samples(name, count, samples, columns, expected_count, sample_indexes)
    return Result(name, batch_size, expected_count, times)


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print *rows* as a table with right aligned columns, except the first two."""
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]

    def fmt(cells):
        return '  '.join(c.ljust(widths[i]) if i < 2 else c.rjust(widths[i]) for i, c in enumerate(cells))

    print(fmt(headers))
    print('  '.join('-' * w for w in widths))
    for r in rows:
        print(fmt(r))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--rows', type=int, default=500_000,
        help='Rows in the table (default 500,000)'
        )
    parser.add_argument(
        '--batch-sizes', nargs='+', type=int, default=[10_000, DEFAULT_PYARROW_BATCH_SIZE],
        help='Maximum rows per record batch to try (default 10,000 and the pyarrow default 131,072)',
    )
    parser.add_argument('--repeats', type=int, default=5, help='Timed runs per strategy; the median is reported')
    parser.add_argument(
        '--include-read', action='store_true',
        help='Read the Parquet file inside the timing (default reads the batches before the clock starts)',
    )
    args = parser.parse_args()
    if args.rows < 1:
        parser.error('--rows must be at least 1')
    if args.repeats < 1:
        parser.error('--repeats must be at least 1')
    if any(size < 1 for size in args.batch_sizes):
        parser.error('--batch-sizes must all be at least 1')

    logging.disable(logging.CRITICAL)
    print(f'Generating {args.rows:,} rows...')
    columns = make_columns(args.rows)
    sample_indexes = pick_sample_indexes(args.rows)

    results: list[Result] = []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'bench.parquet'
        write_parquet(columns, path)
        for batch_size in args.batch_sizes:
            get_batches = build_row_source(path, batch_size, args.include_read)
            print(f'\nBatch size {batch_size:,}: validating every row of each strategy...')
            for name, strategy in STRATEGIES.items():
                validate_all_rows(name, strategy, get_batches, columns)
                print(f'  {name}: all {args.rows:,} rows OK')
            for name, strategy in STRATEGIES.items():
                result = run_strategy(
                    name, strategy, get_batches, columns, sample_indexes, batch_size, args.repeats
                )
                results.append(result)
                print(f'  {name:<22} {result.median:.3f}s', flush=True)

    print(
        f'\n{args.rows:,} rows, {args.repeats} run(s) each, median reported'
        f'{", including file read" if args.include_read else ""}\n'
        )
    rows = []
    for batch_size in args.batch_sizes:
        group = [r for r in results if r.batch_size == batch_size]
        fastest = min(r.median for r in group)
        for r in group:
            rows.append(
                [
                    f'{r.batch_size:,}', r.strategy, f'{r.median:.3f}', f'{r.stdev:.3f}',
                    f'{r.rows_per_second:,.0f}', f'{r.median / fastest - 1:+.1%}',
                ]
            )
    print_table(['batch_size', 'strategy', 'median s', 'stdev s', 'rows/s', 'vs fastest'], rows)


if __name__ == '__main__':
    main()
