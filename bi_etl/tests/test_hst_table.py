"""
Created on Jan 27, 2016
"""
from datetime import datetime
import logging
import unittest

import sqlalchemy
from bi_etl.components.hst_table import HistoryTable
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
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.row.row import Row
from bi_etl.database.connect import Connect
from bi_etl.scheduler.task import ETLTask


# pylint: disable=missing-docstring, protected-access
from bi_etl.tests.dummy_etl_component import DummyETLComponent


class TestHstTable(unittest.TestCase):
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

        with HistoryTable(
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
        with HistoryTable(
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
        with HistoryTable(
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

        rows_to_insert = 10
        upsert_start = 5
        upsert_end = 15
        with HistoryTable(
                self.task,
                self.mock_database,
                table_name=tbl_name) as tbl:
            tbl.begin_date_column = 'source_begin_date'
            tbl.end_date_column = 'source_end_date'
            tbl.auto_generate_key = True
            tbl.type_1_surrogate = 'sk1_col'
            tbl.trace_data = True

            tbl.define_lookup('NK',
                              [sa_table.c.nk_col1,
                               sa_table.c.nk_col2,
                               ]
                              )

            for i in range(rows_to_insert):
                row = tbl.Row()
                row.remove_columns([tbl.type_1_surrogate])
                row['nk_col1'] = i
                row['nk_col2'] = i + 100
                row['text_col'] = 'this is row {}'.format(i)
                row['real_col'] = i / 1000.0
                row['num_col'] = i / 100000000.0
                row['blob_col'] = 'this is row {} blob'.format(i).encode('ascii')
                tbl.insert(row)
            tbl.commit()

            tbl.fill_cache()

            update_row_header = RowIterationHeader()
            source_excludes = frozenset([tbl.type_1_surrogate, tbl.primary_key[0]])
            for i in range(upsert_start, upsert_end + 1):
                row = Row(iteration_header=update_row_header)
                row['nk_col1'] = i
                row['nk_col2'] = i + 100
                row['text_col'] = 'upsert row {}'.format(i)
                row['datetime_col'] = datetime(2001, 1, i, 12, 51, 43)

                tbl.upsert(row, lookup_name='NK', source_excludes=source_excludes)

            tbl.commit()

            # Validate data
            last_int_value = -1
            for row in tbl.order_by(['nk_col1', 'nk_col2', tbl.begin_date_column]):
                self.log.debug(row.values_in_order())
                if row[tbl.begin_date_column] == tbl.default_begin_date:
                    self.assertEqual(last_int_value + 1, row['nk_col1'], 'Order by did not work')
                    last_int_value = row['nk_col1']
                else:
                    self.assertEqual(last_int_value, row['nk_col1'], 'Order by did not work for new version row')

                # Check the row contents
                i = row['nk_col1']
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


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
