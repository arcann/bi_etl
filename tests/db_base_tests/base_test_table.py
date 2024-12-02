"""
Created on Jan 22, 2016

@author: Derek Wood
"""
import enum
import logging
from contextlib import ExitStack
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from decimal import Decimal
from unittest import mock, TestSuite

import sqlalchemy
from sqlalchemy import exc
from sqlalchemy.exc import DatabaseError
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import BOOLEAN
from sqlalchemy.sql.sqltypes import Date
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.sqltypes import Enum
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.sqltypes import Interval
from sqlalchemy.sql.sqltypes import REAL
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql.sqltypes import TEXT
from sqlalchemy.sql.sqltypes import Time

from bi_etl.bulk_loaders.bulk_loader import BulkLoader
from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.table import Table
from bi_etl.scheduler.task import ETLTask
from bi_etl.utility import dict_to_str
from tests.db_base_tests.base_test_database import BaseTestDatabase


def load_tests(loader, standard_tests, pattern):
    # Filter out all
    suite = TestSuite()
    return suite


# pylint: disable=missing-docstring, protected-access
class BaseTestTable(BaseTestDatabase):
    class MyEnum(enum.Enum):
        a = "a"
        b = "b"
        c = "c"

    @property
    def DEFAULT_NUMERIC(self):
        return self._NUMERIC(16, 2)

    def _create_table(self, tbl_name):
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

    def _create_table_2(self, tbl_name):
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
            Column('del_flg', self._TEXT()),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

    def _create_table_3(self, tbl_name):
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT(), primary_key=True),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

    def testInit(self):
        tbl_name = self._get_table_name('testInit')

        self._create_table(tbl_name)

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            self.assertIn('col1', tbl.column_names)
            self.assertIn('col2', tbl.column_names)
            self.assertIn('col3', tbl.column_names)
            self.assertIn('col4', tbl.column_names)

    def testRelease(self):
        tbl_name = self._get_table_name('testRelease')

        self._create_table(tbl_name)

        mock_db = self._get_mock_db()

        with Table(
            self.task,
            mock_db,
            table_name=tbl_name
        ) as tbl:
            pass
        self.assertTrue(tbl.is_closed)
        for trans in mock_db._transactions:
            self.assertFalse(trans.is_active)
        for conn in mock_db._connection_pool:
            self.assertTrue(conn.is_closed)

    def testReleaseMany(self):
        tbl_name = self._get_table_name('testReleaseMany')

        self._create_table(tbl_name)

        mock_db = self._get_mock_db()

        with ExitStack() as stack:
            tbl1 = stack.enter_context(
                Table(
                    self.task,
                    mock_db,
                    table_name=tbl_name
                )
            )
            tbl2 = stack.enter_context(
                Table(
                    self.task,
                    mock_db,
                    table_name=tbl_name
                )
            )

        self.assertTrue(tbl1.is_closed)
        self.assertTrue(tbl2.is_closed)
        for trans in mock_db._transactions:
            self.assertFalse(trans.is_active)
        for conn in mock_db._connection_pool:
            self.assertTrue(conn.is_closed)

    def testReleaseExitStack(self):
        task = ETLTask(config=self.config)
        tbl_name = self._get_table_name('testReleaseExitStack')

        self._create_table(tbl_name)

        mock_db = self._get_mock_db()

        with task.ExitStack() as stack:
            tbl1 = stack.enter_context(
                Table(
                    self.task,
                    mock_db,
                    table_name=tbl_name
                )
            )
            tbl2 = stack.enter_context(
                Table(
                    self.task,
                    mock_db,
                    table_name=tbl_name
                )
            )

        self.assertTrue(tbl1.is_closed)
        self.assertTrue(tbl2.is_closed)
        for trans in mock_db._transactions:
            self.assertFalse(trans.is_active)
        for conn in mock_db._connection_pool:
            self.assertTrue(conn.is_closed)

    def testReleaseExplicitAutoClose(self):
        task = ETLTask(config=self.config)

        tbl_name = self._get_table_name('testReleaseExplicitAutoClose')

        self._create_table(tbl_name)

        mock_db = self._get_mock_db()

        tbl1: Table = task.auto_close(
            Table(
                task,
                mock_db,
                table_name=tbl_name
            )
        )
        tbl2: Table = task.auto_close(
            Table(
                task,
                mock_db,
                table_name=tbl_name
            )
        )

        class TestContext:
            def __init__(self):
                self.status = 'init'

            def __enter__(self):
                self.status = 'opened'
                return self

            def __exit__(self, exit_type, exit_value, exit_traceback):
                self.status = 'closed'
                return False

        # auto_close should work with any context manager
        ctx = task.auto_close(
            TestContext()
        )
        task.close()

        self.assertTrue(tbl1.is_closed)
        self.assertTrue(tbl2.is_closed)
        self.assertEqual(ctx.status, 'closed')
        for trans in mock_db._transactions:
            self.assertFalse(trans.is_active)
        for conn in mock_db._connection_pool:
            self.assertTrue(conn.is_closed)

    def testReleaseImplicitAutoClose(self):
        task = ETLTask(config=self.config)

        tbl_name = self._get_table_name('testReleaseImplicitAutoClose')

        self._create_table(tbl_name)

        mock_db = self._get_mock_db()

        tbl1 = Table(
            task,
            mock_db,
            table_name=tbl_name
        )

        tbl2 = Table(
            task,
            mock_db,
            table_name=tbl_name
        )

        # Note: ImplicitAutoClose only works for ETLComponent based objects

        task.close()

        self.assertTrue(tbl1.is_closed)
        self.assertTrue(tbl2.is_closed)
        for trans in mock_db._transactions:
            self.assertFalse(trans.is_active)
        for conn in mock_db._connection_pool:
            self.assertTrue(conn.is_closed)

    def testReleaseManyFailed(self):
        tbl_name = self._get_table_name('testReleaseManyFailed')

        self._create_table(tbl_name)

        mock_db = self._get_mock_db()

        try:
            with ExitStack() as stack:
                tbl1 = stack.enter_context(
                    Table(
                        self.task,
                        mock_db,
                        table_name=tbl_name
                    )
                )
                raise RuntimeError("test")
        except RuntimeError:
            pass

        self.assertTrue(tbl1.is_closed)
        for trans in mock_db._transactions:
            self.assertFalse(trans.is_active)
        for conn in mock_db._connection_pool:
            self.assertTrue(conn.is_closed)

    def testInitExcludeCol(self):
        tbl_name = self._get_table_name('testInitExcludeCol')

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name,
                   exclude_columns={'col4'},
                   ) as tbl:
            self.assertIn('col1', tbl.column_names)
            self.assertIn('col2', tbl.column_names)
            self.assertIn('col3', tbl.column_names)
            self.assertNotIn('col4', tbl.column_names)

    def testInitExcludeCol2(self):
        tbl_name = self._get_table_name('testInitExcludeCol2')

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name,
                   exclude_columns={'col4'},
                   ) as tbl:
            tbl.exclude_columns(({'col3'}))

            self.assertIn('col1', tbl.column_names)
            self.assertIn('col2', tbl.column_names)
            self.assertNotIn('col3', tbl.column_names)
            self.assertNotIn('col4', tbl.column_names)

    def testDoesNotExist(self):
        self.assertRaises(exc.NoSuchTableError, Table, task=self.task, database=self.mock_database,
                          table_name='does_not_exist')

    @staticmethod
    def _generate_test_rows_range(
            tbl,
            range_to_use,
            assign_col1: bool = True,
            commit: bool = True,
    ):
        iteration_header = RowIterationHeader()
        for i in range_to_use:
            row = tbl.Row(iteration_header=iteration_header)
            if assign_col1:
                row['col1'] = i
            row['col2'] = f'this is row {i}'
            row['col3'] = i / 1000.0
            row['col4'] = i / 100000000.0

            tbl.insert(row)
        if commit:
            tbl.commit()

    @staticmethod
    def _generate_test_rows(
            tbl,
            rows_to_insert,
            assign_col1: bool = True,
            commit: bool = True,
    ):
        BaseTestTable._generate_test_rows_range(
            tbl,
            range(rows_to_insert),
            assign_col1=assign_col1,
            commit=commit
        )

    def testInsertAndIterateNoKey(self):
        tbl_name = self._get_table_name('testInsertAndIterateNoKey')

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        rows_to_insert = 10
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            self._generate_test_rows(tbl, rows_to_insert)

            # Validate data
            rows_dict = dict()
            for row in tbl:
                self.log.debug(row)
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), rows_to_insert)

            for i in range(rows_to_insert):
                row = rows_dict[i]
                self.assertEqual(row['col1'], i)
                self.assertEqual(row['col2'], f'this is row {i}')
                self.assertEquivalentNumber(row['col3'], i / 1000.0)
                self.assertEquivalentNumber(row['col4'], i / 100000000.0)

    def testInsertAndIterateWithKey(self):
        tbl_name = self._get_table_name('testInsertAndIterateWithKey')
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        tbl.auto_generate_key = True
        tbl.batch_size = 5

        # col1 should be auto-generated
        self._generate_test_rows(tbl, rows_to_insert, assign_col1=False)

        # Validate data
        rows_dict = dict()
        for row in tbl:
            self.log.debug(dict_to_str(row))
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            try:
                row = rows_dict[i + 1]  # Auto-generate starts with 1 not 0
                self.assertEqual(row['col1'], i + 1)  # Auto-generate starts with 1 not 0
                self.assertEqual(row['col2'], f'this is row {i}')
                self.assertEquivalentNumber(row['col3'], i / 1000.0)
                self.assertEquivalentNumber(row['col4'], i / 100000000.0)
            except KeyError:
                raise KeyError(f'Row key {i} did not exist')

    def testInsertDuplicate(self):
        tbl_name = self._get_table_name('testInsertDuplicate')
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        tbl.batch_size = rows_to_insert * 2
        with self.assertLogs(tbl.log, logging.ERROR) as log:
            try:
                for i in range(rows_to_insert):
                    # Use full table row
                    row = tbl.Row()
                    row['col1'] = i % 5
                    row['col2'] = f'this is row {i}'
                    row['col3'] = i / 1000.0
                    row['col4'] = i / 100000000.0

                    tbl.insert(row)
                tbl.commit()
                self.fail('Error not raised (or passed on) on duplicate key')
            except (DatabaseError, sqlalchemy.exc.StatementError):
                full_output = '\n'.join(log.output)
                self.assertIn('UNIQUE constraint'.lower(), full_output.lower())
                self.assertIn('col1', full_output)
                self.assertRegex(full_output, "col1'?:.*0", 'col1: 0 not found in log output')
                self.assertIn('stmt_values', full_output)

    def testInsertAutogenerateContinue(self):
        tbl_name = self._get_table_name('testInsertAutogenCont')
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        rows_to_insert1 = 10
        rows_to_insert2 = 10

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            self._generate_test_rows(tbl, rows_to_insert1)

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            tbl.auto_generate_key = True
            tbl.batch_size = 5
            BaseTestTable._generate_test_rows_range(
                tbl,
                range(rows_to_insert1, rows_to_insert1 + rows_to_insert2),
                # col1 should be autogenerated
                assign_col1=False,
            )

            # Validate data
            rows_dict = dict()
            for row in tbl:
                self.log.debug(dict_to_str(row))
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), rows_to_insert1 + rows_to_insert2, 'row count check')

            for i in range(rows_to_insert1 + rows_to_insert2):
                try:
                    row = rows_dict[i]
                    self.assertEqual(row['col1'], i, 'col1 check')
                    self.assertEqual(row['col2'], f'this is row {i}', 'col2 check')
                    self.assertEquivalentNumber(row['col3'], i / 1000.0, 'col3 check')
                    self.assertEquivalentNumber(row['col4'], i / 100000000.0, 'col4 check')
                except KeyError:
                    raise KeyError(f'Row key {i} did not exist')

    def testInsertAutogenerateContinueNegative(self):
        tbl_name = self._get_table_name('testInsertAutogenContNeg')
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        rows_to_insert1 = 3
        rows_to_insert2 = 10

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            self._generate_test_rows_range(tbl, [-9999, -8888, -7777])

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            tbl.auto_generate_key = True
            tbl.batch_size = 5
            # col1 should be auto-generated
            self._generate_test_rows(tbl, rows_to_insert2, assign_col1=False)

            # Validate data
            rows_dict = dict()
            for row in tbl:
                self.log.debug(dict_to_str(row))
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), rows_to_insert1 + rows_to_insert2)

            for i in range(rows_to_insert2):
                try:
                    row = rows_dict[i + 1]  # Auto generate starts at 1 not 0
                    self.assertEqual(row['col1'], i + 1)  # Auto generate starts at 1 not 0
                    self.assertEqual(row['col2'], f'this is row {i}')
                    self.assertEquivalentNumber(row['col3'], i / 1000.0)
                    self.assertEquivalentNumber(row['col4'], i / 100000000.0)
                except KeyError:
                    raise KeyError(f'Row key {i} did not exist')

    def testUpdate_partial_by_alt_key(self):
        tbl_name = self._get_table_name('testUpdate_by_alt_key')
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('alt_key', Integer),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        for i in range(rows_to_insert):
            # Use full table row
            row = tbl.Row()
            row['col1'] = i
            row['alt_key'] = i + 100
            row['col2'] = f'this is row {i}'
            row['col3'] = i / 1000.0
            row['col4'] = i / 100000000.0

            tbl.insert(row)
        tbl.commit()

        for i in range(rows_to_insert):
            # self.task.debug_sql()
            tbl.trace_sql = True
            tbl.update(updates_to_make={'col2': f'new col2 {i}'},
                       key_names=['alt_key'],
                       key_values=[i + 100],
                       )
            # self.task.debug_sql(False)
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            self.log.debug(f"{row}, col1={row['col1']}, col2={row['col2']}")
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], f'new col2 {i}')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            self.assertEquivalentNumber(row['col4'], i / 100000000.0)

    def testUpdate_partial_by_key(self):
        tbl_name = self._get_table_name('testUpdate_partial_by_key')
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        tbl.batch_size = 0
        iteration_header = RowIterationHeader(
            logical_name='test',
            columns_in_order=[
                'col1',
                'col2',
                'col3',
                'col4',
            ],
        )
        for i in range(rows_to_insert):
            # Use full table row
            row = tbl.Row(iteration_header=iteration_header)
            row['col1'] = i
            row['col2'] = f'this is row {i} before update'
            row['col3'] = i / 1000.0
            row['col4'] = i / 100000000.0

            tbl.insert(row)
        tbl.commit()

        # Update the values
        for i in range(rows_to_insert):
            # self.task.debug_sql()
            tbl.trace_sql = True
            tbl.update(updates_to_make={'col2': f'new col2 {i}'},
                       key_values=[i],
                       )
            # self.task.debug_sql(False)
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            self.log.debug(f"{row}, col1={row['col1']}, col2={row['col2']}")
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], f'new col2 {i}')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            self.assertEquivalentNumber(row['col4'], i / 100000000.0)

    def testUpdate_whole_by_key(self):
        tbl_name = self._get_table_name('testUpdate_whole_by_key')
        self._create_table(tbl_name)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        self._generate_test_rows(tbl, rows_to_insert)

        # Do the updates
        iteration_header = RowIterationHeader()
        for i in range(rows_to_insert):
            # self.task.debug_sql()
            tbl.trace_sql = True
            # DO NOT use full table row since we want a column to not exist
            row = Row(iteration_header)
            row['col1'] = i
            row['col2'] = f'new col2 {i}'
            row['col3'] = i / 1000.0
            row['col4'] = i / 100000000.0
            tbl.update(updates_to_make=row)
            # self.task.debug_sql(False)
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            self.log.debug(f"{row}, col1={row['col1']}, col2={row['col2']}")
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], f'new col2 {i}')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            self.assertEquivalentNumber(row['col4'], i / 100000000.0)

    def test_update_where_pk(self):
        tbl_name = self._get_table_name('test_update_where_pk')
        self._create_table(tbl_name)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        self._generate_test_rows(tbl, rows_to_insert)

        # Do the updates
        for i in range(rows_to_insert):
            # self.task.debug_sql()
            tbl.trace_sql = True
            # Use full table row
            row = tbl.Row()
            row['col1'] = i
            row['col2'] = f'new col2 {i}'
            row['col3'] = i / 1000.0
            row['col4'] = i / 100000000.0
            tbl.update_where_pk(updates_to_make=row)
            # self.task.debug_sql(False)
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            self.log.debug(f"{row}, col1={row['col1']}, col2={row['col2']}")
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], f'new col2 {i}')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            self.assertEquivalentNumber(row['col4'], i / 100000000.0)

    def test_upsert_int_pk(self):
        tbl_name = self._get_table_name('test_upsert_int_pk')
        self._create_table_2(tbl_name)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        tbl.delete_flag = 'del_flg'
        self._generate_test_rows(tbl, rows_to_insert)

        # Do the updates
        tbl.track_source_rows = True
        row_key_values = list(range(rows_to_insert))
        # Add one value that will be inserted
        row_key_values.append(12)
        iteration_header = RowIterationHeader()
        for i in row_key_values:
            # only upsert even rows
            if i % 2 == 0:
                # self.task.debug_sql()
                tbl.trace_sql = True
                # DO NOT use full table row since we want a column to not exist
                row = Row(iteration_header)
                row['col1'] = i
                row['col2'] = f'new col2 {i}'
                row['col3'] = i / 1000.0
                # leave out col 4
                tbl.upsert(row)
                # self.task.debug_sql(False)
        tbl.commit()

        tbl.logically_delete_not_processed()
        tbl.commit()

        # Validate data
        rows_dict = dict()
        last_int_value = -1
        # Note: We intentionally pass a str and not a list below
        # noinspection PyTypeChecker
        for row in tbl.order_by('col1'):
            if row['col1'] <= 9:  # Sequence only holds up from 0 to 9.
                self.assertEqual(last_int_value + 1, row['col1'], 'Order by did not work')
                last_int_value = row['col1']
            self.log.debug(row.values())
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert + 1)

        for i in row_key_values:
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            if i % 2 == 0:
                self.assertEqual(row['col2'], f'new col2 {i}')
                self.assertEqual(row['del_flg'], 'N')
            else:
                self.assertEqual(row['col2'], f'this is row {i}')
                self.assertEqual(row['del_flg'], 'Y')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            if i != 12:
                self.assertEquivalentNumber(row['col4'], i / 100000000.0)
        tbl.close()

        self.mock_database.drop_table_if_exists(tbl_name)

    def test_upsert_int_dual_pk(self):
        tbl_name = self._get_table_name('test_upsert_int_dual_pk')
        self._create_table_3(tbl_name)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        for i in range(rows_to_insert):
            # Use full table row
            row = tbl.Row()
            row['col1'] = i
            row['col2'] = f'this is row {i}'
            row['col3'] = i * 1 / 1000.0
            row['col4'] = i / 100000000.0

            tbl.insert(row)
        tbl.commit()

        # Do the updates / inserts
        iteration_header = RowIterationHeader()
        rows_generated = list()
        for i in range(rows_to_insert):
            # only update even rows            
            # self.task.debug_sql()
            tbl.trace_sql = True
            # DO NOT use full table row since we want a column to not exist
            row = Row(iteration_header)
            row['col1'] = i
            row['col2'] = f'this is row {i}'
            if i % 2 == 0:
                row['col3'] = i * 10
            else:
                row['col3'] = i * 1 / 1000.0
            # leave out col 4
            tbl.upsert(row)

            # Add col4 to the saved list for validation
            saved_row = row.clone()
            saved_row['col4'] = i / 100000000.0
            rows_generated.append(saved_row)
            # self.task.debug_sql(False)
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            self.log.debug(f"{row}, col1={row['col1']}, values={row.values()}")
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for expected_row in rows_generated:
            row = rows_dict[expected_row['col1']]
            self.assertEqual(row['col2'], expected_row['col2'], 'col2 check')
            if expected_row['col1'] % 2 == 0:
                self.assertEqual(row['col3'], expected_row['col3'], 'col3 check even')
            else:
                self.assertEquivalentNumber(row['col3'], expected_row['col3'], 'col3 check odd')
            self.assertEquivalentNumber(row['col4'], expected_row['col4'], 'col4 check')

        tbl.close()
        self.mock_database.drop_table_if_exists(tbl_name)

    def test_delete_int_pk(self):
        tbl_name = self._get_table_name('test_delete_int_pk')
        self._create_table(tbl_name)

        rows_to_insert = 10
        with Table(
            self.task,
            self.mock_database,
            table_name=tbl_name
        ) as tbl:
            self._generate_test_rows(tbl, rows_to_insert)

            # Do the deletes
            tbl.delete(key_values=[2])
            tbl.delete(key_names=['col2'], key_values=[f'this is row {8}'])
            tbl.commit()

            # Validate data
            rows_dict = dict()
            for row in tbl:
                self.log.debug(dict_to_str(row))
                rows_dict[row['col1']] = row

            self.assertEqual(
                rows_to_insert - 2,
                len(rows_dict),
                f"Table has {len(rows_dict)} rows but we expect {rows_to_insert - 2} rows after deletes.\n"
                f"Actual rows = {rows_dict}"
            )

            for i in range(rows_to_insert):
                if i in [2, 8]:
                    self.assertNotIn(i, rows_dict, f'row {i} not deleted')
                else:
                    row = rows_dict[i]
                    self.assertEqual(row['col1'], i)
                    self.assertEqual(row['col2'], f'this is row {i}')
                    self.assertEquivalentNumber(row['col3'], i * 1 / 1000.0)
                    self.assertEquivalentNumber(row['col4'], i / 100000000.0)

        self.mock_database.drop_table_if_exists(tbl_name)

    def test_delete_int_pk_no_batch(self):
        tbl_name = self._get_table_name('test_delete_int_pk_no_batch')
        self._create_table(tbl_name)

        rows_to_insert = 10
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        tbl.batch_size = 1
        self._generate_test_rows(tbl, rows_to_insert)

        # Do the deletes
        tbl.delete(key_values=[2])
        tbl.delete(key_names=['col2'], key_values=[f'this is row {8}'])
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            self.log.debug(dict_to_str(row))
            rows_dict[row['col1']] = row

        self.assertEqual(
            rows_to_insert - 2,
            len(rows_dict),
            f"Table has {len(rows_dict)} rows but we expect {rows_to_insert - 4} rows after deletes.\n"
            f"Actual rows = {rows_dict}"
        )

        for i in range(rows_to_insert):
            if i in [2, 8]:
                self.assertNotIn(i, rows_dict, f'row {i} not deleted')
            else:
                row = rows_dict[i]
                self.assertEqual(row['col1'], i)
                self.assertEqual(row['col2'], f'this is row {i}')
                self.assertEquivalentNumber(row['col3'], i * 1 / 1000.0)
                self.assertEquivalentNumber(row['col4'], i / 100000000.0)

        tbl.close()
        self.mock_database.drop_table_if_exists(tbl_name)

    def testSanityCheck1(self):
        src_tbl_name = self._get_table_name('testSanityCheck1s')
        self.log.info(src_tbl_name)
        sa_table = sqlalchemy.schema.Table(
            src_tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2a', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        tgt_tbl_name = self._get_table_name('testSanityCheck1t')
        sa_table = sqlalchemy.schema.Table(
            tgt_tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2a', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        with Table(
            self.task,
            self.mock_database,
            table_name=src_tbl_name
        ) as src_tbl:
            with Table(
                self.task,
                self.mock_database,
                table_name=tgt_tbl_name
            ) as tgt_tbl:
                with mock.patch('bi_etl.components.etlcomponent.logging', autospec=True) as log:
                    tgt_tbl.log = log
                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                    )
                    self.assertFalse(
                        log.error.called,
                        f"unexpected error from sanity_check_source_mapping. {log.mock_calls}"
                    )
                    self.assertFalse(
                        log.warning.called,
                        f"unexpected warning from sanity_check_source_mapping. {log.mock_calls}"
                    )
                    log.reset_mock()

                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                        target_excludes=frozenset(['col4']),
                    )
                    self.assertFalse(log.error.called)
                    log.reset_mock()

                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                        target_excludes=frozenset(['col4']),
                    )
                    self.assertFalse(log.error.called)
                    # calls_str = '\n'.join([str(call) for call in log.mock_calls])
                    log.reset_mock()

                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                        target_excludes=frozenset(['col4']),
                    )
                    self.assertFalse(log.error.called)
                    calls_str = '\n'.join([str(call) for call in log.mock_calls])
                    self.assertIn('col4', calls_str)
                    log.reset_mock()

                    # Test using row and not source component
                    # DO NOT use full table row since we want a column to not exist
                    iteration_header = RowIterationHeader()
                    src_row = Row(iteration_header)
                    src_row['col1'] = 0
                    src_row['col2a'] = 0
                    src_row['col3'] = 0
                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                    )
                    # calls_str = '\n'.join([str(call) for call in log.mock_calls])
                    self.assertFalse(
                        log.error.called,
                        f'unexpected error from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    self.assertFalse(
                        log.warning.called,
                        f'unexpected warning from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    log.reset_mock()

                    # Test using row and not source component
                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                        target_excludes=frozenset(['col4']),
                    )
                    # calls_str = '\n'.join([str(call) for call in log.mock_calls])
                    self.assertFalse(
                        log.error.called,
                        f'unexpected error from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    log.reset_mock()

        self.mock_database.drop_table_if_exists(src_tbl_name)
        self.mock_database.drop_table_if_exists(tgt_tbl_name)

    def testBuildRow1(self):
        src_tbl_name = self._get_table_name('testBuildRow1s')
        self.log.info(src_tbl_name)
        sa_table = sqlalchemy.schema.Table(
            src_tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2a', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
            Column('ext1', Integer),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        tgt_tbl_name = self._get_table_name('testBuildRow1t')
        sa_tgt_table = sqlalchemy.schema.Table(
            tgt_tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2b', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
            Column('ext2', Integer),
        )
        sa_tgt_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_tgt_table)

        with Table(
            self.task,
            self.mock_database,
            table_name=src_tbl_name
        ) as src_tbl:
            with Table(
                self.task,
                self.mock_database,
                table_name=tgt_tbl_name
            ) as tgt_tbl:
                with mock.patch('bi_etl.components.etlcomponent.logging', autospec=True) as log:
                    tgt_tbl.log = log

                    # Use full table row
                    src_row = src_tbl.Row()
                    src_row['col1'] = 0
                    src_row['col2a'] = 'example text'
                    src_row['col3'] = 123.12
                    src_row['col4'] = 1234.12

                    src_row.rename_columns({'col2a': 'col2b'})
                    tgt_row = tgt_tbl.build_row(
                        src_row,
                        source_excludes=frozenset({'ext1'}),
                        target_excludes=frozenset({'ext2'}),
                    )
                    self.assertFalse(
                        log.error.called,
                        f'unexpected error from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    self.assertFalse(
                        log.warning.called,
                        f'unexpected warning from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    self.assertEqual(tgt_row['col1'], 0)
                    self.assertEqual(tgt_row['col2b'], 'example text')
                    self.assertEquivalentNumber(tgt_row['col3'], 123.12)
                    self.assertEquivalentNumber(tgt_row['col4'], 1234.12)
                    self.assertNotIn('ext1', tgt_row)
                    self.assertNotIn('ext2', tgt_row)
                    log.reset_mock()

                    # Use full table row
                    src_row = src_tbl.Row()
                    src_row['col1'] = '0'
                    src_row['col2a'] = 123
                    src_row['col3'] = '123.12'
                    src_row['col4'] = '1,234.12'

                    src_row.rename_columns({'col2a': 'col2b'})
                    tgt_row = tgt_tbl.build_row(src_row,
                                                source_excludes=frozenset({'ext1'}),
                                                target_excludes=frozenset({'ext2'}),
                                                )
                    self.assertFalse(
                        log.error.called,
                        f'unexpected error from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    self.assertFalse(
                        log.warning.called,
                        f'unexpected warning from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    self.assertEqual(tgt_row['col1'], 0)
                    self.assertEqual(tgt_row['col2b'], '123')
                    self.assertAlmostEqual(tgt_row['col3'], 123.12, places=2)
                    self.assertEqual(tgt_row['col4'], Decimal('1234.12'))
                    self.assertNotIn('ext1', tgt_row)
                    self.assertNotIn('ext2', tgt_row)

    def testBuildRow2(self):
        tbl_name = self._get_table_name('testBuildRow2')

        cols = [
            Column('float_col', Float),
            Column('date_col', Date),
            Column('datetime_col', DateTime),
            Column('numeric13_col', self._NUMERIC(13)),
            Column('numeric25_col', self._NUMERIC(25)),
            Column('numeric25_15_col', self._NUMERIC(25, 15)),
            Column('string_10_col', String(10)),
            Column('enum_col', Enum(BaseTestTable.MyEnum)),
        ]
        if self.db_container.SUPPORTS_TIME:
            cols.append(Column('time_col', Time))

        if self.db_container.SUPPORTS_INTERVAL:
            cols.append(Column('interval_col', Interval))

        if self.db_container.SUPPORTS_BOOLEAN:
            cols.append(Column('bool_col', BOOLEAN))

        if self.db_container.SUPPORTS_BINARY:
            cols.append(Column('large_binary_col', self._BINARY()))

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            *cols
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        with self.dummy_etl_component as src_tbl:
            with Table(
                    self.task,
                    self.mock_database,
                    table_name=tbl_name,
            ) as tgt_tbl:
                # Just here to help IDE know the data type
                assert isinstance(tgt_tbl, Table)
                tgt_tbl.default_date_format = '%m/%d/%Y'

                with mock.patch('bi_etl.components.etlcomponent.logging', autospec=True) as log:
                    tgt_tbl.log = log

                    tgt_tbl.default_date_time_format = ('%m/%d/%Y %H:%M:%S', '%m/%d/%Y')
                    tgt_tbl.default_date_format = '%m/%d/%Y'

                    #
                    # Use full table row
                    src_row = src_tbl.Row()
                    if self.db_container.SUPPORTS_BOOLEAN:
                        src_row['bool_col'] = 0
                    src_row['date_col'] = '01/01/2015'
                    src_row['datetime_col'] = '01/01/2001 12:51:43'  # default format '%m/%d/%Y %H:%M:%S'
                    if self.db_container.SUPPORTS_TIME:
                        src_row['time_col'] = '22:13:55'
                    src_row['enum_col'] = 'a'
                    src_row['float_col'] = '123.45'
                    if self.db_container.SUPPORTS_INTERVAL:
                        src_row['interval_col'] = timedelta(seconds=50)
                    if self.db_container.SUPPORTS_BINARY:
                        src_row['large_binary_col'] = "It's a Python world.".encode('ascii')
                    src_row['numeric13_col'] = '1234567890123'
                    src_row['numeric25_col'] = Decimal('1234567890123456789012345')
                    src_row['numeric25_15_col'] = Decimal('1234567890.123456789012345')
                    src_row['string_10_col'] = '1234567890'

                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertFalse(
                        log.error.called,
                        f'unexpected error from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    self.assertFalse(
                        log.warning.called,
                        f'unexpected warning from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    if self.db_container.SUPPORTS_BOOLEAN:
                        self.assertEqual(tgt_row['bool_col'], False)
                    self.assertIn(tgt_row['date_col'], [
                        date(2015, 1, 1),
                        datetime(2015, 1, 1),
                    ])
                    self.assertEqual(tgt_row['datetime_col'], datetime(2001, 1, 1, 12, 51, 43))
                    if self.db_container.SUPPORTS_TIME:
                        self.assertEqual(tgt_row['time_col'], time(22, 13, 55))
                    self.assertEqual(tgt_row['enum_col'], 'a')
                    self.assertAlmostEqual(tgt_row['float_col'], 123.45, places=2)
                    if self.db_container.SUPPORTS_INTERVAL:
                        self.assertEqual(tgt_row['interval_col'], timedelta(seconds=50))
                    if self.db_container.SUPPORTS_BINARY:
                        self.assertEqual(tgt_row['large_binary_col'], "It's a Python world.".encode('ascii'))
                    self.assertEqual(tgt_row['numeric13_col'], 1234567890123)
                    result_numeric25_col = tgt_row['numeric25_col']
                    if isinstance(result_numeric25_col, int):
                        self.assertEqual(result_numeric25_col, 1234567890123456789012345)
                    elif isinstance(result_numeric25_col, Decimal):
                        self.assertEqual(result_numeric25_col, Decimal(1234567890123456789012345))
                    else:
                        self.log.warning(
                            f"{self}.testBuildRow2 numeric25_col is not int or decimal "
                            f"but {type(result_numeric25_col)} with value {result_numeric25_col}. "
                            "It will be tested for equality in the first 16 significant digits."
                        )
                        col = tgt_tbl.get_column('numeric25_col')
                        self.log.warning(f"numeric25_col type = {repr(col.type)}")
                        self.log.warning(f"numeric25_col type.asdecimal = {repr(col.type.asdecimal)}")
                        self.log.warning(f"numeric25_col type.python_type. = {col.type.python_type}")
                        self.assertAlmostEqualsSignificant(
                            result_numeric25_col, 1234567890123456789012345,
                            significant_digits=16,
                        )

                    # noinspection PyTypeChecker
                    self.assertAlmostEqual(tgt_row['numeric25_15_col'],
                                           Decimal('1234567890.123456789012345'),
                                           places=15)
                    self.assertEqual(tgt_row['string_10_col'], '1234567890')
                    log.reset_mock()

                    # Test datetime to datetime
                    src_row['datetime_col'] = datetime(2001, 1, 1, 12, 51, 43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['datetime_col'], datetime(2001, 1, 1, 12, 51, 43), " Test datetime to datetime")

                    # Test datetime to date
                    src_row['date_col'] = datetime(2001, 1, 1, 12, 51, 43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    tgt_date_col = tgt_row['date_col']
                    if isinstance(tgt_date_col, datetime):
                        # Databases like oracle register DATE as python datetime. So test that at least we got the same out.
                        self.assertEqual(tgt_date_col.date(), date(2001, 1, 1), "Test datetime to date date part")
                        self.assertEqual(tgt_date_col, src_row['date_col'], "Test datetime to date (exception case)")
                    elif isinstance(tgt_date_col, date):
                        self.assertEqual(tgt_date_col, date(2001, 1, 1), "Test datetime to date")
                    else:
                        raise ValueError(f"date_col is {type(tgt_date_col)} = {repr(tgt_row)}")

                    # Test date to date
                    src_row['date_col'] = date(2001, 1, 1)
                    tgt_row = tgt_tbl.build_row(src_row)
                    tgt_date_col = tgt_row['date_col']
                    if isinstance(tgt_date_col, datetime):
                        # Databases like oracle register DATE as python datetime. So test that at least we got the same out.
                        self.assertEqual(tgt_date_col.date(), date(2001, 1, 1), " Test date to date")
                    else:
                        self.assertEqual(tgt_date_col, date(2001, 1, 1), " Test date to date")

                    # Test datetime to time
                    if self.db_container.SUPPORTS_TIME:
                        src_row['time_col'] = datetime(2001, 1, 1, 12, 51, 43)
                        tgt_row = tgt_tbl.build_row(src_row)
                        self.assertEqual(tgt_row['time_col'], time(12, 51, 43), " datetime to time")

                        # Test time to time
                        src_row['time_col'] = time(12, 51, 43)
                        tgt_row = tgt_tbl.build_row(src_row)
                        self.assertEqual(tgt_row['time_col'], time(12, 51, 43), "Test time to time")

                        # Test timedelta to interval
                        src_row['time_col'] = time(12, 51, 43)
                        tgt_row = tgt_tbl.build_row(src_row)
                        self.assertEqual(tgt_row['time_col'], time(12, 51, 43), " timedelta to interval")

                    # Test force_ascii
                    tgt_tbl.force_ascii = True
                    tgt_tbl._build_coerce_methods()
                    src_row['string_10_col'] = 'Ёarth'
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['string_10_col'], '~arth', "Test force_ascii")
                    tgt_tbl.force_ascii = False
                    tgt_tbl._build_coerce_methods()

                    # Test decode bytes as ascii
                    src_row['string_10_col'] = b'Earth'
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['string_10_col'], 'Earth', "Test decode bytes as ascii")

                    # Test string too long
                    src_row['string_10_col'] = '12345678901'
                    self.assertRaises(ValueError, tgt_tbl.build_row, src_row)
                    src_row['string_10_col'] = '12345678'

                    # Test number too long from int
                    src_row['numeric13_col'] = 12345678901234
                    try:
                        _ = tgt_tbl.build_row(src_row)
                        self.fail('Test number too long from int did not raise ValueError')
                    except ValueError:
                        pass
                    src_row['numeric13_col'] = '1234567890123'

                    # Test number too long from str
                    src_row['numeric13_col'] = '12345678901234'
                    try:
                        _ = tgt_tbl.build_row(src_row)
                        self.fail('Test number too long from str did not raise ValueError')
                    except ValueError:
                        pass

    def _test_upsert_special_values_rows_check(self, tbl_name):
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        tbl.primary_key = ['col1']
        tbl.auto_generate_key = True
        tbl.batch_size = 99
        tbl.upsert_special_values_rows()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            self.log.debug(dict_to_str(row))
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), 5)

        row = rows_dict[-9999]
        self.assertEqual(row['col1'], -9999)
        self.assertEqual(row['col2'], 'Missing')
        self.assertEqual(row['col3'], -9999)
        self.assertEqual(row['col4'], -9999)

        row = rows_dict[-8888]
        self.assertEqual(row['col1'], -8888)
        self.assertEqual(row['col2'], 'Invalid')
        self.assertEqual(row['col3'], -8888)
        self.assertEqual(row['col4'], -8888)

        row = rows_dict[-7777]
        self.assertEqual(row['col1'], -7777)
        self.assertEqual(row['col2'], 'Not Available')
        self.assertEqual(row['col3'], -7777)
        self.assertEqual(row['col4'], -7777)

        row = rows_dict[-6666]
        self.assertEqual(row['col1'], -6666)
        self.assertEqual(row['col2'], 'Various')
        self.assertEqual(row['col3'], -6666)
        self.assertEqual(row['col4'], -6666)

    def test_upsert_special_values_rows(self):
        tbl_name = self._get_table_name('test_ups_spec_val_rows')
        self._create_table(tbl_name)
        self._test_upsert_special_values_rows_check(tbl_name)
        # Run a second time to make sure rows stay the same
        self._test_upsert_special_values_rows_check(tbl_name)

    def testInsertAndTruncate(self):
        tbl_name = self._get_table_name('testInsertAndTruncate')
        self._create_table(tbl_name)

        rows_to_insert = 10
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            self._generate_test_rows(tbl, rows_to_insert)

            tbl.truncate()
            tbl.commit()

            # Validate no data
            rows_dict = dict()
            for row in tbl:
                self.log.debug(row)
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), 0, 'Truncate did not remove rows')

    def testInsertAndRollback(self):
        tbl_name = self._get_table_name('testInsertAndRollback')
        self._create_table(tbl_name)

        rows_to_insert = 10
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            self._generate_test_rows(tbl, rows_to_insert, commit=False)

            tbl.rollback()

            # Validate no data
            rows_dict = dict()
            for row in tbl:
                self.log.debug(row)
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), 0, 'Rollback did not remove rows')

    def test_build_row(self):
        tbl_name = self._get_table_name('test_build_row')
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col_int', Integer),
            Column('col_txt', self._TEXT()),
            Column('col_real', REAL),
            Column('col_num', self.DEFAULT_NUMERIC),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            # Add additional columns to test data types not in sqllite
            columns = tbl.columns
            columns.extend([
                Column('col_str_10', String(10)),
                Column('col_d', Date),
                Column('col_dt', DateTime),
                ])
            tbl.set_columns(columns)

            iteration_header = RowIterationHeader()

            #########################################
            # Test default default_date_time_format
            # mm/dd/yyyy should work
            row = Row(iteration_header=iteration_header)
            row['col_dt'] = '01/23/2018 12:56:33'
            result_row = tbl.build_row(row)
            self.assertEqual(result_row['col_dt'], datetime(2018, 1, 23, 12, 56, 33))

            # yyyy-mm-dd should work
            row = Row(iteration_header=iteration_header)
            row['col_dt'] = '2019-02-15 12:56:33'
            result_row = tbl.build_row(row)
            self.assertEqual(result_row['col_dt'], datetime(2019, 2, 15, 12, 56, 33))
            #
            #########################################

            tbl.default_date_time_format = '%m/%d/%Y %H:%M:%S'
            tbl.default_date_format = '%m/%d/%Y'

            row = Row(iteration_header=iteration_header)
            row['col_int'] = '123456789'
            row['col_txt'] = '1234567890'
            row['col_str_10'] = '1234567890'
            row['col_real'] = '42345678901'
            row['col_num'] = '52345678901'
            row['col_dt'] = '01/23/2018 12:56:33'
            row['col_d'] = '05/15/2017'
            result_row = tbl.build_row(row)

            self.assertIsInstance(result_row['col_int'], int)
            self.assertIsInstance(result_row['col_txt'], str)
            self.assertIsInstance(result_row['col_str_10'], str)
            self.assertIsInstance(result_row['col_real'], float)
            self.assertIsInstance(result_row['col_num'], Decimal)
            self.assertIsInstance(result_row['col_dt'], datetime)
            self.assertEqual(result_row['col_dt'], datetime(2018, 1, 23, 12, 56, 33))
            self.assertIsInstance(result_row['col_d'], date)
            self.assertEqual(result_row['col_d'], date(2017, 5, 15))

            row = Row(iteration_header=iteration_header)
            row['col_int'] = '123456789'
            row['col_txt'] = '1234567890'
            row['col_str_10'] = '1234567890'
            row['col_real'] = '42345678901'
            row['col_num'] = '52345678901'
            row['col_dt'] = datetime(2017, 11, 23, 5, 11, 23)
            row['col_d'] = date(2017, 11, 25)

            for _ in range(1000):
                result_row = tbl.build_row(row)

            self.assertIsInstance(result_row['col_int'], int)
            self.assertIsInstance(result_row['col_txt'], str)
            self.assertIsInstance(result_row['col_str_10'], str)
            self.assertIsInstance(result_row['col_real'], float)
            self.assertIsInstance(result_row['col_num'], Decimal)
            self.assertIsInstance(result_row['col_dt'], datetime)
            self.assertIsInstance(result_row['col_d'], date)

    def test_upsert_override_autogen_pk(self):
        tbl_name = self._get_table_name('test_ups_overr_autogen_pk')
        self._create_table_2(tbl_name)

        rows_to_insert = 10
        with Table(
            self.task,
            self.mock_database,
            table_name=tbl_name
        ) as tbl:
            tbl.primary_key = ['col1']
            tbl.natural_key = ['col2']
            tbl.auto_generate_key = True
            tbl.delete_flag = 'del_flg'

            iteration_header = RowIterationHeader()
            for i in range(rows_to_insert):
                row = tbl.Row(iteration_header=iteration_header)
                row['col1'] = i
                row['col2'] = f'this is row {i}'
                row['col3'] = i / 1000.0
                row['col4'] = i / 100000000.0

                tbl.upsert(row)
            tbl.commit()

        self.mock_database.drop_table_if_exists(tbl_name)

    # TODO: Test update_not_in_set, delete_not_in_set 

    @staticmethod
    def _generate_bulk_test_row(
            i: int,
            tbl: Table,
            iteration_header: RowIterationHeader
    ) -> Row:
        row = tbl.Row(iteration_header=iteration_header)
        row['col1'] = i
        row['col2'] = f'this is row {i}'
        row['col3'] = i / 1000.0
        row['col4'] = i / 100000000.0
        return row

    def _testBulkInsertAndIterateNoKey(
            self,
            tbl_name: str,
            bulk_loader: BulkLoader,
    ):
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', self._TEXT()),
            Column('col3', REAL),
            Column('col4', self.DEFAULT_NUMERIC),
            Column('col5', TEXT),
        )
        sa_table.create(bind=self.mock_database.bind)

        self.print_ddl(sa_table)

        rows_to_insert = 10
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            tbl.set_bulk_loader(bulk_loader)
            iteration_header = RowIterationHeader()
            for i in range(rows_to_insert):
                row = self._generate_bulk_test_row(
                    i,
                    tbl,
                    iteration_header
                )

                tbl.insert_row(row)

            tbl.bulk_load_from_cache()

            # Validate data
            rows_dict = dict()
            for row in tbl:
                # self.log.debug(row.values())
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), rows_to_insert)

            for i in range(rows_to_insert):
                expected_row = self._generate_bulk_test_row(
                    i,
                    tbl,
                    iteration_header
                )
                row = rows_dict[i]
                self._compare_rows(
                    expected_row=expected_row,
                    actual_row=row,
                )
