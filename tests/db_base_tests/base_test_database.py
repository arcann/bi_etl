import inspect
import logging
import math
import random
import string
import typing
import unittest
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Union, Optional

import sqlalchemy
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase
from sqlalchemy.exc import NoSuchModuleError
from sqlalchemy.sql.ddl import CreateTable
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import BOOLEAN
from sqlalchemy.sql.sqltypes import Date
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.sqltypes import Interval
from sqlalchemy.sql.sqltypes import REAL
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql.sqltypes import Time

from bi_etl.components.readonlytable import ReadOnlyTable
from bi_etl.components.row.row import Row
from bi_etl.conversions import str2date, str2datetime
from bi_etl.database import DatabaseMetadata
from bi_etl.scheduler.task import ETLTask
from tests.config_for_tests import build_config
from tests.dummy_etl_component import DummyETLComponent


class BaseTestDatabase(unittest.TestCase):
    db_container = None
    TABLE_PREFIX = ''
    TABLE_VALID_CHARS = string.ascii_lowercase + string.digits

    class ApproxDatetime(object):
        def __init__(self, expected_dt: datetime, interval: timedelta = None):
            self.expected_dt = expected_dt
            self.interval = interval or timedelta(minutes=2)

        def matches(self, other_dt):
            if (self.expected_dt - self.interval) <= other_dt <= (self.expected_dt + self.interval):
                return True
            else:
                return False

        def __str__(self):
            return f"{self.expected_dt} +/- {self.interval}"

    @classmethod
    def setUpClass(cls) -> None:
        logging.basicConfig(level=logging.DEBUG, format='%(name)s %(levelname)s %(message)s')
        bi_etl_log = logging.getLogger('bi_etl')
        bi_etl_log.setLevel(logging.DEBUG)
        if cls.__name__.startswith('Base'):
            raise ValueError(
                f"{cls} is a base and not a testable class. "
                f"Use pytest config or `del BaseTestTable` to avoid loading this as a test."
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_container.shutdown()

    @staticmethod
    def get_package_path() -> Path:
        module_path = Path(inspect.getfile(BaseTestDatabase))
        return module_path.parents[1]

    @staticmethod
    def make_short_table_name(full_name: str, max_length: int) -> str:
        name_hash = hash(full_name)
        short_name_list = ['t']
        base = len(BaseTestDatabase.TABLE_VALID_CHARS)
        while name_hash != 0 and len(short_name_list) < max_length:
            char_number = name_hash % base
            short_name_list.append(BaseTestDatabase.TABLE_VALID_CHARS[char_number])
            name_hash //= base
        return ''.join(short_name_list)

    def get_test_file_path(self, file_name: str) -> Path:
        # Search the folders from the last added to first added
        # since the last added is the child class that might override a test file
        for folder in reversed(self.test_file_search_folders):
            path = self.get_package_path() / folder / file_name
            if path.exists():
                return path
        raise FileNotFoundError(f"{file_name} not found in folders {self.test_file_search_folders}")

    def setUp(self):
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        self.tmp = TemporaryDirectory()
        database_name = 'test_db'
        db_config = SQLAlchemyDatabase(
            dialect='sqlite',
            database_name=database_name,
            host='local',
            user_id='sqlite',
        )
        self.config = build_config(db_config=db_config, tmp=self.tmp)
        self.task = ETLTask(config=self.config)
        self.dummy_etl_component = DummyETLComponent(task=self.task)
        try:
            engine = self.db_container.create_engine()
        except NoSuchModuleError as e:
            raise unittest.SkipTest(repr(e))
        self.engine = engine
        self.log.info(f"Using DB connection {engine}")

        self.mock_database = self._get_mock_db()
        self.test_file_search_folders = []

    def tearDown(self):
        self.mock_database.dispose()
        self.tmp.cleanup()

    def _get_mock_db(self):
        return DatabaseMetadata(
            bind=self.engine,
            quote_schema=False,
            database_name=__name__,
            uses_bytes_length_limits=True,
        )

    def assertEquivalentNumber(self, first, second, msg=None):
        if first is None or second is None:
            if first is None and second is not None:
                raise AssertionError(f"{first} != {second} {msg}")
        else:
            return self.assertAlmostEqual(float(first), float(second), places=6, msg=msg)

    def assertAlmostEqualsSignificant(self, first, second, significant_digits: int = 7):
        if significant_digits < 1:
            raise ValueError("assertAlmostEqualsSignificant: 'significant_digits' must be >=1")

        first_non_zero = first or second
        if (first_non_zero == 0) or ((first - second) == 0):
            return

        magnitude = int(math.floor((math.log10(first_non_zero))))
        margin = 10 ** (magnitude - significant_digits + 1) / 2.0
        diff_gt_margin = abs(first - second) - margin > -1e-15
        if diff_gt_margin:
            raise AssertionError(f'{first} != {second} to {significant_digits:d} significant figures')

    # noinspection PyPep8Naming
    def _TEXT(self):
        return self.db_container.TEXT

    # noinspection PyPep8Naming
    def _BINARY(self):
        return self.db_container.BINARY

    # noinspection PyPep8Naming
    def _NUMERIC(
            self,
            precision: Optional[int] = None,
            scale: Optional[int] = None,
    ):
        return self.db_container.NUMERIC(precision=precision, scale=scale)

    def print_ddl(self, sa_table: sqlalchemy.schema.Table):
        self.log.debug("DDL:")
        self.log.debug(CreateTable(sa_table).compile(self.mock_database.bind))

    def _get_column_list_table_1(self) -> List[Column]:
        cols = [
            Column('id', Integer, primary_key=True),
            Column('int_col_2', Integer),
            Column('text_col', self._TEXT()),
            Column('text_col_2', self._TEXT()),
            Column('real_col', REAL),
            Column('date_col', Date),
            Column('datetime_col', DateTime),
            Column('float_col', Float),
            Column('string_10_col', String(10)),
            Column('num_col', self._NUMERIC(38, 6)),
            Column('numeric13_col', self._NUMERIC(13)),
            Column('delete_flag', self._TEXT()),
        ]
        if self.db_container.SUPPORTS_TIME:
            cols.append(Column('time_col', Time))

        if self.db_container.SUPPORTS_INTERVAL:
            cols.append(Column('interval_col', Interval))

        if self.db_container.SUPPORTS_BOOLEAN:
            cols.append(Column('bool_col', BOOLEAN))

        if self.db_container.SUPPORTS_BINARY:
            cols.append(Column('large_binary_col', self._BINARY()))

        return cols

    def _get_table_name(self, partial_name: str) -> str:
        existing_tables = self.mock_database.table_inventory(force_reload=True)

        partial_name = partial_name.replace('-', '_')

        while True:
            name = f"{self.TABLE_PREFIX}{partial_name}"

            name_suffix_len = 3 + 3  # Room for _99_i1 for table instance 99 (random) + index 1-9

            if (len(name) + name_suffix_len) > self.db_container.MAX_NAME_LEN:
                name = BaseTestDatabase.make_short_table_name(name, self.db_container.MAX_NAME_LEN - name_suffix_len)

            name_with_id = f"{name}_{random.randint(1, 99)}"
            if name_with_id not in existing_tables:
                return name_with_id

    def _create_index_table_1(self, sa_table) -> List[sqlalchemy.schema.Index]:
        return []

    def _create_table_1(self, tbl_name) -> sqlalchemy.schema.Table:
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            *self._get_column_list_table_1()
        )
        sa_table.create(bind=self.mock_database.bind)

        self._create_index_table_1(sa_table)

        return sa_table

    def _gen_src_rows_1(self, int_range: Union[range, int]) -> typing.Iterator[Row]:
        source_compontent = self.dummy_etl_component
        iteration_header = source_compontent.generate_iteration_header()

        if isinstance(int_range, int):
            int_range = range(int_range)

        for i in int_range:
            row = source_compontent.Row(iteration_header=iteration_header)
            row['id'] = i
            row['int_col_2'] = i * 10
            row['text_col'] = f'this is row {i}'
            row['text_col_2'] = f'{i}'
            row['real_col'] = i / 1000.0
            if self.db_container.SUPPORTS_BOOLEAN:
                row['bool_col'] = (i % 2 == 0)
            row['date_col'] = date(2015 + i, 1, 1 + i)
            row['datetime_col'] = datetime(2001, 1, 1, 12, 1 + i, 12)
            if self.db_container.SUPPORTS_TIME:
                row['time_col'] = time(22, 1 + i, 12)
            row['float_col'] = i / 100000000.0
            if self.db_container.SUPPORTS_INTERVAL:
                row['interval_col'] = timedelta(seconds=i)
            row['large_binary_col'] = f'this is row {i} large_binary_col'.encode('ascii')
            if self.db_container.SUPPORTS_DECIMAL:
                row['num_col'] = Decimal(i) / Decimal(10**6)
                row['numeric13_col'] = Decimal(i * 100)
            row['string_10_col'] = f"row {i}"
            yield row

    def _compare_rows(
            self,
            expected_row: Row,
            actual_row: Row,
            special_check_values: typing.Dict[str, typing.Dict] = None,
            skip_testing: set = None,
            msg: str = None
    ):
        if msg is None:
            msg = ''
        errors_dict = dict()
        has_error = False
        for col in expected_row:
            try:
                if skip_testing is not None:
                    if col in skip_testing:
                        continue
                expected = expected_row[col]
                if special_check_values is not None:
                    if col in special_check_values:
                        if expected in special_check_values[col]:
                            expected = special_check_values[col][expected]

                actual = actual_row[col]
                if isinstance(expected, str) and isinstance(actual, datetime):
                    # Special values should have already been taken care of
                    expected = str2datetime(expected, '%Y-%m-%d %H:%M:%S')
                elif isinstance(expected, str) and isinstance(actual, date):
                    try:
                        expected = str2date(expected, '%Y-%m-%d')
                    except ValueError:
                        expected = str2datetime(expected, '%Y-%m-%d %H:%M:%S').date()

                try:
                    if isinstance(expected, float) or isinstance(actual, float):
                        self.assertEquivalentNumber(expected, actual, f"{col}: Expected {expected} got {actual}")
                    elif isinstance(expected, timedelta) or isinstance(actual, timedelta):
                        if isinstance(expected, str):
                            expected = timedelta(seconds=float(expected))
                        elif isinstance(expected, float):
                            expected = timedelta(seconds=expected)
                        elif isinstance(expected, int):
                            expected = timedelta(seconds=expected)

                        if isinstance(actual, str):
                            actual = timedelta(seconds=float(actual))
                        elif isinstance(actual, float):
                            actual = timedelta(seconds=actual)
                        elif isinstance(expected, int):
                            # noinspection PyTypeChecker
                            actual = timedelta(seconds=actual)

                        self.assertEqual(expected, actual, f"{col}: Expected {expected} got {actual}")

                    elif isinstance(expected, self.ApproxDatetime):
                        self.assertIsNotNone(actual, f"{col}: Expected {expected} got {actual}")
                        self.assertTrue(expected.matches(actual), f"{col}: Expected {expected} got {actual}")
                    elif self.db_container.DATE_AS_DATETIME and isinstance(expected, datetime) and isinstance(actual, datetime):
                        # Since datetime is also date... we have to check the case where both are datetime first
                        self.assertEqual(expected, actual, f"{col}: Expected {expected} got {actual}")
                    elif self.db_container.DATE_AS_DATETIME and isinstance(expected, date) and isinstance(actual, datetime):
                        self.assertEqual(expected, actual.date(), f"{col}: Expected {expected} got {actual}")
                        self.assertIn(actual.hour, {0, 12})
                        self.assertIn(actual.minute, {0})
                        self.assertIn(actual.second, {0})
                    elif self.db_container.DATE_AS_DATETIME and isinstance(expected, datetime) and isinstance(actual, date):
                        self.assertEqual(expected.date(), actual, f"{col}: Expected {expected} got {actual}")
                        self.assertIn(expected.hour, {0, 12})
                        self.assertIn(expected.minute, {0})
                        self.assertIn(expected.second, {0})
                    else:
                        self.assertEqual(expected, actual, f"{col}: Expected {expected} got {actual}")
                    errors_dict[col] = f"OK. Both values are {actual}"
                except AssertionError as e:
                    has_error = True
                    errors_dict[col] = str(e)
            except ValueError as e:
                raise ValueError(f"{e} on column {col} on actual_row {actual_row} to expected {expected_row}")

        if has_error:
            error_parts = list()
            error_parts.append(f"Differences found for {msg}")
            for col in errors_dict:
                error_parts.append(f"   {col}: {errors_dict[col]}")
            raise AssertionError("\n".join(error_parts))

    def _sql_query_date_conv(self, dt_val):
        return dt_val

    def _check_table_rows(
            self,
            source_row_generator: typing.Iterable[Row],
            target_table: ReadOnlyTable,
            key_list: list = None,
            log_rows_found: bool = True,
            msg: str = None,
    ):
        if msg is None:
            msg = ''

        if key_list is None:
            key_list = target_table.primary_key
            self.assertIsNotNone(
                key_list,
                f"Test definition error. key_list not provided and table {target_table} has no primary key"
            )

        rows_dict = dict()
        actual_count = 0
        for row in target_table:
            actual_count += 1
            if log_rows_found:
                self.log.debug(f"{target_table} result row = {row.values()}")
            key = tuple([row[col] for col in key_list])
            rows_dict[key] = row

        self.assertEqual(len(rows_dict), actual_count, f"Test definition error. Read {actual_count} rows but key based dict has {len(rows_dict)}")

        expected_count = 0
        for expected_row in source_row_generator:
            expected_count += 1
            key = tuple([expected_row[col] for col in key_list])
            actual_row = rows_dict[key]
            self._compare_rows(expected_row, actual_row, msg=f"key={key} {msg}")

        self.assertEqual(expected_count, actual_count, f"Test result error. Read {actual_count} rows but expected {expected_count} rows")
