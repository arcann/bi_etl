"""
Created on Jan 27, 2016
"""
import logging
import unittest
from datetime import datetime

import sqlalchemy
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.schema import Index
from sqlalchemy.sql.sqltypes import BLOB
from sqlalchemy.sql.sqltypes import BOOLEAN
from sqlalchemy.sql.sqltypes import CLOB
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

from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.components.hst_table_source_based import HistoryTableSourceBased
from bi_etl.components.row.row import Row
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.database.connect import Connect
from bi_etl.scheduler.task import ETLTask
# pylint: disable=missing-docstring, protected-access
from bi_etl.tests.dummy_etl_component import DummyETLComponent


class TestHistoryTableSourceBased(unittest.TestCase):
    def setUp(self):
        self.log = logging.getLogger('TestHstTable')
        self.log.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        database_name = 'test_db'
        self.config = BIConfigParser()
        self.config[database_name] = {}
        self.config[database_name]['dialect'] = 'sqlite'
        self.task = ETLTask(config=self.config)
        self.mock_database = Connect.get_database_metadata(config=self.config,
                                                           database_name=database_name,
                                                           )

    def tearDown(self):
        pass

    def testInsertAndIterate(self):
        tbl_name = 'testInsertAndIterate'

        sa_table = sqlalchemy.schema.Table(tbl_name,
                                           self.mock_database,
                                           Column('int_col', Integer, primary_key=True),
                                           Column('source_begin_date', DateTime, primary_key=True),
                                           Column('source_end_date', DateTime),
                                           Column('text_col', TEXT),
                                           Column('real_col', REAL),
                                           Column('num_col', NUMERIC),
                                           Column('blob_col', BLOB),
                                           Column('bool_col', BOOLEAN),
                                           Column('clob_col', CLOB),
                                           Column('date_col', Date),
                                           Column('datetime_col', DateTime),
                                           Column('time_col', Time),
                                           Column('float_col', Float),
                                           Column('interval_col', Interval),
                                           Column('large_binary_col', LargeBinary),
                                           Column('numeric13_col', Numeric(13)),
                                           Column('numeric25_col', Numeric(25)),
                                           Column('numeric25_15_col', Numeric(25, 15)),
                                           Column('strin_10_col', String(10)),
                                           )
        sa_table.create()

        rows_to_insert = 10
        source_compontent = DummyETLComponent()

        with HistoryTableSourceBased(
                self.task,
                self.mock_database,
                table_name=tbl_name) as tbl:
            tbl.begin_date_column = 'source_begin_date'
            tbl.end_date_column = 'source_end_date'
            for i in range(rows_to_insert):
                row = source_compontent.Row()
                row['int_col'] = i
                row['text_col'] = 'this is row {}'.format(i)
                row['real_col'] = i / 1000.0
                row['num_col'] = i / 100000000.0
                row['blob_col'] = 'this is row {} blob'.format(i).encode('ascii')

                tbl.insert(row)
            tbl.commit()

            # Validate data
            rows_dict = dict()
            for row in tbl:
                self.log.debug(row.values_in_order())
                rows_dict[row['int_col']] = row

            self.assertEqual(len(rows_dict), rows_to_insert)

            for i in range(rows_to_insert):
                row = rows_dict[i]
                self.assertEqual(row['int_col'], i)
                self.assertEqual(row['text_col'], 'this is row {}'.format(i))
                self.assertEqual(row['real_col'], i / 1000.0)
                self.assertEqual(row['num_col'], i / 100000000.0)
                self.assertEqual(row['blob_col'], 'this is row {} blob'.format(i).encode('ascii'))

        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))

    def testInsertAndUpsertPK(self):
        tbl_name = 'testInsertAndUpsertPK'

        sa_table = sqlalchemy.schema.Table(tbl_name,
                                           self.mock_database,
                                           Column('int_col', Integer, primary_key=True),
                                           Column('source_begin_date', DateTime, primary_key=True),
                                           Column('source_end_date', DateTime),
                                           Column('text_col', TEXT),
                                           Column('real_col', REAL),
                                           Column('num_col', NUMERIC),
                                           Column('blob_col', BLOB),
                                           Column('bool_col', BOOLEAN),
                                           Column('clob_col', CLOB),
                                           Column('date_col', Date),
                                           Column('datetime_col', DateTime),
                                           Column('time_col', Time),
                                           Column('float_col', Float),
                                           Column('interval_col', Interval),
                                           Column('large_binary_col', LargeBinary),
                                           Column('numeric13_col', Numeric(13)),
                                           Column('numeric25_col', Numeric(25)),
                                           Column('numeric25_15_col', Numeric(25, 15)),
                                           Column('strin_10_col', String(10)),
                                           )
        sa_table.create()

        rows_to_insert = 10
        upsert_start = 5
        upsert_end = 15
        with HistoryTableSourceBased(
                self.task,
                self.mock_database,
                table_name=tbl_name) as tbl:
            tbl.begin_date_column = 'source_begin_date'
            tbl.end_date_column = 'source_end_date'
            tbl.trace_data = True
            for i in range(rows_to_insert):
                row = tbl.Row()
                row['int_col'] = i
                row['text_col'] = 'this is row {}'.format(i)
                row['real_col'] = i / 1000.0
                row['num_col'] = i / 100000000.0
                row['blob_col'] = 'this is row {} blob'.format(i).encode('ascii')
                tbl.insert(row)
            tbl.commit()

            update_row_header = RowIterationHeader()
            for i in range(upsert_start, upsert_end + 1):
                row = Row(iteration_header=update_row_header)
                row['int_col'] = i
                row['text_col'] = 'upsert row {}'.format(i)
                row['datetime_col'] = datetime(2001, 1, i, 12, 51, 43)

                tbl.upsert(row)

            tbl.commit()

            # Validate data
            rows_dict = dict()
            last_int_value = -1
            for row in tbl.order_by(['int_col', tbl.begin_date_column]):
                self.log.debug(row.values_in_order())
                if row[tbl.begin_date_column] == tbl.default_begin_date:
                    self.assertEqual(last_int_value + 1, row['int_col'], 'Order by did not work')
                    last_int_value = row['int_col']
                else:
                    self.assertEqual(last_int_value, row['int_col'], 'Order by did not work for new version row')
                rows_dict[row['int_col']] = row

                # Check the row contents
                i = row['int_col']
                if i in range(upsert_start):
                    self.assertEqual(row['text_col'], 'this is row {}'.format(i))
                    self.assertEqual(row['real_col'], i / 1000.0)
                    self.assertEqual(row['num_col'], i / 100000000.0)
                    self.assertEqual(row['blob_col'], 'this is row {} blob'.format(i).encode('ascii'))
                    self.assertIsNone(row['datetime_col'])
                else:
                    if row[tbl.begin_date_column] == tbl.default_begin_date and i in range(rows_to_insert):
                        # original values
                        self.assertEqual(row['text_col'], 'this is row {}'.format(i))
                        self.assertEqual(row['real_col'], i / 1000.0)
                        self.assertEqual(row['num_col'], i / 100000000.0)
                        self.assertEqual(row['blob_col'], 'this is row {} blob'.format(i).encode('ascii'))
                        self.assertIsNone(row['datetime_col'])
                    else:
                        # new values
                        self.assertEqual(row['text_col'], 'upsert row {}'.format(i))
                        # for the originally inserted rows the new version will have the original data for
                        # these fields that are not in the upsert
                        if i in range(rows_to_insert):
                            self.assertEqual(row['real_col'], i / 1000.0)
                            self.assertEqual(row['num_col'], i / 100000000.0)
                            self.assertEqual(row['blob_col'], 'this is row {} blob'.format(i).encode('ascii'))
                        else:
                            self.assertIsNone(row['real_col'])
                            self.assertIsNone(row['num_col'])
                            self.assertIsNone(row['blob_col'])
                        self.assertEqual(row['datetime_col'], datetime(2001, 1, i, 12, 51, 43))

        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))

    def testInsertAndUpsertPKCached(self):
        tbl_name = 'testInsertAndUpsertPKCached'

        sa_table = sqlalchemy.schema.Table(tbl_name,
                                           self.mock_database,
                                           Column('int_col', Integer, primary_key=True),
                                           Column('source_begin_date', DateTime, primary_key=True),
                                           Column('source_end_date', DateTime),
                                           Column('text_col', TEXT),
                                           Column('real_col', REAL),
                                           Column('num_col', NUMERIC),
                                           Column('blob_col', BLOB),
                                           Column('bool_col', BOOLEAN),
                                           Column('clob_col', CLOB),
                                           Column('date_col', Date),
                                           Column('datetime_col', DateTime),
                                           Column('time_col', Time),
                                           Column('float_col', Float),
                                           Column('interval_col', Interval),
                                           Column('large_binary_col', LargeBinary),
                                           Column('numeric13_col', Numeric(13)),
                                           Column('numeric25_col', Numeric(25)),
                                           Column('numeric25_15_col', Numeric(25, 15)),
                                           Column('strin_10_col', String(10)),
                                           )
        sa_table.create()

        rows_to_insert = 10
        upsert_start = 5
        upsert_end = 15
        with HistoryTableSourceBased(
                self.task,
                self.mock_database,
                table_name=tbl_name) as tbl:
            tbl.begin_date_column = 'source_begin_date'
            tbl.end_date_column = 'source_end_date'
            tbl.trace_data = True
            for i in range(rows_to_insert):
                row = tbl.Row()
                row['int_col'] = i
                row['text_col'] = 'this is row {}'.format(i)
                row['real_col'] = i / 1000.0
                row['num_col'] = i / 100000000.0
                row['blob_col'] = 'this is row {} blob'.format(i).encode('ascii')
                tbl.insert(row)
            tbl.commit()

            tbl.fill_cache()

            update_row_header = RowIterationHeader()
            for i in range(upsert_start, upsert_end + 1):
                row = Row(iteration_header=update_row_header)
                row['int_col'] = i
                row['text_col'] = 'upsert row {}'.format(i)
                row['datetime_col'] = datetime(2001, 1, i, 12, 51, 43)

                tbl.upsert(row)

            tbl.commit()

            # Validate data
            last_int_value = -1
            for row in tbl.order_by(['int_col', tbl.begin_date_column]):
                self.log.debug(row.values_in_order())
                if row[tbl.begin_date_column] == tbl.default_begin_date:
                    self.assertEqual(last_int_value + 1, row['int_col'], 'Order by did not work')
                    last_int_value = row['int_col']
                else:
                    self.assertEqual(last_int_value, row['int_col'], 'Order by did not work for new version row')

                # Check the row contents
                i = row['int_col']
                if i in range(upsert_start):
                    self.assertEqual(row['text_col'], 'this is row {}'.format(i))
                    self.assertEqual(row['real_col'], i / 1000.0)
                    self.assertEqual(row['num_col'], i / 100000000.0)
                    self.assertEqual(row['blob_col'], 'this is row {} blob'.format(i).encode('ascii'))
                    self.assertIsNone(row['datetime_col'])
                else:
                    if row[tbl.begin_date_column] == tbl.default_begin_date and i in range(rows_to_insert):
                        # original values
                        self.assertEqual(row['text_col'], 'this is row {}'.format(i))
                        self.assertEqual(row['real_col'], i / 1000.0)
                        self.assertEqual(row['num_col'], i / 100000000.0)
                        self.assertEqual(row['blob_col'], 'this is row {} blob'.format(i).encode('ascii'))
                        self.assertIsNone(row['datetime_col'])
                    else:
                        # new values
                        self.assertEqual(row['text_col'], 'upsert row {}'.format(i))
                        # for the originally inserted rows the new version will have the original data for
                        # these fields that are not in the upsert
                        if i in range(rows_to_insert):
                            self.assertEqual(row['real_col'], i / 1000.0)
                            self.assertEqual(row['num_col'], i / 100000000.0)
                            self.assertEqual(row['blob_col'], 'this is row {} blob'.format(i).encode('ascii'))
                        else:
                            self.assertIsNone(row['real_col'])
                            self.assertIsNone(row['num_col'])
                            self.assertIsNone(row['blob_col'])
                        self.assertEqual(row['datetime_col'], datetime(2001, 1, i, 12, 51, 43))

        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))

    def testInsertAndUpsertNKCached(self):
        tbl_name = 'testInsertAndUpsertNKCached'

        sa_table = sqlalchemy.schema.Table(tbl_name,
                                           self.mock_database,
                                           Column('sk2_col', Integer, primary_key=True),
                                           Column('source_begin_date', DateTime),
                                           Column('source_end_date', DateTime),
                                           Column('sk1_col', Integer),
                                           Column('nk_col1', Integer),
                                           Column('nk_col2', TEXT),
                                           Column('text_col', TEXT),
                                           )
        sa_table.create()

        idx = Index(tbl_name + '_idx',
                    sa_table.c.nk_col1,
                    sa_table.c.nk_col2,
                    sa_table.c.source_begin_date,
                    unique=True
                    )
        idx.create()

        idx = Index(tbl_name + '_idx2',
                    sa_table.c.sk1_col,
                    sa_table.c.source_begin_date,
                    unique=True
                    )
        idx.create()

        with DummyETLComponent(self.task, ) as src_tbl:
            with HistoryTableSourceBased(
                    self.task,
                    self.mock_database,
                    table_name=tbl_name) as tgt_tbl:
                tgt_tbl.begin_date_column = 'source_begin_date'
                tgt_tbl.end_date_column = 'source_end_date'
                tgt_tbl.auto_generate_key = True
                tgt_tbl.type_1_surrogate = 'sk1_col'
                tgt_tbl.trace_data = True
                tgt_tbl.default_date_time_format = '%m/%d/%Y %H:%M:%S'

                tgt_tbl.define_lookup(
                    'NK',
                    [sa_table.c.nk_col1, sa_table.c.nk_col2]
                  )

                starting_rows = [
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '1/1/2000 00:00:00', 'text_col': 'A'},
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '5/1/2000 00:00:00', 'text_col': 'B'},
                    {'nk_col1': 2, 'nk_col2': 'x', 'source_begin_date': '1/1/2000 00:00:00', 'text_col': 'C'},
                    {'nk_col1': 3, 'nk_col2': 'y', 'source_begin_date': '1/1/2000 00:00:00', 'text_col': 'C'},
                ]

                for row_dict in starting_rows:
                    row = src_tbl.Row(data=row_dict)
                    tgt_tbl.upsert(row, lookup_name='NK',)
                tgt_tbl.commit()

                # Validate data from pass 1 (upsert on empty)
                table_rows = tgt_tbl.order_by(['nk_col1', 'nk_col2', tgt_tbl.begin_date_column])
                for expected_row, row in zip(starting_rows, table_rows):
                    self.log.debug(row.as_dict)
                    for test_col in ['nk_col1', 'nk_col2', 'text_col']:
                        self.assertEqual(row[test_col], expected_row[test_col], "Test upsert on empty")

                tgt_tbl.fill_cache()

                upsert_rows = [
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '1/1/2000 00:00:00', 'text_col': 'A'},
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '5/1/2000 00:00:00', 'text_col': 'B'},
                    {'nk_col1': 2, 'nk_col2': 'x', 'source_begin_date': '1/1/2000 00:00:00', 'text_col': 'C'},
                    {'nk_col1': 3, 'nk_col2': 'y', 'source_begin_date': '1/1/2000 00:00:00', 'text_col': 'C'},
                ]

                for row_dict in upsert_rows:
                    row = src_tbl.Row(data=row_dict)
                    tgt_tbl.upsert(
                        row,
                        lookup_name='NK',
                        source_excludes=frozenset({tgt_tbl.type_1_surrogate, tgt_tbl.primary_key[0]}),
                    )

                tgt_tbl.commit()

                expected_rows = [
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'A'},
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '2000-05-01 00:00:00', 'text_col': 'B'},
                    {'nk_col1': '2', 'nk_col2': 'x', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'C'},
                    {'nk_col1': '3', 'nk_col2': 'y', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'C'},
                ]

                # Validate data
                table_rows = tgt_tbl.order_by(['nk_col1', 'nk_col2', tgt_tbl.begin_date_column])
                for expected_row, row in zip(expected_rows, table_rows):
                    self.log.debug("-"*80)
                    self.log.debug("Row={}".format(row.as_dict))
                    self.log.debug("Exp={}".format(expected_row))
                    for test_col in expected_row.keys():
                        self.assertEqual(str(row[test_col]), expected_row[test_col], "Not changed test")

                # New dates, no change except that 1.a now keeps text_col = A for a month longer

                upsert_rows = [
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '1/1/2000 00:00:00', 'text_col': 'A'},
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '6/1/2000 00:00:00', 'text_col': 'B'},
                    {'nk_col1': 2, 'nk_col2': 'x', 'source_begin_date': '2/1/2000 00:00:00', 'text_col': 'C'},
                    {'nk_col1': 3, 'nk_col2': 'y', 'source_begin_date': '3/1/2000 00:00:00', 'text_col': 'C'},
                ]

                for row_dict in upsert_rows:
                    row = src_tbl.Row(data=row_dict)
                    tgt_tbl.upsert(
                        row,
                        lookup_name='NK',
                        source_excludes=frozenset({tgt_tbl.type_1_surrogate, tgt_tbl.primary_key[0]}),
                    )

                tgt_tbl.commit()

                expected_rows = [
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'A'},
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '2000-05-01 00:00:00', 'text_col': 'A'},
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '2000-06-01 00:00:00', 'text_col': 'B'},
                    {'nk_col1': '2', 'nk_col2': 'x', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'C'},
                    {'nk_col1': '3', 'nk_col2': 'y', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'C'},
                ]

                # Validate data
                table_rows = tgt_tbl.order_by(['nk_col1', 'nk_col2', tgt_tbl.begin_date_column])
                for expected_row, row in zip(expected_rows, table_rows):
                    self.log.debug("-" * 80)
                    self.log.debug("Row={}".format(row.as_dict))
                    self.log.debug("Exp={}".format(expected_row))
                    for test_col in expected_row.keys():
                        self.assertEqual(str(row[test_col]), expected_row[test_col], "New dates, no change")

                # New data values

                upsert_rows = [
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '1/1/2000 00:00:00', 'text_col': 'A2'},
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '6/1/2000 00:00:00', 'text_col': 'B2'},
                    {'nk_col1': 1, 'nk_col2': 'a', 'source_begin_date': '7/1/2010 00:00:00', 'text_col': '10'},

                    {'nk_col1': 2, 'nk_col2': 'x', 'source_begin_date': '2/1/2000 00:00:00', 'text_col': 'C'},
                    {'nk_col1': 2, 'nk_col2': 'x', 'source_begin_date': '8/1/2001 00:00:00', 'text_col': 'C2'},

                    {'nk_col1': 3, 'nk_col2': 'y', 'source_begin_date': '3/1/2000 00:00:00', 'text_col': 'C3'},
                    {'nk_col1': 3, 'nk_col2': 'y', 'source_begin_date': '9/1/2001 00:00:00', 'text_col': 'C4'},

                    {'nk_col1': 4, 'nk_col2': 'a', 'source_begin_date': '9/1/2001 00:00:00', 'text_col': 'D'},
                ]

                for row_dict in upsert_rows:
                    row = src_tbl.Row(data=row_dict)
                    tgt_tbl.upsert(
                        row,
                        lookup_name='NK',
                        source_excludes=frozenset({tgt_tbl.type_1_surrogate, tgt_tbl.primary_key[0]}),
                    )

                tgt_tbl.commit()

                expected_rows = [
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'A2'},
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '2000-05-01 00:00:00', 'text_col': 'A2'},
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '2000-06-01 00:00:00', 'text_col': 'B2'},
                    {'nk_col1': '1', 'nk_col2': 'a', 'source_begin_date': '2010-07-01 00:00:00', 'text_col': '10'},

                    {'nk_col1': '2', 'nk_col2': 'x', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'C'},
                    {'nk_col1': '2', 'nk_col2': 'x', 'source_begin_date': '2001-08-01 00:00:00', 'text_col': 'C2'},

                    {'nk_col1': '3', 'nk_col2': 'y', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'C3'},
                    {'nk_col1': '3', 'nk_col2': 'y', 'source_begin_date': '2001-09-01 00:00:00', 'text_col': 'C4'},

                    {'nk_col1': '4', 'nk_col2': 'a', 'source_begin_date': '1900-01-01 00:00:00', 'text_col': 'D'},
                ]

                # Validate data
                table_rows = tgt_tbl.order_by(['nk_col1', 'nk_col2', tgt_tbl.begin_date_column])
                for expected_row, row in zip(expected_rows, table_rows):
                    self.log.debug("-" * 80)
                    self.log.debug("Row={}".format(row.as_dict))
                    self.log.debug("Exp={}".format(expected_row))
                    for test_col in expected_row.keys():
                        self.assertEqual(str(row[test_col]), expected_row[test_col], "New dates, no change")

            self.mock_database.execute('DROP TABLE {}'.format(tbl_name))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
