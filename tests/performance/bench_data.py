"""
Table definition and row generator shared by the benchmarks in this folder.

NOT a benchmark itself. The table has these columns:

===================  ===========  ====================================================================
Column               Type         Values
===================  ===========  ====================================================================
``id``               Integer      Unique key (primary key): the numbers 0 to rows-1 in random order.
``enum_a``           String       5 distinct values of 4 to 10 characters, skewed in frequency. 2% null.
``code_b``           String       3 distinct values of exactly 5 characters, equally frequent.
``enum_c``           String       10 distinct values of 6 to 20 characters, skewed in frequency.
``few_datetimes``    DateTime     8 distinct values, from 2000 to 2030. 2% null.
``random_float``     Float        Random, from -1e9 to 1e9. 2% null.
``small_int``        Integer      Random, 0 to 15. 2% null.
``random_datetime``  DateTime     Random whole seconds from 1900 to 2030.
``free_text``        String       Sentences of made-up words with punctuation and special characters,
                                  5 to 100 characters long. See :func:`_free_text`.
``decimal_amount``   Numeric      Random decimal(12,2), the full range of the type.
``random_date``      Date         Random day from 1900 to 2030.
===================  ===========  ====================================================================

The skewed columns pick their values with Zipf weights: the n-th most frequent value has 1/n the weight of the
most frequent one. The nulls are exactly :data:`NULL_FRACTION` of the rows, in random positions.

The words of ``free_text`` come from a random vocabulary of :data:`VOCABULARY_SIZE` made-up words, picked with
Zipf weights as real text does: a few words are very common and most are rare.

Every column is generated from its own random generator, seeded from the seed and the column name, so every run
(and every benchmark) sees the same data and a column does not change when other columns are added.
Datetimes are whole seconds so that they survive every file format unchanged.

A *column multiplier* of N repeats all columns except ``id`` N times in total, to make the table wider.
The repeats are named like the original with ``_2``, ``_3``... added, and have their own values.
"""
import itertools
import random
import string
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Callable

from sqlalchemy import Column, Date, DateTime, Float, Integer, Numeric, String
from sqlalchemy.types import TypeEngine

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader

DEFAULT_SEED = 1234
NULL_FRACTION = 0.02
ALPHANUMERIC = string.ascii_letters + string.digits
VOCABULARY_SIZE = 2000
COMMON_WORD_COUNT = 20
# Lengths 2 to 12, with short words the most common
WORD_LENGTH_WEIGHTS = [8, 14, 16, 15, 12, 10, 8, 6, 4, 3, 2]
WORD_MIN_LENGTH = 2
SENTENCE_MIN_WORDS = 4
SENTENCE_MAX_WORDS = 16
SPECIAL_CHARACTERS = '@#$%^&*+=<>/\\'
FREE_TEXT_MIN_LENGTH = 5
FREE_TEXT_MAX_LENGTH = 100
MIN_DATETIME = datetime(1900, 1, 1)
MAX_DATETIME = datetime(2030, 12, 31, 23, 59, 59)
MIN_FEW_DATETIME = datetime(2000, 1, 1)
FLOAT_LIMIT = 1e9
SMALL_INT_MAX = 15
DECIMAL_PRECISION = 12
DECIMAL_SCALE = 2
# Largest value of a decimal(12,2) with the decimal point removed
DECIMAL_MAX_UNSCALED = 10 ** DECIMAL_PRECISION - 1


@dataclass
class BenchColumn:
    """The parts of a column that the loaders read, see :class:`BenchTable`."""
    name: str
    type: TypeEngine
    primary_key: bool = False


@dataclass
class BenchTable:
    """
    The parts of a :class:`~bi_etl.components.table.Table` that the bulk loaders read.

    Attributes
    ----------
    qualified_table_name
        Schema qualified name of the table.
    columns
        The columns, in order.
    """
    qualified_table_name: str
    columns: list[BenchColumn]

    @property
    def column_names(self) -> list[str]:
        """Names of the columns, in order."""
        return [column.name for column in self.columns]

    @staticmethod
    def _get_python_type(sql_type: TypeEngine) -> type:
        """Return the Python type of a SQLAlchemy type, as :meth:`bi_etl.components.table.Table._get_python_type`."""
        return sql_type.python_type


ValueMaker = Callable[[random.Random, int], list]


