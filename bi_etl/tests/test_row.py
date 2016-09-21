"""
Created on Mar 26, 2015

@author: woodd
"""
import unittest
from collections import OrderedDict

from sqlalchemy.sql.schema import Column, Table, DEFAULT_NAMING_CONVENTION
from sqlalchemy.engine.result import RowProxy
from sqlalchemy.sql.sqltypes import Integer, String, Numeric
from bi_etl.timer import Timer
from bi_etl.components.row import Row
from bi_etl.components.row.row_parent import RowParent
from bi_etl.conversions import nullif

#pylint: disable=missing-docstring, protected-access

class TestRow(unittest.TestCase):
    ## Iteration counts tuned so that tests take less than a second
    create_performance_iterations = 3*10**4
    get_performance_iterations =  10**6
    set_existing_performance_iterations =  5*10**5
    set_new_performance_rows =  10**3
    set_new_performance_columns = 100

    def setUp(self):
        self.longMessage = True
        self.source1 = { 
                      'MixedCase': 1,
                      'lower': 'two',
                      'UPPER': 1.5,
                      }
        self.row1 = Row(self.source1)
        
        ## Make a SQLAlchemy type of row (RowProxy)
        self.source2 = self._make_row_from_dict(self.source1)
        self.row2 = Row(self.source2, name='my_row_name')
        
        ## Row3 will be our only row with a known order
        self.row3_parent = RowParent(logical_name='row3', primary_key=['MixedCase'])
        self.keys= ['MixedCase', 'lower', 'UPPER']
        self.values= [1, 'two', 1.5]
        self.row3 = Row(list(zip(self.keys, self.values)), parent=self.row3_parent)        
        
    def tearDown(self):
        pass
    
    def test_init_iter_zip(self):        
        for k in self.keys:
            self.assertEqual(self.row1[k], self.row3[k])
            
    def test_column_count(self):
        self.assertEqual(self.row1.column_count, 3, 'row1.column_count returned wrong value.')
        self.assertEqual(self.row2.column_count, 3, 'row2.column_count returned wrong value.')
        self.assertEqual(self.row3.column_count, 3, 'row3.column_count returned wrong value.')
    
    def test_getter_fail(self):
        test_bad_key = 'DoesNotExist'
        with self.assertRaises(KeyError) as e:
            _ = self.row1[test_bad_key]
        ## Check that we got a good exception message
        self.assertIn(test_bad_key, str(e.exception))

    def test_getter_mixed_case(self):
        mixed_case_str = 'MixedCase'         
        self.assertEqual(self.row1[mixed_case_str], 1)
    
    def _test_getter_single_case(self, name, contained_value):
        ## For lower case columns we can access it by any case
        self.assertEqual(self.row1[name], contained_value)
        self.assertEqual(self.row1[name.lower()], contained_value)
        self.assertEqual(self.row1[name.upper()], contained_value)
        self.assertEqual(self.row1[name.title()], contained_value)
    
    def test_getter_lower_case(self):
        ## For lower case columns we can access it by any case
        self._test_getter_single_case('LoWeR', 'two')        

    def test_getter_upper_case(self):
        ## For upper case columns we can access it by any case
        self._test_getter_single_case('uPpEr', 1.5)
        
    def test_setter_mixed_case(self):
        test_row = self.row2.clone()
        mixed_case_str = 'MixedCase'
        test_row[mixed_case_str] = 21         
        self.assertEqual(test_row[mixed_case_str], 21)
        
        test_row = self.row2.clone()
        test_row[mixed_case_str.lower()] = 21
        self.assertEqual(test_row[mixed_case_str], 21)
        self.assertEqual(test_row[mixed_case_str.lower()], 21)
    
    def _test_setter_single_case_example(self, name):
        ## For single case columns we can access it by any case
        test_row = self.row2.clone()
        test_row[name] = 21
        self.assertEqual(test_row[name], 21)
    
    def _test_setter_single_case(self, name):
        self._test_setter_single_case_example(name)
        self._test_setter_single_case_example(name.lower())
        self._test_setter_single_case_example(name.upper())
    
    def test_setter_lower_case(self):
        ## For lower case columns we can access it by any case
        self._test_setter_single_case('LoWeR')        

    def test_setter_upper_case(self):
        ## For upper case columns we can access it by any case
        self._test_setter_single_case('uPpEr')

    def test_transform_mixed_case(self):
        test_row = self.row2.clone()
        mixed_case_str = 'MixedCase'
        test_row.transform(mixed_case_str, str)         
        self.assertEqual(test_row[mixed_case_str], '1')
        
        test_row = self.row2.clone()
        test_row.transform(mixed_case_str.lower(), nullif, 'not_our_value')
        self.assertEqual(test_row[mixed_case_str], self.row2[mixed_case_str])
        self.assertEqual(test_row[mixed_case_str.lower()], self.row2[mixed_case_str])
        
        test_row.transform(mixed_case_str.lower(), nullif, 1)
        self.assertIsNone(test_row[mixed_case_str.lower()], 'nullif transform failed in test_transform_mixed_case')
    
    def _test_transform_single_case_example(self, name):
        ## For single case columns we can access it by any case
        test_row = self.row2.clone()
        test_row.transform(name, nullif, value_to_null='not_our_value')
        self.assertEqual(test_row[name], self.row2[name])
        
        test_row.transform(name, nullif, value_to_null=self.row2[name])
        self.assertIsNone(test_row[name], 'nullif transform failed in _test_transform_single_case_example')
    
    def _test_transform_single_case(self, name):
        self._test_transform_single_case_example(name)
        self._test_transform_single_case_example(name.lower())
        self._test_transform_single_case_example(name.upper())
    
    def test_transform_lower_case(self):
        ## For lower case columns we can access it by any case
        self._test_transform_single_case('LoWeR')        

    def test_transform_upper_case(self):
        ## For upper case columns we can access it by any case
        self._test_transform_single_case('uPpEr')

    def testDefaultName(self):
        row1Name= self.row1.name
        self.assertIsInstance(row1Name, str)
        for c in self.source1:
            self.assertIn(str(c).lower(), row1Name)
    
    def _make_row_from_dict(self, row_dict):
        class MockMeta(object):
            def __init__(self, keys):
                self.keys = keys   
        metadata = MockMeta(list(row_dict.keys()))
        def proc1(value):
            return value
        
        row = [v for v in row_dict.values()]        
        processors = [proc1 for _ in row_dict]  # @UnusedVariable
        keymap = {}
        index = 0
        for key in row_dict.keys():
            keymap[key] = (proc1, key, index)
            keymap[index] = (proc1, key, index)
            index += 1
        
        #return sqlalchemy.engine.result.RowProxy(metadata, #parent
        return RowProxy(metadata, #parent
                                                 row, # row
                                                 processors, #processors
                                                 keymap #keymap
                                                 )
    
    def _make_row_from_list(self, row_list):
        class MockMeta(object):
            def __init__(self, keys):
                self.keys = keys   
        
        keys = [t[0] for t in row_list]
        metadata = MockMeta(keys)
        def proc1(value):
            return value
        
        row = [t[1] for t in row_list]        
        processors = [proc1 for _ in row_list]
        index = 0
        keymap = {}
        for key, _ in row_list:
            keymap[key] = (proc1, key, index)
            keymap[index] = (proc1, key, index)
            index += 1
        
        #return sqlalchemy.engine.result.RowProxy(metadata, #parent
        return RowProxy(metadata, #parent
                                                 row, # row
                                                 processors, #processors
                                                 keymap #keymap
                                                 )
            
    def test_SA_init(self):        
        self.assertEqual(self.row2.name, 'my_row_name', "row.name didn't return correct value")
        self.assertIn('my_row_name', str(self.row2), "str(Row) didn't return row name")
        
        self.assertEqual( self.row2['MixedCase'], self.source2['MixedCase'] )
        self.assertEqual( self.row2['lower'], self.source2['lower'] )
        self.assertEqual( self.row2['lower'.upper()], self.source2['lower'] )
        self.assertEqual( self.row2['UPPER'], self.source2['UPPER'] )
        self.assertEqual( self.row2['UPPER'.lower()], self.source2['UPPER'] )
        class MockMeta(object):
            def __init__(self, tables= None):
                self.schema = None
                self.tables = tables or []
                self.naming_convention = DEFAULT_NAMING_CONVENTION
                self._fk_memos = []
                
            def _add_table(self, name, schema, table):
                pass
            def _remove_table(self, name, schema):
                pass
        metadata = MockMeta()
        mytable = Table("mytable", metadata,
                        Column('MixedCase', Integer, primary_key=True),
                        Column('lower', String(50)),
                        Column('UPPER', Numeric),
                   )
        ## Check that the column str representation is as we expect
        self.assertEqual( str(mytable.c.UPPER), 'mytable.UPPER' )
        ## Check that we can still get the value using the Column
        self.assertEqual( self.row2[mytable.c.UPPER], self.source2['UPPER'] )
        ## Should also work on row1 which was not built with a RowProxy
        self.assertEqual( self.row1[mytable.c.UPPER], self.source2['UPPER'] )

    def test_subset_and_columns(self):
        full_clone = self.row1.subset()
        self.assertEqual(full_clone.columns_in_order, self.row1.columns_in_order)
        self.assertEqual(full_clone.column_set, self.row1.column_set)
        
        clone = self.row1.subset()
        self.assertEqual(clone.columns_in_order, self.row1.columns_in_order)
        self.assertEqual(clone.column_set, self.row1.column_set)
        
        drop_mixed = self.row1.subset(exclude=['MixedCase'])
        self.assertIn('lower', drop_mixed)
        self.assertIn('UPPER', drop_mixed)
        self.assertEqual('upper' in drop_mixed.column_set, True)
        self.assertEqual('mixedcase' in drop_mixed.column_set, False)
        self.assertEqual(drop_mixed.column_count, 2, 'drop_mixed.column_count returned wrong value.')
        
        keep_lower = self.row1.subset(keep_only=['lower'])
        self.assertIn('lower', keep_lower.column_set)
        self.assertNotIn('upper', keep_lower.column_set)
        self.assertNotIn('mixedcase', keep_lower.column_set)
        self.assertEqual(keep_lower.column_count, 1, 'keep_lower.column_count returned wrong value.')                
        
    def test_rename_column(self):
        test_row = self.row1.clone()
        test_row.rename_column('MixedCase', 'batman')
        self.assertIn('batman', test_row)
        self.assertIn('lower', test_row)
        self.assertIn('UPPER', test_row)
        self.assertNotIn('MixedCase', test_row.columns)
        self.assertEqual(test_row.column_count, 3, 'test_row.column_count returned wrong value.')
        
    def test_rename_columns(self):
        test_row = self.row1.clone()
        test_row.rename_columns( {'lower': 'batman', 'UPPER':'robin'} )
        self.assertIn('batman', test_row)
        self.assertIn('robin', test_row)
        self.assertIn('MixedCase', test_row)
        self.assertNotIn('lower', test_row.columns)
        self.assertNotIn('UPPER', test_row.columns)
        self.assertEqual(test_row.column_count, 3, 'test_row.column_count returned wrong value.')
        
    def test_remove_columns(self):
        test_row = self.row3.subset()
        self.assertEqual(test_row.column_set, self.row3.column_set)
        
        test_row.remove_columns(['MixedCase'])
        self.assertIn('lower', test_row)
        self.assertIn('UPPER', test_row)
        self.assertNotIn('MixedCase', test_row.column_set)
        self.assertEqual(test_row.column_count, 2, 'test_row.column_count #1 returned wrong value.')
        self.assertEqual(test_row.columns_in_order(), ['lower', 'upper'])
        
        test_row['New'] = 'New Value'
        test_row.remove_columns(['lower','UPPER'])
        self.assertNotIn('lower', test_row)
        self.assertNotIn('upper', test_row)
        self.assertNotIn('mixedcase', test_row)
        self.assertIn('New', test_row)
        self.assertEqual(test_row['New'], 'New Value')
        self.assertEqual(test_row.column_count, 1, 'test_row.column_count #2 returned wrong value.')
        self.assertEqual(test_row.columns_in_order(), ['new'])
    
    def test_columns_in_order(self):
        ## We have to use the list of tuple init call to maintain the ordering
        test_row = self.row3
        columns_in_order = test_row.columns_in_order()
        expectedKeys = [k.lower() for k in self.keys]        
        self.assertEqual(expectedKeys, columns_in_order)
        
    def test_by_position(self):
        test_row = self.row3
        self.assertEqual(test_row.get_by_position(1), self.values[1-1]) ## -1 because positions are 1 based
        self.assertEqual(test_row.get_by_position(2), self.values[2-1]) ## -1 because positions are 1 based
        self.assertEqual(test_row.get_by_position(3), self.values[3-1]) ## -1 because positions are 1 based
        test_row = self.row3.clone()
        test_row.set_by_position(1, 'abc')
        self.assertEqual(test_row.get_by_position(1), 'abc')
        self.assertEqual(test_row[self.keys[1-1]], 'abc')  ## -1 because positions are 1 based
        
          
    def _test_create_performance(self):
        """
        Establish a baseline of init performance to make sure it doens't get worse
        """
        timer = Timer(start_running=True)
        row_lst = list()
        for _ in range(self.create_performance_iterations):
            row_lst.append( OrderedDict(self.source1) )            
        timer.stop()
        dict_seconds = timer.seconds_elapsed        
        del row_lst[:]        
        timer.reset()
        for _ in range(self.create_performance_iterations):
            row_lst.append( Row(self.source1) )            
        timer.stop()
        row_seconds = timer.seconds_elapsed
        print("create performance {:.2f} that of OrderedDict = {:f} per call".format(row_seconds / dict_seconds, row_seconds/self.create_performance_iterations))
        self.assertLessEqual(row_seconds, dict_seconds*2, "Row init did not meet performance goal")

    def _test_get_performance(self):
        """
        Establish a baseline of get performance to make sure it doens't get worse.
        We expect the extra checks we do here to make Row slower than OrderedDict.
        """
        od = OrderedDict(self.source1)
        timer = Timer(start_running=True)
        for _ in range(self.get_performance_iterations):
            _ = od['UPPER']            
        timer.stop()
        dict_seconds = timer.seconds_elapsed
        
        test_row = self.row1
        timer.reset()        
        for _ in range(self.get_performance_iterations):
            _ = test_row['UPPER']            
        timer.stop()
        row_seconds = timer.seconds_elapsed
        
        print("get performance {:.2f} that of OrderedDict = {:f} per call".format(row_seconds / dict_seconds, row_seconds/self.get_performance_iterations))
        self.assertLessEqual(row_seconds, dict_seconds*8, "Row get did not meet performance goal")
        
    def _test_set_existing_performance(self):
        """
        Establish a baseline of set existing value performance to make sure it doens't get worse
        We expect the extra checks we do here to make Row slower than OrderedDict.
        """
        timer = Timer(start_running=True)
        od = OrderedDict(self.source1)
        for _ in range(self.set_existing_performance_iterations):
            od['lower'] = 'new value'            
        timer.stop()
        dict_seconds = timer.seconds_elapsed
        timer.reset()        
        for _ in range(self.set_existing_performance_iterations):
            self.row1['lower'] = 'new value'            
        timer.stop()
        print("set existing performance {:.2f} that of OrderedDict  = {:f} per call".format(timer.seconds_elapsed / dict_seconds, timer.seconds_elapsed/self.set_existing_performance_iterations ))
        self.assertLessEqual(timer.seconds_elapsed, dict_seconds*2, "Row set did not meet performance goal")
        
    def _test_set_new_performance(self):
        """
        Establish a baseline of set new value performance to make sure it doens't get worse.
        We expect the extra checks we do here to make Row slower than OrderedDict.
        """
        timer = Timer(start_running=True)
        od = OrderedDict(self.source1)
        for _ in range(self.set_new_performance_rows):
            od = OrderedDict(self.source1)
            for i in range(self.set_new_performance_columns):
                od['new key {}'.format(i)] = 'new value {}'.format(i)            
        timer.stop()
        dict_seconds = timer.seconds_elapsed
        timer.reset()        
        for _ in range(self.set_new_performance_rows):
            row = Row()
            for i in range(self.set_new_performance_columns):
                row['new key {}'.format(i)] = 'new value {}'.format(i)            
        timer.stop()
        print("set new performance {:.2f} that of OrderedDict  = {:f} per call".format(timer.seconds_elapsed / dict_seconds, timer.seconds_elapsed/(self.set_new_performance_rows * (self.set_new_performance_columns))))
        self.assertLessEqual(timer.seconds_elapsed, dict_seconds*2, "Row set new did not meet performance goal")

if __name__ == "__main__":    
    unittest.main()
