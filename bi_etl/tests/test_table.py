"""
Created on Jan 22, 2016

@author: Derek Wood
"""
import enum
import logging
import unittest
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import sqlalchemy
from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.components.csvreader import CSVReader
from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.table import Table
from bi_etl.database.connect import Connect
from bi_etl.scheduler.task import ETLTask
from bi_etl.tests._test_base_database import _TestBaseDatabase
from bi_etl.utility import dict_to_str
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
from sqlalchemy.sql.sqltypes import LargeBinary
from sqlalchemy.sql.sqltypes import NUMERIC
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy.sql.sqltypes import REAL
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql.sqltypes import TEXT
from sqlalchemy.sql.sqltypes import Time


# pylint: disable=missing-docstring, protected-access


class TestTable(_TestBaseDatabase):
    class MyEnum(enum.Enum):
        a = "a"
        b = "b"
        c = "c"

    def _create_table(self, tbl_name):
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

    def _create_table_2(self, tbl_name):
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
            Column('del_flg', TEXT),
        )
        sa_table.create()

    def _create_table_3(self, tbl_name):
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT, primary_key=True),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

    def testInit(self):
        tbl_name = 'testInit'

        self._create_table(tbl_name)

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            self.assertIn('col1', tbl.column_names)
            self.assertIn('col2', tbl.column_names)
            self.assertIn('col3', tbl.column_names)
            self.assertIn('col4', tbl.column_names)
            self.assertIn('col5', tbl.column_names)

    def testInitExcludeCol(self):
        tbl_name = 'testInitExcludeCol'

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name,
                   exclude_columns={'col4'},
                   ) as tbl:
            self.assertIn('col1', tbl.column_names)
            self.assertIn('col2', tbl.column_names)
            self.assertIn('col3', tbl.column_names)
            self.assertNotIn('col4', tbl.column_names)
            self.assertIn('col5', tbl.column_names)

    def testInitExcludeCol2(self):
        tbl_name = 'testInitExcludeCol2'

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

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
            self.assertIn('col5', tbl.column_names)

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
            row['col5'] = f'this is row {i} blob'.encode('ascii')

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
        TestTable._generate_test_rows_range(
            tbl,
            range(rows_to_insert),
            assign_col1=assign_col1,
            commit=commit
        )

    def testInsertAndIterateNoKey(self):
        tbl_name = 'testInsertAndIterateNoKey'

        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

        rows_to_insert = 10
        with Table(self.task,
                   self.mock_database,
                   table_name=tbl_name) as tbl:
            self._generate_test_rows(tbl, rows_to_insert)

            # Validate data
            rows_dict = dict()
            for row in tbl:
                print(row)
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), rows_to_insert)

            for i in range(rows_to_insert):
                row = rows_dict[i]
                self.assertEqual(row['col1'], i)
                self.assertEqual(row['col2'], f'this is row {i}')
                self.assertEquivalentNumber(row['col3'], i / 1000.0)
                self.assertEquivalentNumber(row['col4'], i / 100000000.0)
                self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))


    def testInsertAndIterateWithKey(self):
        tbl_name = 'testInsertAndIterateWithKey'
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

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
            print(row, row.values())
            print(dict_to_str(row))
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            try:
                row = rows_dict[i + 1]  # Auto-generate starts with 1 not 0
                self.assertEqual(row['col1'], i + 1)  # Auto-generate starts with 1 not 0
                self.assertEqual(row['col2'], f'this is row {i}')
                self.assertEquivalentNumber(row['col3'], i / 1000.0)
                self.assertEquivalentNumber(row['col4'], i / 100000000.0)
                self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))
            except KeyError:
                raise KeyError(f'Row key {i} did not exist')

    def testInsertDuplicate(self):
        tbl_name = 'testInsertDuplicate'
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

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
                    row['col5'] = f'this is row {i} blob'.encode('ascii')

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
        tbl_name = 'testInsertAutogenerateContinue'
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

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
            TestTable._generate_test_rows_range(
                tbl,
                range(rows_to_insert1, rows_to_insert1 + rows_to_insert2),
                # col1 should be autogenerated
                assign_col1=False,
            )
            iteration_header = RowIterationHeader()

            # Validate data
            rows_dict = dict()
            for row in tbl:
                print(row, row.values())
                print(dict_to_str(row))
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), rows_to_insert1 + rows_to_insert2, 'row count check')

            for i in range(rows_to_insert1 + rows_to_insert2):
                try:
                    row = rows_dict[i]
                    self.assertEqual(row['col1'], i, 'col1 check')
                    self.assertEqual(row['col2'], f'this is row {i}', 'col2 check')
                    self.assertEquivalentNumber(row['col3'], i / 1000.0, 'col3 check')
                    self.assertEquivalentNumber(row['col4'], i / 100000000.0, 'col4 check')
                    self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'), 'col5 check')
                except KeyError:
                    raise KeyError(f'Row key {i} did not exist')

    def testInsertAutogenerateContinueNegative(self):
        tbl_name = 'testInsertAutogenerateContinueNegative'
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

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
                print(row, row.values())
                print(dict_to_str(row))
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), rows_to_insert1 + rows_to_insert2)

            for i in range(rows_to_insert2):
                try:
                    row = rows_dict[i + 1]  # Auto generate starts at 1 not 0
                    self.assertEqual(row['col1'], i + 1)  # Auto generate starts at 1 not 0
                    self.assertEqual(row['col2'], f'this is row {i}')
                    self.assertEquivalentNumber(row['col3'], i / 1000.0)
                    self.assertEquivalentNumber(row['col4'], i / 100000000.0)
                    self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))
                except KeyError:
                    raise KeyError(f'Row key {i} did not exist')

    def testUpdate_partial_by_alt_key(self):
        tbl_name = 'testUpdate_by_alt_key'
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('alt_key', Integer),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

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
            row['col5'] = f'this is row {i} blob'.encode('ascii')

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
            print(row, row['col1'], row['col2'])
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], f'new col2 {i}')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            self.assertEquivalentNumber(row['col4'], i / 100000000.0)
            self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))

    def testUpdate_partial_by_key(self):
        tbl_name = 'testUpdate_partial_by_key'
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

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
                'col5',
            ],
        )
        for i in range(rows_to_insert):
            # Use full table row
            row = tbl.Row(iteration_header=iteration_header)
            row['col1'] = i
            row['col2'] = f'this is row {i} before update'
            row['col3'] = i / 1000.0
            row['col4'] = i / 100000000.0
            row['col5'] = f'this is row {i} blob'.encode('ascii')

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
            print(row, row['col1'], row['col2'])
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], f'new col2 {i}')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            self.assertEquivalentNumber(row['col4'], i / 100000000.0)
            self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))

    def testUpdate_whole_by_key(self):
        tbl_name = 'testUpdate_whole_by_key'
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
            row['col5'] = f'this is row {i} blob'.encode('ascii')
            tbl.update(updates_to_make=row)
            # self.task.debug_sql(False)
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            print(row, row['col1'], row['col2'])
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], f'new col2 {i}')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            self.assertEquivalentNumber(row['col4'], i / 100000000.0)
            self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))

    def test_update_where_pk(self):
        tbl_name = 'test_update_where_pk'
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
            row['col5'] = f'this is row {i} blob'.encode('ascii')
            tbl.update_where_pk(updates_to_make=row)
            # self.task.debug_sql(False)
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            print(row, row['col1'], row['col2'])
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), rows_to_insert)

        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], f'new col2 {i}')
            self.assertEquivalentNumber(row['col3'], i / 1000.0)
            self.assertEquivalentNumber(row['col4'], i / 100000000.0)
            self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))

    def test_upsert_int_pk(self):
        tbl_name = 'test_upsert_int_pk'
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
                row['col5'] = f'this is row {i} blob'.encode('ascii')
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
            self.log.debug(row.values_in_order())
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
            self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))
        tbl.close()

        self.mock_database.drop_table_if_exists(tbl_name)

    def test_upsert_int_dual_pk(self):
        tbl_name = 'test_upsert_int_dual_pk'
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
            row['col5'] = f'this is row {i} blob'.encode('ascii')

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
            row['col5'] = f'this is row {i} blob'.encode('ascii')
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
            print(row, row['col1'], row.values_in_order())
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
            self.assertEqual(row['col5'], expected_row['col5'], 'col5 check')

        tbl.close()
        self.mock_database.drop_table_if_exists(tbl_name)

    def test_delete_int_pk(self):
        tbl_name = 'test_delete_int_pk'
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
                print(row, row.values())
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
                    self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))


        self.mock_database.drop_table_if_exists(tbl_name)

    def test_delete_int_pk_no_batch(self):
        tbl_name = 'test_delete_int_pk_no_batch'
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
            print(row, row.values())
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
                self.assertEqual(row['col5'], f'this is row {i} blob'.encode('ascii'))

        tbl.close()
        self.mock_database.drop_table_if_exists(tbl_name)

    def testSanityCheck1(self):
        src_tbl_name = 'testSanityCheck1s'
        self.log.info(src_tbl_name)
        sa_table = sqlalchemy.schema.Table(
            src_tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2a', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
        )
        sa_table.create()

        tgt_tbl_name = 'testSanityCheck1t'
        sa_table = sqlalchemy.schema.Table(
            tgt_tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2a', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
        )
        sa_table.create()

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
                        source_excludes=frozenset(['col5']),
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
                        source_excludes=frozenset(['col5']),
                        target_excludes=frozenset(['col4']),
                    )
                    self.assertFalse(log.error.called)
                    log.reset_mock()

                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                        target_excludes=frozenset(['col4']),
                    )
                    self.assertFalse(log.error.called)
                    calls_str = '\n'.join([str(call) for call in log.mock_calls])
                    self.assertIn('col5', calls_str)
                    log.reset_mock()

                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                        source_excludes=frozenset(['col5']),
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
                    src_row['col5'] = 0
                    tgt_tbl.sanity_check_source_mapping(
                        src_tbl,
                        source_excludes=frozenset(['col5']),
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
                        source_excludes=frozenset(['col5']),
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
        src_tbl_name = 'testBuildRow1s'
        self.log.info(src_tbl_name)
        sa_table = sqlalchemy.schema.Table(
            src_tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2a', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
            Column('ext1', Integer),
        )
        sa_table.create()

        tgt_tbl_name = 'testBuildRow1t'
        sa_table = sqlalchemy.schema.Table(
            tgt_tbl_name,
            self.mock_database,
            Column('col1', Integer, primary_key=True),
            Column('col2b', TEXT),
            Column('col3', REAL),
            Column('col4', NUMERIC),
            Column('col5', LargeBinary),
            Column('ext2', Integer),
        )
        sa_table.create()

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
                    src_row['col5'] = 'this is row blob'.encode('ascii')

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
                    self.assertEqual(tgt_row['col5'], 'this is row blob'.encode('ascii'))
                    self.assertNotIn('ext1', tgt_row)
                    self.assertNotIn('ext2', tgt_row)
                    log.reset_mock()

                    # Use full table row
                    src_row = src_tbl.Row()
                    src_row['col1'] = '0'
                    src_row['col2a'] = 123
                    src_row['col3'] = '123.12'
                    src_row['col4'] = '1,234.12'
                    src_row['col5'] = 123

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
                    self.assertEqual(tgt_row['col5'], b'123')
                    self.assertNotIn('ext1', tgt_row)
                    self.assertNotIn('ext2', tgt_row)

    def testBuildRow2(self):
        tbl_name = 'testBuildRow2'
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('float_col', Float),
            Column('date_col', Date),
            Column('datetime_col', DateTime),
            Column('time_col', Time),
            Column('interval_col', Interval),
            Column('large_binary_col', LargeBinary),
            Column('numeric13_col', Numeric(13)),
            Column('numeric25_col', Numeric(25)),
            Column('numeric25_15_col', Numeric(25, 15)),
            Column('strin_10_col', String(10)),
            Column('bool_col', BOOLEAN),
            Column('enum_col', Enum(TestTable.MyEnum)),
        )
        sa_table.create()

        with CSVReader(
            self.task,
            filedata=None,
            logical_name='testBuildRow2_src',
        ) as src_tbl:
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

                    tgt_tbl.default_date_time_format = '%m/%d/%Y %H:%M:%S'
                    tgt_tbl.default_date_format = '%m/%d/%Y'

                    #
                    # Use full table row
                    src_row = src_tbl.Row()
                    src_row['bool_col'] = 0
                    src_row['date_col'] = '01/01/2015'
                    src_row['datetime_col'] = '01/01/2001 12:51:43'  # default format '%m/%d/%Y %H:%M:%S'
                    src_row['time_col'] = '22:13:55'
                    src_row['enum_col'] = 'a'
                    src_row['float_col'] = '123.45'
                    src_row['interval_col'] = timedelta(seconds=50)
                    src_row['large_binary_col'] = "It's a Python world.".encode('ascii')
                    src_row['numeric13_col'] = '1234567890123'
                    src_row['numeric25_col'] = Decimal('1234567890123456789012345')
                    src_row['numeric25_15_col'] = Decimal('1234567890.123456789012345')
                    src_row['strin_10_col'] = '1234567890'

                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertFalse(
                        log.error.called,
                        f'unexpected error from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    self.assertFalse(
                        log.warning.called,
                        f'unexpected warning from sanity_check_source_mapping. {log.mock_calls}'
                    )
                    self.assertEqual(tgt_row['bool_col'], False)
                    self.assertEqual(tgt_row['date_col'], date(2015, 1, 1))
                    self.assertEqual(tgt_row['datetime_col'], datetime(2001, 1, 1, 12, 51, 43))
                    self.assertEqual(tgt_row['time_col'], time(22, 13, 55))
                    self.assertEqual(tgt_row['enum_col'], 'a')
                    self.assertAlmostEqual(tgt_row['float_col'], 123.45, places=2)
                    self.assertEqual(tgt_row['interval_col'], timedelta(seconds=50))
                    self.assertEqual(tgt_row['large_binary_col'], "It's a Python world.".encode('ascii'))
                    self.assertEqual(tgt_row['numeric13_col'], 1234567890123)
                    self.assertEqual(tgt_row['numeric25_col'], 1234567890123456789012345)
                    self.assertAlmostEqual(tgt_row['numeric25_15_col'], Decimal('1234567890.123456789012345'),
                                           places=15)
                    self.assertEqual(tgt_row['strin_10_col'], '1234567890')
                    log.reset_mock()

                    # Test datetime to datetime
                    src_row['datetime_col'] = datetime(2001, 1, 1, 12, 51, 43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['datetime_col'], datetime(2001, 1, 1, 12, 51, 43), " Test datetime to datetime")

                    # Test datetime to date
                    src_row['date_col'] = datetime(2001, 1, 1, 12, 51, 43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['date_col'], date(2001, 1, 1), "Test datetime to date")

                    # Test date to date
                    src_row['date_col'] = date(2001, 1, 1)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['date_col'], date(2001, 1, 1), " Test date to date")

                    # Test datetime to time
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
                    src_row['strin_10_col'] = 'Ёarth'
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['strin_10_col'], '~arth', "Test force_ascii")
                    tgt_tbl.force_ascii = False
                    tgt_tbl._build_coerce_methods()

                    # Test decode bytes as ascii
                    src_row['strin_10_col'] = b'Earth'
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['strin_10_col'], 'Earth', "Test decode bytes as ascii")

                    # Test string too long
                    src_row['strin_10_col'] = '12345678901'
                    self.assertRaises(ValueError, tgt_tbl.build_row, src_row)
                    src_row['strin_10_col'] = '12345678'

                    # Test number too long from int
                    src_row['numeric13_col'] = 12345678901234
                    try:
                        tgt_row = tgt_tbl.build_row(src_row)
                        self.fail('Test number too long from int did not raise ValueError')
                    except ValueError:
                        pass
                    src_row['numeric13_col'] = '1234567890123'

                    # Test number too long from str
                    src_row['numeric13_col'] = '12345678901234'
                    try:
                        tgt_row = tgt_tbl.build_row(src_row)
                        self.fail('Test number too long from str did not raise ValueError')
                    except ValueError:
                        pass

    def _test_upsert_special_values_rows_check(self, tbl_name):
        tbl = Table(self.task,
                    self.mock_database,
                    table_name=tbl_name)
        tbl.primary_key = ['col1']
        tbl.auto_generate_key = True
        tbl.batch_size = 5
        tbl.upsert_special_values_rows()
        tbl.commit()

        # Validate data
        rows_dict = dict()
        for row in tbl:
            print(row, row.values())
            print(dict_to_str(row))
            rows_dict[row['col1']] = row

        self.assertEqual(len(rows_dict), 4)

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
        tbl_name = 'test_upsert_special_values_rows'
        self._create_table(tbl_name)
        self._test_upsert_special_values_rows_check(tbl_name)
        # Run a second time to make sure rows stay the same
        self._test_upsert_special_values_rows_check(tbl_name)

    def testInsertAndTruncate(self):
        tbl_name = 'testInsertAndTruncate'
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
                print(row)
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), 0, 'Truncate did not remove rows')

    def testInsertAndRollback(self):
        tbl_name = 'testInsertAndRollback'
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
                print(row)
                rows_dict[row['col1']] = row

            self.assertEqual(len(rows_dict), 0, 'Rollback did not remove rows')

    def test_build_row(self):
        tbl_name = 'test_build_row'
        sa_table = sqlalchemy.schema.Table(
            tbl_name,
            self.mock_database,
            Column('col_int', Integer),
            Column('col_txt', TEXT),
            Column('col_real', REAL),
            Column('col_num', NUMERIC),
            Column('col_blob', LargeBinary),
        )
        sa_table.create()

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

            tbl.default_date_time_format = '%m/%d/%Y %H:%M:%S'
            tbl.default_date_format = '%m/%d/%Y'

            iteration_header = RowIterationHeader()
            row = Row(iteration_header=iteration_header)
            row['col_int'] = '123456789'
            row['col_txt'] = '1234567890'
            row['col_str_10'] = '1234567890'
            row['col_real'] = '42345678901'
            row['col_num'] = '52345678901'
            row['col_blob'] = '62345678901'
            row['col_dt'] = '01/23/2018 12:56:33'
            row['col_d'] = '05/15/2017'
            result_row = tbl.build_row(row)

            self.assertIsInstance(result_row['col_int'], int)
            self.assertIsInstance(result_row['col_txt'], str)
            self.assertIsInstance(result_row['col_str_10'], str)
            self.assertIsInstance(result_row['col_real'], float)
            self.assertIsInstance(result_row['col_num'], Decimal)
            self.assertIsInstance(result_row['col_blob'], bytes)
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
            row['col_blob'] = '62345678901'
            row['col_dt'] = datetime(2017, 11, 23, 5, 11, 23)
            row['col_d'] = date(2017, 11, 25)

            for _ in range(1000):
                result_row = tbl.build_row(row)

            self.assertIsInstance(result_row['col_int'], int)
            self.assertIsInstance(result_row['col_txt'], str)
            self.assertIsInstance(result_row['col_str_10'], str)
            self.assertIsInstance(result_row['col_real'], float)
            self.assertIsInstance(result_row['col_num'], Decimal)
            self.assertIsInstance(result_row['col_blob'], bytes)
            self.assertIsInstance(result_row['col_dt'], datetime)
            self.assertIsInstance(result_row['col_d'], date)

    def test_upsert_override_autogen_pk(self):
        tbl_name = 'test_upsert_override_autogen_pk'
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
                row = tbl.Row()
                row['col1'] = i
                row['col2'] = 'this is row {}'.format(i)
                row['col3'] = i / 1000.0
                row['col4'] = i / 100000000.0
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')

                tbl.upsert(row)
            tbl.commit()

        self.mock_database.drop_table_if_exists(tbl_name)

    # TODO: Test update_not_in_set, delete_not_in_set 


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