@dataclass(frozen=True)
class ColumnSpec:
    """
    How to create a column and its values.

    Attributes
    ----------
    column
        The column.
    make_values
        Function of a random generator and a row count that returns that many values, before nulls are added.
    null_fraction
        Fraction of the values to replace with None.
    """
    column: BenchColumn
    make_values: ValueMaker
    null_fraction: float = 0.0


def _distinct_strings(rng: random.Random, count: int, min_length: int, max_length: int) -> list[str]:
    """Return *count* different random alphanumeric strings with lengths from *min_length* to *max_length*."""
    values: dict[str, None] = {}
    while len(values) < count:
        values[''.join(rng.choices(ALPHANUMERIC, k=rng.randint(min_length, max_length)))] = None
    return list(values)


def _random_datetime(rng: random.Random, low: datetime, high: datetime) -> datetime:
    """Return a random whole second between *low* and *high*."""
    return low + timedelta(seconds=rng.randint(0, int((high - low).total_seconds())))


def _distinct_datetimes(rng: random.Random, count: int, low: datetime, high: datetime) -> list[datetime]:
    """Return *count* different random datetimes between *low* and *high*."""
    values: dict[datetime, None] = {}
    while len(values) < count:
        values[_random_datetime(rng, low, high)] = None
    return list(values)


def _zipf_weights(count: int) -> list[float]:
    """Return weights 1, 1/2, 1/3... for *count* values."""
    return [1 / rank for rank in range(1, count + 1)]


def _unique_key(rng: random.Random, count: int) -> list[int]:
    """Return the numbers 0 to *count* - 1 in random order."""
    values = list(range(count))
    rng.shuffle(values)
    return values


def _strings_of_distinct_values(
        distinct: int,
        min_length: int,
        max_length: int,
        skewed: bool,
) -> ValueMaker:
    """Return a value maker that picks from *distinct* random strings, uniformly or with Zipf weights."""
    def make(rng: random.Random, count: int) -> list[str]:
        values = _distinct_strings(rng, distinct, min_length, max_length)
        return rng.choices(values, weights=_zipf_weights(distinct) if skewed else None, k=count)

    return make


def _few_datetimes(rng: random.Random, count: int) -> list[datetime]:
    """Return *count* values picked equally often from 8 random datetimes."""
    return rng.choices(_distinct_datetimes(rng, 8, MIN_FEW_DATETIME, MAX_DATETIME), k=count)


def _random_float(rng: random.Random, count: int) -> list[float]:
    """Return *count* random floats."""
    return [rng.uniform(-FLOAT_LIMIT, FLOAT_LIMIT) for _ in range(count)]


def _small_int(rng: random.Random, count: int) -> list[int]:
    """Return *count* random integers from 0 to :data:`SMALL_INT_MAX`."""
    return [rng.randint(0, SMALL_INT_MAX) for _ in range(count)]


def _random_datetimes(rng: random.Random, count: int) -> list[datetime]:
    """Return *count* random datetimes from :data:`MIN_DATETIME` to :data:`MAX_DATETIME`."""
    return [_random_datetime(rng, MIN_DATETIME, MAX_DATETIME) for _ in range(count)]


def _make_vocabulary(rng: random.Random) -> list[str]:
    """
    Return :data:`VOCABULARY_SIZE` different made-up lowercase words, most common first.

    As in real text, the :data:`COMMON_WORD_COUNT` most common words are short (2 to 4 characters).
    The other words have the lengths of :data:`WORD_LENGTH_WEIGHTS`.
    """
    lengths = range(WORD_MIN_LENGTH, WORD_MIN_LENGTH + len(WORD_LENGTH_WEIGHTS))
    words: dict[str, None] = {}
    while len(words) < VOCABULARY_SIZE:
        if len(words) < COMMON_WORD_COUNT:
            length = rng.choices([2, 3, 4], weights=[3, 5, 3])[0]
        else:
            length = rng.choices(lengths, weights=WORD_LENGTH_WEIGHTS)[0]
        words[''.join(rng.choices(string.ascii_lowercase, k=length))] = None
    return list(words)


def _decorate_word(rng: random.Random, word: str) -> str:
    """
    Return *word*, usually unchanged, but sometimes as a number, with an apostrophe or hyphen inside it,
    in quotes or parentheses, or with a special character.
    """
    r = rng.random()
    if r < 0.03:
        return str(rng.randint(0, 99999))
    if r < 0.05:
        split = rng.randrange(1, len(word))
        return f"{word[:split]}'{word[split:]}"
    if r < 0.06:
        split = rng.randrange(1, len(word))
        return f'{word[:split]}-{word[split:]}'
    if r < 0.09:
        return f'"{word}"'
    if r < 0.11:
        return f"'{word}'"
    if r < 0.125:
        return f'({word})'
    if r < 0.14:
        return rng.choice(SPECIAL_CHARACTERS) + word
    if r < 0.145:
        return rng.choice(SPECIAL_CHARACTERS)
    return word


