"""
Created on Jan 22, 2016

@author: woodd
"""
from datetime import date
from datetime import time
from datetime import timedelta
from datetime import datetime
from decimal import Decimal
import logging
from unittest import mock
import unittest


import sqlalchemy
from sqlalchemy import exc
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import BOOLEAN
from sqlalchemy.sql.sqltypes import CLOB
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.sqltypes import Date
from sqlalchemy.sql.sqltypes import Enum
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.sqltypes import Interval
from sqlalchemy.sql.sqltypes import LargeBinary
from sqlalchemy.sql.sqltypes import Numeric
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql.sqltypes import Time
from sqlalchemy.sql.sqltypes import REAL
from sqlalchemy.sql.sqltypes import TEXT
from sqlalchemy.sql.sqltypes import NUMERIC
from sqlalchemy.sql.sqltypes import BLOB


from bi_etl.bi_config_parser import BIConfigParser
from bi_etl.components.table import Table
from bi_etl.scheduler.task import ETLTask
from bi_etl.database.connect import Connect
from bi_etl.utility import dict_to_str
from bi_etl.components.csvreader import CSVReader
from bi_etl.conversions import Transformation
from bi_etl.conversions import Conversion
from bi_etl.conversions import str2date
from bi_etl.conversions import str2datetime
from bi_etl.conversions import str2time
from bi_etl.conversions import str2float
from bi_etl.conversions import str2decimal
from bi_etl.conversions import nullif
from sqlalchemy.exc import DatabaseError

#pylint: disable=missing-docstring, protected-access


