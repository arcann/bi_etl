import inspect
import logging
import os
import random
import typing
import unittest
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import sqlalchemy
from config_wrangler.config_templates.sqlalchemy_database import SQLAlchemyDatabase
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.schema import Index
from sqlalchemy.sql.sqltypes import BOOLEAN
from sqlalchemy.sql.sqltypes import Date
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.sqltypes import Interval
from sqlalchemy.sql.sqltypes import LargeBinary
from sqlalchemy.sql.sqltypes import NUMERIC
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy.sql.sqltypes import REAL
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql.sqltypes import TEXT
from sqlalchemy.sql.sqltypes import Time

from bi_etl.components.readonlytable import ReadOnlyTable
from bi_etl.components.row.row import Row
from bi_etl.database import DatabaseMetadata
from bi_etl.scheduler.task import ETLTask
from tests.config_for_tests import build_config
from tests.db_sqlite.sqlite_db import SqliteDB
from tests.dummy_etl_component import DummyETLComponent


class _TestBaseDatabase(unittest.TestCase):
    db_container = None
    SUPPORTS_DECIMAL = False
    TABLE_PREFIX = ''

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
        if cls.__name__[0] == '_':
            # if unittest
            raise unittest.SkipTest("Not a test class")
            # if pytest ... but how do we detect?
            # For now we'll detect if db_container is None in setUp
            # pytest.skip("Not a test class")
        cls.db_container = SqliteDB()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db_container.shutdown()

    @staticmethod
    def get_package_path():
        module_path = Path(inspect.getfile(_TestBaseDatabase))
        return module_path.parents[1]

    def setUp(self):
        if self.db_container is None:
            raise unittest.SkipTest("Pytest not skipping whole class on raise unittest.SkipTest from setUpClass")
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
        engine = self.db_container.create_engine()
        self.log.info(f"Using DB connection {engine}")

        self.mock_database = DatabaseMetadata(
            bind=engine,
            quote_schema=False,
            database_name=__name__,
            uses_bytes_length_limits=True,
        )

    def tearDown(self):
        self.mock_database.dispose()
        self.tmp.cleanup()

    def assertEquivalentNumber(self, first, second, msg=None):
        if first is None or second is None:
            if first is None and second is not None:
                raise AssertionError(f"{first} != {second} {msg}")
        else:
            return self.assertAlmostEqual(float(first), float(second), places=6, msg=msg)

    def _get_column_list_table_1(self) -> typing.List[Column]:
        cols = [
            Column('id', Integer, primary_key=True),
            Column('int_col_2', Integer),
            Column('text_col', TEXT),
            Column('text_col_2', TEXT),
            Column('real_col', REAL),
            Column('bool_col', BOOLEAN),
            Column('date_col', Date),
            Column('datetime_col', DateTime),
            Column('time_col', Time),
            Column('float_col', Float),
            Column('interval_col', Interval),
            Column('large_binary_col', LargeBinary),
            Column('strin_10_col', String(10)),
            Column('num_col', NUMERIC(38, 6)),
            Column('numeric13_col', Numeric(13)),
            Column('delete_flag', TEXT),
        ]
        return cols

    def _get_table_name(self, partial_name: str) -> str:
        return f"{self.TABLE_PREFIX}{partial_name}_{random.randint(1, 99)}"

    def _create_index_table_1(self, sa_table) -> typing.List[sqlalchemy.schema.Index]:
        idx = Index(sa_table.name + '_idx',
                    sa_table.c.int_col,
                    unique=True
                    )
        idx.create()
        return [idx]

    def _create_table_1(self, tbl_name) -> sqlalchemy.schema.Table:
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            *self._get_column_list_table_1()
        )
        sa_table.create()

        self._create_index_table_1(sa_table)

        return sa_table

    def _gen_src_rows_1(self, int_range: typing.Union[range, int]) -> typing.Iterator[Row]:
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
            row['bool_col'] = (i % 2 == 0)
            row['date_col'] = date(2015 + i, 1, 1 + i)
            row['datetime_col'] = datetime(2001, 1, 1, 12, 1 + i, 12)
            row['time_col'] = time(22, 1 + i, 12)
            row['float_col'] = i / 100000000.0
            row['interval_col'] = timedelta(seconds=i)
            row['large_binary_col'] = f'this is row {i} large_binary_col'.encode('ascii')
            if self.SUPPORTS_DECIMAL:
                row['num_col'] = Decimal(i) / Decimal(10**6)
                row['numeric13_col'] = Decimal(i * 100)
            row['strin_10_col'] = f"row {i}"
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
            if skip_testing is not None:
                if col in skip_testing:
                    continue
            expected = expected_row[col]
            if special_check_values is not None:
                if col in special_check_values:
                    if expected in special_check_values[col]:
                        expected = special_check_values[col][expected]

            actual = actual_row[col]
            try:
                if isinstance(expected, float) or isinstance(actual, float):
                    self.assertEquivalentNumber(expected, actual, f"Expected {expected} got {actual}")
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
                        actual = timedelta(seconds=actual)

                    self.assertEqual(expected, actual, f"Expected {expected} got {actual}")

                elif isinstance(expected, self.ApproxDatetime):
                    self.assertIsNotNone(actual, f"Expected {expected} got {actual}")
                    self.assertTrue(expected.matches(actual), f"Expected {expected} got {actual}")
                else:
                    self.assertEqual(expected, actual, f"Expected {expected} got {actual}")
                errors_dict[col] = f"OK. Both values are {actual}"
            except AssertionError as e:
                has_error = True
                errors_dict[col] = str(e)

        if has_error:
            error_parts = list()
            error_parts.append(f"Differences found for {msg}")
            for col in errors_dict:
                error_parts.append(f"   {col}: {errors_dict[col]}")
            raise AssertionError("\n".join(error_parts))

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
                self.log.debug(f"{target_table} result row = {row.values_in_order()}")
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