def _make_text(rng: random.Random, vocabulary: list[str], cum_weights: list[float], target_length: int) -> str:
    """
    Return sentences of words from *vocabulary* that are at most *target_length* characters long
    (but at least :data:`FREE_TEXT_MIN_LENGTH`).

    Sentences are :data:`SENTENCE_MIN_WORDS` to :data:`SENTENCE_MAX_WORDS` words long, start with a capital
    and end with ``.``, ``!`` or ``?``. Words are followed by ``,``, ``;`` or ``:`` now and then.
    """
    # Every word takes at least 2 characters with its space, so this is enough words to reach the length
    words = rng.choices(vocabulary, cum_weights=cum_weights, k=target_length // 2 + 1)
    parts: list[str] = []
    length = 0
    capitalize = True
    words_left = rng.randint(SENTENCE_MIN_WORDS, SENTENCE_MAX_WORDS)
    for word in words:
        piece = _decorate_word(rng, word)
        if capitalize:
            piece = piece[0].upper() + piece[1:]
            capitalize = False
        words_left -= 1
        if words_left == 0:
            piece += rng.choices('.!?', weights=[85, 7, 8])[0]
            capitalize = True
            words_left = rng.randint(SENTENCE_MIN_WORDS, SENTENCE_MAX_WORDS)
        else:
            r = rng.random()
            if r < 0.08:
                piece += ','
            elif r < 0.09:
                piece += ';'
            elif r < 0.10:
                piece += ':'
        added = len(piece) + (1 if parts else 0)
        if length + added > target_length and length >= FREE_TEXT_MIN_LENGTH:
            break
        parts.append(piece)
        length += added
    text = ' '.join(parts)
    if text[-1] in ',;:':
        text = text[:-1] + '.'
    return text


def _free_text(rng: random.Random, count: int) -> list[str]:
    """
    Return *count* texts of 5 to 100 characters that look like sentences, made of random words that are not real.

    The words are picked with Zipf weights from a vocabulary of :data:`VOCABULARY_SIZE` words,
    see :func:`_make_text` and :func:`_decorate_word` for the punctuation and special characters.
    """
    vocabulary = _make_vocabulary(rng)
    cum_weights = list(itertools.accumulate(_zipf_weights(len(vocabulary))))
    return [
        _make_text(rng, vocabulary, cum_weights, rng.randint(FREE_TEXT_MIN_LENGTH, FREE_TEXT_MAX_LENGTH))
        for _ in range(count)
    ]


def _decimal_amounts(rng: random.Random, count: int) -> list[Decimal]:
    """Return *count* random decimal(12,2) values."""
    return [
        Decimal(rng.randint(-DECIMAL_MAX_UNSCALED, DECIMAL_MAX_UNSCALED)).scaleb(-DECIMAL_SCALE)
        for _ in range(count)
    ]


def _random_dates(rng: random.Random, count: int) -> list[date]:
    """Return *count* random dates from :data:`MIN_DATETIME` to :data:`MAX_DATETIME`."""
    days = (MAX_DATETIME - MIN_DATETIME).days
    return [(MIN_DATETIME + timedelta(days=rng.randint(0, days))).date() for _ in range(count)]


# The first column is the unique key, which is not repeated by the column multiplier
BASE_SPECS = [
    ColumnSpec(BenchColumn('id', Integer(), primary_key=True), _unique_key),
    ColumnSpec(BenchColumn('enum_a', String()), _strings_of_distinct_values(5, 4, 10, skewed=True), NULL_FRACTION),
    ColumnSpec(BenchColumn('code_b', String()), _strings_of_distinct_values(3, 5, 5, skewed=False)),
    ColumnSpec(BenchColumn('enum_c', String()), _strings_of_distinct_values(10, 6, 20, skewed=True)),
    ColumnSpec(BenchColumn('few_datetimes', DateTime()), _few_datetimes, NULL_FRACTION),
    ColumnSpec(BenchColumn('random_float', Float()), _random_float, NULL_FRACTION),
    ColumnSpec(BenchColumn('small_int', Integer()), _small_int, NULL_FRACTION),
    ColumnSpec(BenchColumn('random_datetime', DateTime()), _random_datetimes),
    ColumnSpec(BenchColumn('free_text', String()), _free_text),
    ColumnSpec(BenchColumn('decimal_amount', Numeric(DECIMAL_PRECISION, DECIMAL_SCALE)), _decimal_amounts),
    ColumnSpec(BenchColumn('random_date', Date()), _random_dates),
]


def column_specs(column_multiplier: int = 1) -> list[ColumnSpec]:
    """
    Return the specs of the columns of the table.

    Parameters
    ----------
    column_multiplier
        Number of times to repeat all of the columns except the unique key. See the module description.

    Raises
    ------
    ValueError
        If *column_multiplier* is less than 1.
    """
    if column_multiplier < 1:
        raise ValueError(f'column_multiplier must be at least 1, got {column_multiplier}')
    specs = list(BASE_SPECS)
    for copy in range(2, column_multiplier + 1):
        for spec in BASE_SPECS[1:]:
            column = BenchColumn(f'{spec.column.name}_{copy}', spec.column.type)
            specs.append(ColumnSpec(column, spec.make_values, spec.null_fraction))
    return specs


COLUMN_NAMES = [spec.column.name for spec in column_specs()]


def build_table(qualified_table_name: str = 'bench_schema.bench_table', column_multiplier: int = 1) -> BenchTable:
    """
    Return a table-like object with the columns of the table.

    Parameters
    ----------
    qualified_table_name
        Name of the table.
    column_multiplier
        See :func:`column_specs`.
    """
    return BenchTable(qualified_table_name, [spec.column for spec in column_specs(column_multiplier)])


def sqlalchemy_columns(column_multiplier: int = 1) -> list[Column]:
    """
    Return new SQLAlchemy columns for creating a real table with the columns of the table.

    Parameters
    ----------
    column_multiplier
        See :func:`column_specs`.
    """
    return [
        Column(spec.column.name, spec.column.type, primary_key=spec.column.primary_key)
        for spec in column_specs(column_multiplier)
    ]


def make_columns(count: int, seed: int = DEFAULT_SEED, column_multiplier: int = 1) -> dict[str, list]:
    """
    Generate the data for *count* rows of :func:`build_table` as one list of values per column.

    Parameters
    ----------
    count
        Number of rows.
    seed
        Seed for the random generators, so that every run sees the same data.
    column_multiplier
        See :func:`column_specs`.

    Returns
    -------
    dict
        Column name to list of values, in column order.
    """
    columns = {}
    for spec in column_specs(column_multiplier):
        name = spec.column.name
        # A string seed is hashed in a way that does not vary between runs, unlike hash()
        rng = random.Random(f'{seed}/{name}')
        values = spec.make_values(rng, count)
        for index in rng.sample(range(count), round(count * spec.null_fraction)):
            values[index] = None
        columns[name] = values
    return columns


def make_value_lists(count: int, seed: int = DEFAULT_SEED, column_multiplier: int = 1) -> list[list]:
    """
    Generate the data for *count* rows of :func:`build_table`.

    Parameters
    ----------
    count
        Number of rows.
    seed
        Seed for the random generators, so that every run sees the same data.
    column_multiplier
        See :func:`column_specs`.

    Returns
    -------
    list of list
        One list of values per row, in column order. See the module description for the values.
    """
    return [list(values) for values in zip(*make_columns(count, seed, column_multiplier).values())]


def make_rows(count: int, seed: int = DEFAULT_SEED, column_multiplier: int = 1) -> list[Row]:
    """
    Generate *count* rows of :func:`build_table` as the :class:`~bi_etl.components.row.row.Row` objects that
    :class:`~bi_etl.components.table.Table` gives to the bulk loaders.

    Parameters
    ----------
    count
        Number of rows.
    seed
        Seed for the random generators, so that every run sees the same data.
    column_multiplier
        See :func:`column_specs`.

    Returns
    -------
    list of Row
        The values of :func:`make_value_lists`, all sharing one
        :class:`~bi_etl.components.row.row_iteration_header.RowIterationHeader`.
    """
    header = RowIterationHeader(columns_in_order=[spec.column.name for spec in column_specs(column_multiplier)])
    rows = []
    for values in make_value_lists(count, seed, column_multiplier):
        row = Row(header)
        row.update_from_values(values)
        rows.append(row)
    return rows