class TestTable(unittest.TestCase):

    def setUp(self):        
        self.log = logging.getLogger('TestTable')
        self.log.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)        
        database_name = 'test_db'
        self.config = BIConfigParser()        
        self.config[database_name] = {}
        self.config[database_name]['dialect'] = 'sqlite'
        self.task = ETLTask(config= self.config)
        self.mock_database = Connect.get_database_metadata(config=self.config, 
                                                           database_name=database_name,
                                                           )

    def tearDown(self):
        pass

    def testInit(self):
        tbl_name = 'testInit'
        
        # Wanted to test Table (sqlalchemy metadata) parsing of a table it did not create. 
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        with Table(self.task, 
                   self.mock_database,  
                   table_name= tbl_name) as tbl:
        
            self.assertIn('col1', tbl.column_names)
            self.assertIn('col2', tbl.column_names)
            self.assertIn('col3', tbl.column_names)
            self.assertIn('col4', tbl.column_names)
            self.assertIn('col5', tbl.column_names)
            self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
            
    def testInitExcludeCol(self):
        tbl_name = 'testInitExcludeCol'
        
        # Wanted to test Table (sqlalchemy metadata) parsing of a table it did not create. 
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        with Table(self.task, 
                   self.mock_database,  
                   table_name= tbl_name,
                   exclude_columns=['col4']
                   ) as tbl:
        
            self.assertIn('col1', tbl.column_names)
            self.assertIn('col2', tbl.column_names)
            self.assertIn('col3', tbl.column_names)
            self.assertNotIn('col4', tbl.column_names)
            self.assertIn('col5', tbl.column_names)
            self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
            
    def testInitExcludeCol2(self):
        tbl_name = 'testInitExcludeCol2'
        
        # Wanted to test Table (sqlalchemy metadata) parsing of a table it did not create. 
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        with Table(self.task, 
                   self.mock_database,  
                   table_name= tbl_name,
                   exclude_columns=['col4']
                   ) as tbl:
            tbl.exclude_columns(['col3'])
            
            self.assertIn('col1', tbl.column_names)
            self.assertIn('col2', tbl.column_names)
            self.assertNotIn('col3', tbl.column_names)
            self.assertNotIn('col4', tbl.column_names)
            self.assertIn('col5', tbl.column_names)
            self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
        
    def testDoesNotExist(self):
        self.assertRaises(exc.NoSuchTableError, Table, task=self.task, database=self.mock_database, table_name='does_not_exist') 
        
    def testInsertAndIterateNoKey(self):
        tbl_name = 'testInsertAndIterateNoKey'
                
        sa_table = sqlalchemy.schema.Table(tbl_name, 
                                           self.mock_database,
                                           Column('col1', Integer),
                                           Column('col2', TEXT),
                                           Column('col3', REAL),
                                           Column('col4', NUMERIC),
                                           Column('col5', BLOB),
                                           )
        sa_table.create()
        
        rows_to_insert = 10 
        with Table(self.task, 
                   self.mock_database,  
                   table_name= tbl_name) as tbl:
            for i in range(rows_to_insert):
                row=tbl.Row()
                row['col1'] = i
                row['col2'] = 'this is row {}'.format(i)
                row['col3'] = i/1000.0
                row['col4'] = i/100000000.0
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                
                tbl.insert(row)
            tbl.commit()
            
            # Validate data
            rows_dict = dict()        
            for row in tbl:
                print(row)
                rows_dict[ row['col1'] ] = row
            
            self.assertEqual(len(rows_dict), rows_to_insert)
            
            for i in range(rows_to_insert):
                row = rows_dict[i]
                self.assertEqual(row['col1'], i)
                self.assertEqual(row['col2'], 'this is row {}'.format(i))
                self.assertEqual(row['col3'], i/1000.0)
                self.assertEqual(row['col4'], i/100000000.0)
                self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
                
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
        
    def testInsertAndIterateWithKey(self):
        tbl_name = 'testInsertAndIterateWithKey'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        tbl.auto_generate_key = True
        tbl.batch_size = 5
        for i in range(rows_to_insert):
            row=tbl.Row()
            #col1 should be autogenerated
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row.values())
            print(dict_to_str(row))
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert)
        
        for i in range(rows_to_insert):
            try:
                row = rows_dict[i+1]  # Autogenerate starts with 1 not 0
                self.assertEqual(row['col1'], i+1) # Autogenerate starts with 1 not 0
                self.assertEqual(row['col2'], 'this is row {}'.format(i))
                self.assertEqual(row['col3'], i/1000.0)
                self.assertEqual(row['col4'], i/100000000.0)
                self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
            except KeyError:
                raise KeyError('Row key {} did not exist'.format(i))
            
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))

    def testInsertDuplicate(self):
        tbl_name = 'testInsertDuplicate'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        tbl.batch_size = rows_to_insert * 2
        with self.assertLogs(tbl.log, logging.ERROR) as log:
            try:
                for i in range(rows_to_insert):
                    row = tbl.Row()
                    row['col1'] = i % 5
                    row['col2'] = 'this is row {}'.format(i)
                    row['col3'] = i/1000.0
                    row['col4'] = i/100000000.0
                    row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                    
                    tbl.insert(row)
                tbl.commit()
                self.fail('Error not raised (or passed on) on duplicate key')
            except DatabaseError:
                full_output = '\n'.join(log.output)                                                
                self.assertIn('Error with', full_output)
                self.assertIn('col1', full_output)
                self.assertRegex(full_output, expected_regex='col1:.*0', msg='col1: 0 not found in log output')
                
    def testInsertDuplicateCanNotReplicate(self):
        tbl_name = 'testInsertDuplicate'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        
        # By setting the batch size the the same as the repeat interval the rollback will undo all records
        # vs the redo will only do the current batch. So the failure won't be replicated. 
        tbl.batch_size = int(rows_to_insert / 2)
        
        with self.assertLogs(tbl.log, logging.ERROR) as log:
            try:
                for i in range(rows_to_insert):
                    row=tbl.Row()
                    row['col1'] = i % int(rows_to_insert / 2)
                    row['col2'] = 'this is row {}'.format(i)
                    row['col3'] = i/1000.0
                    row['col4'] = i/100000000.0
                    row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                    
                    tbl.insert(row)
                tbl.commit()
                self.fail('Error not raised (or passed on) on duplicate key')
            except DatabaseError:
                full_output = '\n'.join(log.output)                                                
                self.assertIn('Single inserts did not produce the error', full_output)
        
    def testInsertAutogenerateContinue(self):
        tbl_name = 'testInsertAutogenerateContinue'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))
        
        rows_to_insert1 = 10
        rows_to_insert2 = 10
        
        with Table(self.task, 
                   self.mock_database,  
                   table_name= tbl_name) as tbl:
            for i in range(rows_to_insert1):
                row=tbl.Row()
                row['col1'] = i
                row['col2'] = 'this is row {}'.format(i)
                row['col3'] = i/1000.0
                row['col4'] = i/100000000.0
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                
                tbl.insert(row)
            tbl.commit()
        
        with Table(self.task, 
                   self.mock_database, 
                   table_name= tbl_name) as tbl:
            tbl.auto_generate_key = True
            tbl.batch_size = 5
            for i in range(rows_to_insert1, rows_to_insert1 + rows_to_insert2):
                row=tbl.Row()
                #col1 should be autogenerated
                row['col2'] = 'this is row {}'.format(i)
                row['col3'] = i/1000.0
                row['col4'] = i/100000000.0
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                
                tbl.insert(row)
            tbl.commit()
            
            # Validate data
            rows_dict = dict()        
            for row in tbl:
                print(row, row.values())
                print(dict_to_str(row))
                rows_dict[ row['col1'] ] = row
            
            self.assertEqual(len(rows_dict), rows_to_insert1 + rows_to_insert2)
            
            for i in range(rows_to_insert1 + rows_to_insert2):
                try:
                    row = rows_dict[i]
                    self.assertEqual(row['col1'], i)
                    self.assertEqual(row['col2'], 'this is row {}'.format(i))
                    self.assertEqual(row['col3'], i/1000.0)
                    self.assertEqual(row['col4'], i/100000000.0)
                    self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
                except KeyError:
                    raise KeyError('Row key {} did not exist'.format(i))
            
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
        
    def testInsertAutogenerateContinueNegative(self):
        tbl_name = 'testInsertAutogenerateContinue'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))
        
        rows_to_insert1 = 3
        rows_to_insert2 = 10
        
        with Table(self.task, 
                   self.mock_database,  
                   table_name= tbl_name) as tbl:
            for i in [-9999,-8888,-7777]:
                row=tbl.Row()
                row['col1'] = i
                row['col2'] = 'this is row {}'.format(i)
                row['col3'] = i/1000.0
                row['col4'] = i/100000000.0
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                
                tbl.insert(row)
            tbl.commit()
        
        with Table(self.task, 
                   self.mock_database, 
                   table_name= tbl_name) as tbl:
            tbl.auto_generate_key = True
            tbl.batch_size = 5
            for i in range(rows_to_insert2):
                row=tbl.Row()
                #col1 should be autogenerated
                row['col2'] = 'this is row {}'.format(i)
                row['col3'] = i/1000.0
                row['col4'] = i/100000000.0
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                
                tbl.insert(row)
            tbl.commit()
            
            # Validate data
            rows_dict = dict()        
            for row in tbl:
                print(row, row.values())
                print(dict_to_str(row))
                rows_dict[ row['col1'] ] = row
            
            self.assertEqual(len(rows_dict), rows_to_insert1 + rows_to_insert2)
            
            for i in range(rows_to_insert2):
                try:
                    row = rows_dict[i+1] # Auto generate starts at 1 not 0
                    self.assertEqual(row['col1'], i+1) # Auto generate starts at 1 not 0
                    self.assertEqual(row['col2'], 'this is row {}'.format(i))
                    self.assertEqual(row['col3'], i/1000.0)
                    self.assertEqual(row['col4'], i/100000000.0)
                    self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
                except KeyError:
                    raise KeyError('Row key {} did not exist'.format(i))
            
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
        
    def testUpdate_partial_by_alt_key(self):
        tbl_name = 'testUpdate_by_alt_key'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              alt_key INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        for i in range(rows_to_insert):
            row=tbl.Row()
            row['col1'] = i
            row['alt_key'] = i + 100            
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        for i in range(rows_to_insert):
            #self.task.debug_sql()
            tbl.trace_sql = True
            tbl.update(updates_to_make={'col2':  'new col2 {}'.format(i)},
                       key_names=['alt_key'], 
                       key_values=[i+100],
                       )
            #self.task.debug_sql(False)
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row['col1'], row['col2'] )
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert)
        
        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], 'new col2 {}'.format(i))
            self.assertEqual(row['col3'], i/1000.0)
            self.assertEqual(row['col4'], i/100000000.0)
            self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
        
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
            
    def testUpdate_partial_by_key(self):
        tbl_name = 'testUpdate_partial_by_key'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        tbl.batch_size = 0
        for i in range(rows_to_insert):
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        for i in range(rows_to_insert):
            #self.task.debug_sql()
            tbl.trace_sql = True
            tbl.update(updates_to_make={'col2':  'new col2 {}'.format(i)},
                       key_values=[i],
                       )
            #self.task.debug_sql(False)
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row['col1'], row['col2'] )
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert)
        
        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], 'new col2 {}'.format(i))
            self.assertEqual(row['col3'], i/1000.0)
            self.assertEqual(row['col4'], i/100000000.0)
            self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
            
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
            
    def testUpdate_whole_by_key(self):
        tbl_name = 'testUpdate_whole_by_key'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        for i in range(rows_to_insert):
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        # Do the updates
        for i in range(rows_to_insert):
            #self.task.debug_sql()
            tbl.trace_sql = True
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'new col2 {}'.format(i)
            row['col3'] = i/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            tbl.update(updates_to_make=row)
            #self.task.debug_sql(False)
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row['col1'], row['col2'] )
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert)
        
        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], 'new col2 {}'.format(i))
            self.assertEqual(row['col3'], i/1000.0)
            self.assertEqual(row['col4'], i/100000000.0)
            self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
            
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
            
    def test_update_where_pk(self):
        tbl_name = 'test_update_where_pk'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        for i in range(rows_to_insert):
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        # Do the updates
        for i in range(rows_to_insert):
            #self.task.debug_sql()
            tbl.trace_sql = True
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'new col2 {}'.format(i)
            row['col3'] = i/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            tbl.update_where_pk(updates_to_make=row)
            #self.task.debug_sql(False)
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row['col1'], row['col2'] )
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert)
        
        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            self.assertEqual(row['col2'], 'new col2 {}'.format(i))
            self.assertEqual(row['col3'], i/1000.0)
            self.assertEqual(row['col4'], i/100000000.0)
            self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
            
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))

    def test_upsert_int_pk(self):
        tbl_name = 'test_upsert_int_pk'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB,
              del_flg TEXT
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        tbl.delete_flag = 'del_flg'
        for i in range(rows_to_insert):
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        # Do the updates
        tbl.track_source_rows = True
        row_key_values = list(range(rows_to_insert))
        # Add one value that will be inserted
        row_key_values.append(12)
        for i in row_key_values:
            # only upsert even rows
            if i % 2 == 0:
                #self.task.debug_sql()
                tbl.trace_sql = True
                row=tbl.Row()
                row['col1'] = i
                row['col2'] = 'new col2 {}'.format(i)
                row['col3'] = i/1000.0
                # leave out col 4
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                tbl.upsert(row)
                #self.task.debug_sql(False)
        tbl.commit()
        
        tbl.logically_delete_not_processed()
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        last_int_value = -1
        for row in tbl.order_by('col1'):
            if row['col1'] <= 9:  # Sequence only holds up from 0 to 9.
                self.assertEqual(last_int_value+1, row['col1'], 'Order by did not work')
                last_int_value = row['col1']
            self.log.debug(row.values_in_order())
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert + 1)
        
        
        for i in row_key_values:
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)
            if i % 2 == 0:
                self.assertEqual(row['col2'], 'new col2 {}'.format(i))
                self.assertEqual(row['del_flg'], 'N')
            else:
                self.assertEqual(row['col2'], 'this is row {}'.format(i))
                self.assertEqual(row['del_flg'], 'Y')
            self.assertEqual(row['col3'], i/1000.0)
            if i != 12:
                self.assertEqual(row['col4'], i/100000000.0)
            self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
            
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
            
    def test_upsert_int_dual_pk(self):
        tbl_name = 'test_upsert_int_dual_pk'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB,
              PRIMARY KEY (col1, col2)
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        for i in range(rows_to_insert):
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i * 1/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        # Do the updates / inserts
        for i in range(rows_to_insert):
            # only update even rows            
            #self.task.debug_sql()
            tbl.trace_sql = True
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'this is row {}'.format(i)
            if i % 2 == 0:
                row['col3'] = i * 1/10000.0
            else:
                row['col3'] = i * 1/1000.0
            # leave out col 4
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            tbl.upsert(row)
            #self.task.debug_sql(False)
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row['col1'], row['col2'] )
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert)
        
        for i in range(rows_to_insert):
            row = rows_dict[i]
            self.assertEqual(row['col1'], i)            
            self.assertEqual(row['col2'], 'this is row {}'.format(i))
            if i % 2 == 0:
                self.assertEqual(row['col3'], i * 1/10000.0)
            else:
                self.assertEqual(row['col3'], i * 1/1000.0)             
            self.assertEqual(row['col4'], i/100000000.0)
            self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
            
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
            
    def test_delete_int_pk(self):
        tbl_name = 'test_delete_int_pk'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB,
              PRIMARY KEY (col1)
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        for i in range(rows_to_insert):
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i * 1/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        # Do the deletes
        tbl.delete(key_values=[2])
        tbl.delete(key_values=[4])
        tbl.delete(key_names=['col3'], key_values=[6 * 1/1000.0])
        tbl.delete(key_names=['col2'], key_values=['this is row {}'.format(8)])
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row.values())
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert - 4)
        
        for i in range(rows_to_insert):
            if i in [2,4,6,8]:
                self.assertNotIn(i, rows_dict, 'row {} not deleted'.format(i))
            else:
                row = rows_dict[i]
                self.assertEqual(row['col1'], i)            
                self.assertEqual(row['col2'], 'this is row {}'.format(i))
                self.assertEqual(row['col3'], i * 1/1000.0) 
                self.assertEqual(row['col4'], i/100000000.0)
                self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
                
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))
        
    def test_delete_int_pk_no_batch(self):
        tbl_name = 'test_delete_int_pk_no_batch'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB,
              PRIMARY KEY (col1)
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        tbl = Table(self.task, 
                    self.mock_database, 
                    table_name= tbl_name)
        tbl.batch_size = 1
        for i in range(rows_to_insert):
            row=tbl.Row()
            row['col1'] = i
            row['col2'] = 'this is row {}'.format(i)
            row['col3'] = i * 1/1000.0
            row['col4'] = i/100000000.0
            row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
            
            tbl.insert(row)
        tbl.commit()
        
        # Do the deletes
        tbl.delete(key_values=[2])
        tbl.delete(key_values=[4])
        tbl.delete(key_names=['col3'], key_values=[6 * 1/1000.0])
        tbl.delete(key_names=['col2'], key_values=['this is row {}'.format(8)])
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row.values())
            rows_dict[ row['col1'] ] = row
        
        self.assertEqual(len(rows_dict), rows_to_insert - 4)
        
        for i in range(rows_to_insert):
            if i in [2,4,6,8]:
                self.assertNotIn(i, rows_dict, 'row {} not deleted'.format(i))
            else:
                row = rows_dict[i]
                self.assertEqual(row['col1'], i)            
                self.assertEqual(row['col2'], 'this is row {}'.format(i))
                self.assertEqual(row['col3'], i * 1/1000.0) 
                self.assertEqual(row['col4'], i/100000000.0)
                self.assertEqual(row['col5'], 'this is row {} blob'.format(i).encode('ascii'))
                
        self.mock_database.execute('DROP TABLE {}'.format(tbl_name))                          

    def testSanityCheck1(self):        
        src_tbl_name = 'testSanityCheck1s'
        self.log.info(src_tbl_name)
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2a TEXT,
              col3 REAL,
              col5 BLOB
           )
        """.format(src_tbl_name))
        
        tgt_tbl_name = 'testSanityCheck1t'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2a TEXT,
              col3 REAL,
              col4 NUMERIC
           )
        """.format(tgt_tbl_name))
        
        with Table(self.task, 
                   self.mock_database,  
                   table_name= src_tbl_name) as src_tbl:
            with Table(self.task, 
                   self.mock_database,  
                   table_name= tgt_tbl_name) as tgt_tbl:
                with mock.patch('bi_etl.components.etlcomponent.logging', autospec=True) as log:
                    tgt_tbl.log = log
                    tgt_tbl.sanity_check_source_mapping(src_tbl,
                                                        source_excludes=['col5'],
                                                        target_excludes=['col4'],
                                                        )
                    self.assertFalse(log.error.called,
                                     'unexpected error from sanity_check_source_mapping. {}'
                                     .format(log.mock_calls)
                                     )
                    self.assertFalse(log.warning.called,
                                     'unexpected warning from sanity_check_source_mapping. {}'
                                     .format(log.mock_calls)
                                     )
                    log.reset_mock()
                    
                    tgt_tbl.sanity_check_source_mapping(src_tbl,
                                                        source_excludes=['col5'],
                                                        target_excludes=['col4'],
                                                        )                    
                    self.assertFalse(log.error.called)
                    log.reset_mock()
                    
                    tgt_tbl.sanity_check_source_mapping(src_tbl,
                                                        target_excludes=['col4'],
                                                        )                    
                    self.assertFalse(log.error.called)
                    calls_str = '\n'.join([str(call) for call in log.mock_calls])                    
                    self.assertIn('col5', calls_str)        
                    log.reset_mock()
                    
                    tgt_tbl.sanity_check_source_mapping(src_tbl,
                                                        source_excludes=['col5'],
                                                        )
                    self.assertFalse(log.error.called)                    
                    calls_str = '\n'.join([str(call) for call in log.mock_calls])                    
                    self.assertIn('col4', calls_str)        
                    log.reset_mock()
                   
                    # Test using row and not source component
                    src_row = src_tbl.Row()
                    src_row['col1'] = 0
                    src_row['col2a'] = 0
                    src_row['col3'] = 0
                    src_row['col5'] = 0 
                    tgt_tbl.sanity_check_source_mapping(src_row,
                                                        source_excludes=['col5'],
                                                        target_excludes=['col4'],
                                                        )                    
                    # calls_str = '\n'.join([str(call) for call in log.mock_calls])
                    self.assertFalse(log.error.called,
                                     'unexpected error from sanity_check_source_mapping. {}'.format(log.mock_calls))
                    self.assertFalse(log.warning.called,
                                     'unexpected warning from sanity_check_source_mapping. {}'.format(log.mock_calls))
                    log.reset_mock()
                    
                    # Test using row and not source component
                    tgt_tbl.sanity_check_source_mapping(src_row,
                                                        source_excludes=['col5'],
                                                        target_excludes=['col4'],
                                                        )                    
                    # calls_str = '\n'.join([str(call) for call in log.mock_calls])
                    self.assertFalse(log.error.called,
                                     'unexpected error from sanity_check_source_mapping. {}'.format(log.mock_calls))
                    log.reset_mock()
                                                        
        self.mock_database.execute('DROP TABLE {}'.format(src_tbl_name))        
        self.mock_database.execute('DROP TABLE {}'.format(tgt_tbl_name))
        
    def testBuildRow1(self):        
        src_tbl_name = 'testBuildRow1s'
        self.log.info(src_tbl_name)
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2a TEXT,
              col3 REAL,              
              col4 NUMERIC,
              col5 BLOB,
              ext1 INT
           )
        """.format(src_tbl_name))
        
        tgt_tbl_name = 'testBuildRow1t'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2b TEXT,
              col3 REAL,              
              col4 NUMERIC,
              col5 BLOB,
              ext2 INT
           )
        """.format(tgt_tbl_name))
        
        with Table(self.task, 
                   self.mock_database,  
                   table_name= src_tbl_name) as src_tbl:
            with Table(self.task, 
                   self.mock_database,  
                   table_name= tgt_tbl_name) as tgt_tbl:
                with mock.patch('bi_etl.components.etlcomponent.logging', autospec=True) as log:
                    tgt_tbl.log = log
                    
                    src_row = src_tbl.Row()
                    src_row['col1'] = 0
                    src_row['col2a'] = 'example text'
                    src_row['col3'] = 123.12
                    src_row['col4'] = 1234.12
                    src_row['col5'] = 'this is row blob'.encode('ascii')

                    src_row.rename_columns({'col2a': 'col2b'})
                    tgt_row = tgt_tbl.build_row(src_row,
                                                source_excludes=['ext1'],
                                                target_excludes=['ext2'],
                                                )
                    self.assertFalse(log.error.called, 'unexpected error from sanity_check_source_mapping. {}'.format(log.mock_calls))
                    self.assertFalse(log.warning.called, 'unexpected warning from sanity_check_source_mapping. {}'.format(log.mock_calls))                    
                    self.assertEqual(tgt_row['col1'], 0)
                    self.assertEqual(tgt_row['col2b'], 'example text')
                    self.assertEqual(tgt_row['col3'], 123.12)
                    self.assertEqual(tgt_row['col4'], 1234.12)
                    self.assertEqual(tgt_row['col5'], 'this is row blob'.encode('ascii'))
                    self.assertNotIn('ext1', tgt_row)
                    self.assertNotIn('ext2', tgt_row)                                                    
                    log.reset_mock()
                    
                    src_row = src_tbl.Row()
                    src_row['col1'] = '0'
                    src_row['col2a'] = 123
                    src_row['col3'] = '123.12'
                    src_row['col4'] = '1,234.12'
                    src_row['col5'] = 123

                    src_row.rename_columns({'col2a': 'col2b'})
                    tgt_row = tgt_tbl.build_row(src_row,
                                                source_excludes=['ext1'],
                                                target_excludes=['ext2'],
                                                )
                    self.assertFalse(log.error.called, 'unexpected error from sanity_check_source_mapping. {}'.format(log.mock_calls))
                    self.assertFalse(log.warning.called, 'unexpected warning from sanity_check_source_mapping. {}'.format(log.mock_calls))                    
                    self.assertEqual(tgt_row['col1'], 0)
                    self.assertEqual(tgt_row['col2b'], '123')
                    self.assertAlmostEqual(tgt_row['col3'], 123.12, places=2)
                    self.assertEqual(tgt_row['col4'], Decimal('1234.12'))
                    self.assertEqual(tgt_row['col5'], b'123')
                    self.assertNotIn('ext1', tgt_row)
                    self.assertNotIn('ext2', tgt_row)
                    
    def testBuildRow2(self):
        self.mock_database.execute("""
                          CREATE TABLE {} (
                             col1 INT,
                             col2 TEXT,
                             col3 REAL,
                             col4 NUMERIC,
                             col5 BLOB
                          )
                       """.format('test'))
        tbl_name = 'testBuildRow2'

        with CSVReader(self.task, 
                       filedata=None,
                       logical_name='testBuildRow2_src',                                        
                       ) as src_tbl:
            with Table(self.task, 
                   self.mock_database,  
                   table_name= 'test',
                   ) as tgt_tbl:
                # Just here to help IDE know the data type
                assert isinstance(tgt_tbl, Table)
                
                with mock.patch('bi_etl.components.etlcomponent.logging', autospec=True) as log:
                    tgt_tbl.log = log
                    
                    # http://docs.sqlalchemy.org/en/latest/core/type_basics.html
                    tgt_tbl.table = sqlalchemy.schema.Table(tbl_name, 
                                                            self.mock_database,
                                                            Column('bool_col', BOOLEAN), 
                                                            Column('clob_col', CLOB),
                                                            Column('date_col', Date),
                                                            Column('datetime_col', DateTime),
                                                            Column('time_col', Time),
                                                            Column('enum_col', Enum(['a','b','c'])),
                                                            # We can't create table with this in sqlite
                                                            Column('float_col', Float),
                                                            Column('interval_col', Interval),
                                                            Column('large_binary_col', LargeBinary),
                                                            Column('numeric13_col', Numeric(13)),
                                                            Column('numeric25_col', Numeric(25)),
                                                            Column('numeric25_15_col', Numeric(25,15)),
                                                            Column('strin_10_col', String(10)),
                                                            quote=False
                                                            )
                    
                    src_row = src_tbl.Row()
                    src_row['bool_col'] = 0
                    src_row['clob_col'] = "It's a Python world."
                    src_row['date_col'] = '01/01/2001'
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
                    self.assertFalse(log.error.called, 'unexpected error from sanity_check_source_mapping. {}'.format(log.mock_calls))
                    self.assertFalse(log.warning.called, 'unexpected warning from sanity_check_source_mapping. {}'.format(log.mock_calls))                    
                    self.assertEqual(tgt_row['bool_col'], False)
                    self.assertEqual(tgt_row['clob_col'], "It's a Python world.")
                    self.assertEqual(tgt_row['date_col'], date(2001,1,1))
                    self.assertEqual(tgt_row['datetime_col'], datetime(2001,1,1,12,51,43))
                    self.assertEqual(tgt_row['time_col'], time(22,13,55))
                    self.assertEqual(tgt_row['enum_col'], 'a')
                    self.assertAlmostEqual(tgt_row['float_col'], 123.45, places=2)
                    self.assertEqual(tgt_row['interval_col'], timedelta(seconds=50))
                    self.assertEqual(tgt_row['large_binary_col'], "It's a Python world.".encode('ascii'))
                    self.assertEqual(tgt_row['numeric13_col'], 1234567890123)
                    self.assertEqual(tgt_row['numeric25_col'], 1234567890123456789012345)
                    self.assertAlmostEqual(tgt_row['numeric25_15_col'], Decimal('1234567890.123456789012345'), places=15)
                    self.assertEqual(tgt_row['strin_10_col'], '1234567890')
                    log.reset_mock()
                    
                    # Test datetime to datetime
                    src_row['datetime_col'] = datetime(2001,1,1,12,51,43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['datetime_col'], datetime(2001,1,1,12,51,43))
                    
                    # Test datetime to date
                    src_row['date_col'] = datetime(2001,1,1,12,51,43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['date_col'], date(2001,1,1))
                    
                    # Test date to date
                    src_row['date_col'] = date(2001,1,1)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['date_col'], date(2001,1,1))
                    
                    # Test datetime to time
                    src_row['time_col'] = datetime(2001,1,1,12,51,43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['time_col'], time(12,51,43))
                    
                    # Test time to time
                    src_row['time_col'] = time(12,51,43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['time_col'], time(12,51,43))
                    
                    # Test timedelta to interval
                    src_row['time_col'] = time(12,51,43)
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['time_col'], time(12,51,43))
                    
                    # Test force_ascii
                    tgt_tbl.force_ascii = True
                    src_row['strin_10_col'] = 'Ёarth'
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['strin_10_col'], '~arth')
                    tgt_tbl.force_ascii = False
                    
                    # Test decode bytes as ascii
                    src_row['strin_10_col'] = b'Earth'
                    tgt_row = tgt_tbl.build_row(src_row)
                    self.assertEqual(tgt_row['strin_10_col'], 'Earth')
                    
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
                    table_name= tbl_name)
        tbl.auto_generate_key = True
        tbl.batch_size = 5
        tbl.upsert_special_values_rows()
        tbl.commit()
        
        # Validate data
        rows_dict = dict()        
        for row in tbl:
            print(row, row.values())
            print(dict_to_str(row))
            rows_dict[ row['col1'] ] = row
        
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
        self.assertEqual(row['col2'], 'Not Applicable')
        self.assertEqual(row['col3'], -7777)
        self.assertEqual(row['col4'], -7777)
        
        row = rows_dict[-6666]
        self.assertEqual(row['col1'], -6666)
        self.assertEqual(row['col2'], 'Various')
        self.assertEqual(row['col3'], -6666)
        self.assertEqual(row['col4'], -6666)
    
    def test_upsert_special_values_rows(self):
        tbl_name = 'testInsertAndIterateWithKey'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT  PRIMARY KEY,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))
        self._test_upsert_special_values_rows_check(tbl_name)
        # Run a second time to make sure rows stay the same
        self._test_upsert_special_values_rows_check(tbl_name)
    
    def testInsertAndTruncate(self):
        tbl_name = 'testInsertAndTruncate'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        with Table(self.task, 
                   self.mock_database,  
                   table_name= tbl_name) as tbl:
            for i in range(rows_to_insert):
                row=tbl.Row()
                row['col1'] = i
                row['col2'] = 'this is row {}'.format(i)
                row['col3'] = i/1000.0
                row['col4'] = i/100000000.0
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                
                tbl.insert(row)
            tbl.commit()
            
            tbl.truncate()
            
            # Validate no data
            rows_dict = dict()        
            for row in tbl:
                print(row)
                rows_dict[ row['col1'] ] = row
                
            self.assertEqual(len(rows_dict), 0, 'Truncate did not remove rows')
            
    def testInsertAndRollback(self):
        tbl_name = 'testInsertAndRollback'
        self.mock_database.execute("""
           CREATE TABLE {} (
              col1 INT,
              col2 TEXT,
              col3 REAL,
              col4 NUMERIC,
              col5 BLOB
           )
        """.format(tbl_name))

        rows_to_insert = 10 
        with Table(self.task, 
                   self.mock_database,  
                   table_name= tbl_name) as tbl:
            for i in range(rows_to_insert):
                row=tbl.Row()
                row['col1'] = i
                row['col2'] = 'this is row {}'.format(i)
                row['col3'] = i/1000.0
                row['col4'] = i/100000000.0
                row['col5'] = 'this is row {} blob'.format(i).encode('ascii')
                
                tbl.insert(row)
            
            tbl.rollback()
            
            # Validate no data
            rows_dict = dict()        
            for row in tbl:
                print(row)
                rows_dict[ row['col1'] ] = row
                
            self.assertEqual(len(rows_dict), 0, 'Rollback did not remove rows')        
            
    
    # TODO: Test update_not_in_set, delete_not_in_set 

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    