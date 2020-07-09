"""
Created on Mar 26, 2015

@author: Derek Wood
"""
import unittest
from collections import OrderedDict

from sqlalchemy.engine.result import RowProxy
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.sqltypes import Integer, String, Numeric

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_case_insensitive import RowCaseInsensitive
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.conversions import nullif
from bi_etl.tests.dummy_etl_component import DummyETLComponent
from bi_etl.tests.mock_metadata import MockTableMeta, MockDatabaseMeta
from bi_etl.timer import Timer


class TestRow(unittest.TestCase):
    # Iteration counts tuned so that tests take less than a second
    create_performance_iterations = 5 * 10 ** 4
    get_performance_iterations = 10 ** 6
    set_existing_performance_iterations = 5 * 10 ** 4
    set_new_performance_rows = 5 * 10 ** 3
    set_new_performance_columns = 50

    def setUp(self, row_object=None):
        if row_object is None:
            self.row_object = Row
        else:
            self.row_object = row_object

        self.longMessage = True
        self.source1a = {
                      'MixedCase': 1,
                      'lower': 'two',
                      'UPPER': 1.5,
                      }
        self.source1b = {
            'MixedCase': 2,
            'lower':     'beta',
            'UPPER':     1234.567,
        }
        # Row1 will have a random (or unknown) column order based on the dict ordering
        self.source1_rows = [self.source1a, self.source1b]
        self.parent_component1 = DummyETLComponent(data=self.source1_rows)
        self.parent_component1.row_object = self.row_object
        self.rows1 = [row for row in self.parent_component1]
        self.row1a = self.rows1[0]
        self.row1b = self.rows1[1]

        # Make a SQLAlchemy type of row (RowProxy)
        self.columns = ['MixedCase', 'lower', 'UPPER']
        # Row2 will have a known column order
        self.source2a = self._make_row_from_dict(self.source1a)
        self.source2b = self._make_row_from_dict(self.source1b)
        self.source2_rows = [self.source2a, self.source2b]
        self.sa_row_name = 'sa_row'
        iteration_header = RowIterationHeader(logical_name=self.sa_row_name, columns_in_order=self.columns)
        self.parent_component2 = DummyETLComponent(iteration_header=iteration_header, data=self.source2_rows)
        self.parent_component2.row_object = self.row_object
        self.rows2 = [row for row in self.parent_component2]
        self.row2a = self.rows2[0]
        self.row2b = self.rows2[1]
        
        # Row3 will have a known column order
        self.values3a = [1, 'two', 1.5]
        self.values3b = [2, 'beta', 1234.567]
        self.source3_rows = list()
        self.source3_rows.append(list(zip(self.columns, self.values3a)))
        self.source3_rows.append(list(zip(self.columns, self.values3b)))
        self.parent_component3 = DummyETLComponent(logical_name='row3',
                                                   primary_key=['MixedCase'],
                                                   data=self.source3_rows)
        self.parent_component3.row_object = self.row_object
        self.rows3 = [row for row in self.parent_component3]
        self.row3a = self.rows3[0]
        self.row3b = self.rows3[1]

    def tearDown(self):
        pass

    def test_as_dict(self):
        d = self.row1a.as_dict
        for k in self.source1a:
            self.assertEqual(d[k], self.source1a[k],
                              'row1[{}] returned wrong value {} != {}'.format(k, d[k], self.source1a[k]))

    def test_init_iter_zip(self):
        for k in self.columns:
            self.assertEqual(self.row1a[k], self.row3a[k],
                             "Value mismatch for {k} {v1} != {v2} (the iter zip init)"
                             .format(k=k, v1=self.row1b[k], v2=self.row3b[k]))

    def test_init_iter_zip_b(self):
        for k in self.columns:
            self.assertEqual(self.row1b[k], self.row3b[k],
                             "Value mismatch for {k} {v1} != {v2} (the iter zip init)"
                             .format(k=k, v1=self.row1b[k], v2=self.row3b[k]))

    def test_init_iter_zip_b_columns(self):
        self.assertEqual(set(self.row1b.column_set), set(self.row3b.column_set))
        self.assertEqual(tuple(self.row3a.columns_in_order), tuple(self.row3b.columns_in_order))
            
    def test_column_count(self):
        self.assertEqual(self.row1a.column_count, 3, 'row1.column_count returned wrong value.')
        self.assertEqual(self.row2a.column_count, 3, 'row2.column_count returned wrong value.')
        self.assertEqual(self.row3a.column_count, 3, 'row3.column_count returned wrong value.')

    def _test_getter_fail(self, row, key):
        with self.assertRaises(KeyError) as e:
            _ = row[key]
        # Check that we got a good exception message
        self.assertIn(key, str(e.exception))

    def test_getter_fail_1(self):
        self._test_getter_fail(self.row1a, 'DoesNotExist')

    def test_getter_mixed_case(self):
        mixed_case_str = 'MixedCase'         
        self.assertEqual(self.row1a[mixed_case_str], 1)
    
    def _test_getter_single_case(self, name, contained_value):
        # For lower case columns we can access it by any case
        self.assertEqual(self.row1a[name], contained_value)

    def _test_setter_single_case_example(self, name):
        # For single case columns we can access it by any case
        test_row = self.row2a.clone()
        test_row[name] = 21
        self.assertEqual(test_row[name], 21)

    def _test_setter_single_case(self, name):
        self._test_setter_single_case_example(name)

    def test_transform_mixed_case(self):
        test_row = self.row2a.clone()
        mixed_case_str = 'MixedCase'
        test_row.transform(mixed_case_str, str)
        self.assertEqual(test_row[mixed_case_str], '1')

    def _test_transform_single_case_example(self, name):
        # For single case columns we can access it by any case
        test_row = self.row2a.clone()
        test_row.transform(name, nullif, value_to_null='not_our_value')
        self.assertEqual(test_row[name], self.row2a[name])

        test_row.transform(name, nullif, value_to_null=self.row2a[name])
        self.assertIsNone(test_row[name], 'nullif transform failed in _test_transform_single_case_example')

    def test_transform_lower_case(self):
        # For lower case columns we can access it by any case
        self._test_transform_single_case_example('lower')

    def test_transform_upper_case(self):
        # For upper case columns we can access it by any case
        self._test_transform_single_case_example('UPPER')

    def _make_row_from_dict(self, row_dict):
        metadata = MockTableMeta(list(row_dict.keys()))

        def proc1(value):
            return value

        row = [v for v in row_dict.values()]
        processors = [proc1 for _ in row_dict]
        keymap = {}
        index = 0
        for key in row_dict.keys():
            keymap[key] = (proc1, key, index)
            keymap[index] = (proc1, key, index)
            index += 1

        # return sqlalchemy.engine.result.RowProxy
        return RowProxy(metadata,  # parent
                        row,
                        processors,
                        keymap
                        )

    def _make_row_from_list(self, row_list):
        row_keys = [t[0] for t in row_list]
        metadata = MockTableMeta(row_keys)

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

        # return sqlalchemy.engine.result.RowProxy
        return RowProxy(metadata,  # parent
                        row,
                        processors,
                        keymap
                        )
            
    def test_SA_init(self):        
        self.assertEqual(self.row2a.name, self.sa_row_name, "row.name didn't return correct value")
        self.assertIn(self.sa_row_name, str(self.row2a), "str(Row) didn't return row name")

        self.assertEqual(self.row2a['MixedCase'], self.source2a['MixedCase'])
        self.assertEqual(self.row2a['lower'], self.source2a['lower'])
        self._test_getter_fail(self.row2a, 'LOWER')
        self.assertEqual(self.row2a['UPPER'], self.source2a['UPPER'])
        self._test_getter_fail(self.row2a, 'upper')

        metadata = MockDatabaseMeta()

        mytable = Table("mytable", metadata,
                        Column('MixedCase', Integer, primary_key=True),
                        Column('lower', String(50)),
                        Column('UPPER', Numeric),
                        )
        # Check that the column str representation is as we expect
        self.assertEqual(str(mytable.c.UPPER), 'mytable.UPPER')
        # Check that we can still get the value using the Column
        self.assertEqual(self.row2a[mytable.c.UPPER], self.source2a['UPPER'])
        # Should also work on row1 which was not built with a RowProxy
        self.assertEqual(self.row1a[mytable.c.UPPER], self.source2a['UPPER'])

    def test_subset_and_columns(self):
        full_clone = self.row1a.subset()
        self.assertEqual(full_clone.columns_in_order, self.row1a.columns_in_order)
        self.assertEqual(full_clone.column_set, self.row1a.column_set)

        clone = self.row1a.subset()
        self.assertEqual(clone.columns_in_order, self.row1a.columns_in_order)
        self.assertEqual(clone.column_set, self.row1a.column_set)

        drop_mixed = self.row1a.subset(exclude=['MixedCase'])
        self.assertIn('lower', drop_mixed)
        self.assertIn('UPPER', drop_mixed)
        self.assertEqual('UPPER' in drop_mixed.column_set, True)
        self.assertEqual('MixedCase' in drop_mixed.column_set, False)
        self.assertEqual(drop_mixed.column_count, 2, 'drop_mixed.column_count returned wrong value.')
        
        keep_lower = self.row1a.subset(keep_only=['lower'])
        self.assertIn('lower', keep_lower.column_set)
        self.assertNotIn('UPPER', keep_lower.column_set)
        self.assertNotIn('MixedCase', keep_lower.column_set)
        self.assertEqual(keep_lower.column_count, 1, 'keep_lower.column_count returned wrong value.')

    def test_rename_column(self):
        test_row = self.row1a.clone()
        test_row.rename_column('MixedCase', 'batman')
        self.assertIn('batman', test_row)
        self.assertIn('lower', test_row)
        self.assertIn('UPPER', test_row)
        self.assertNotIn('MixedCase', test_row.column_set)
        self.assertEqual(test_row.column_count, 3, 'test_row.column_count returned wrong value.')

    def test_rename_columns(self):
        test_row = self.row1a.clone()
        test_row.rename_columns( {'lower': 'batman', 'UPPER':'robin'} )
        self.assertIn('batman', test_row)
        self.assertIn('robin', test_row)
        self.assertIn('MixedCase', test_row)
        self.assertNotIn('lower', test_row.column_set)
        self.assertNotIn('UPPER', test_row.column_set)
        self.assertNotIn('lower', test_row.columns_in_order)
        self.assertNotIn('UPPER', test_row.columns_in_order)
        self.assertEqual(test_row.column_count, 3, 'test_row.column_count returned wrong value.')

    def test_remove_columns(self):
        test_row = self.row3a.subset()
        self.assertEqual(test_row.column_set, self.row3a.column_set)
        
        test_row.remove_columns(['MixedCase'])
        self.assertIn('lower', test_row)
        self.assertIn('UPPER', test_row)
        self.assertNotIn('MixedCase', test_row.column_set)
        self.assertEqual(test_row.column_count, 2, 'test_row.column_count #1 returned wrong value.')
        self.assertEqual(test_row.columns_in_order, ('lower', 'UPPER',))
        
        test_row['New'] = 'New Value'
        test_row.remove_columns(['lower', 'UPPER'])
        self.assertNotIn('lower', test_row)
        self.assertNotIn('UPPER', test_row)
        self.assertNotIn('MixedCase', test_row)
        self.assertIn('New', test_row)
        self.assertEqual(test_row['New'], 'New Value')
        self.assertEqual(test_row.column_count, 1, 'test_row.column_count #2 returned wrong value.')
        self.assertEqual(test_row.columns_in_order, ('New',))
    
    def test_columns_in_order(self):
        # We have to use the list of tuple init call to maintain the ordering
        test_row = self.row3a
        columns_in_order = test_row.columns_in_order
        self.assertEqual(tuple(self.columns), columns_in_order)
        
    def test_by_position(self):
        test_row = self.row3a
        self.assertEqual(test_row.get_by_position(1), self.values3a[1 - 1])  # -1 because positions are 1 based
        self.assertEqual(test_row.get_by_position(2), self.values3a[2 - 1])  # -1 because positions are 1 based
        self.assertEqual(test_row.get_by_position(3), self.values3a[3 - 1])  # -1 because positions are 1 based
        test_row = self.row3a.clone()
        test_row.set_by_position(1, 'abc')
        self.assertEqual(test_row.get_by_position(1), 'abc')
        self.assertEqual(test_row[self.columns[1 - 1]], 'abc')  # -1 because positions are 1 based
        self.assertEqual(test_row.get_by_position(2), self.values3a[2 - 1])  # -1 because positions are 1 based
        self.assertEqual(test_row.get_by_position(3), self.values3a[3 - 1])  # -1 because positions are 1 based

    def _create_ordered_dict_rows(self, desired_row_count):
        row_list = list()
        for _ in range(desired_row_count):
            row_list.append(OrderedDict(self.source1a))
        return row_list

    def _create_Row_rows(self, desired_row_count):
        iteration_header = RowIterationHeader(columns_in_order=self.columns)
        row_list = list()
        for _ in range(desired_row_count):
            row_list.append(Row(iteration_header, data=self.source1a))
        return row_list

    def test_from_pandas(self):
        try:
            import pandas
            iteration_header = RowIterationHeader(logical_name='row4', primary_key=['MixedCase'])
            pandas_series = pandas.Series(data=self.values3a, index=self.columns)
            row4 = Row(iteration_header, pandas_series)
            for k in self.columns:
                self.assertIn(k, row4.column_set)
                self.assertEqual(self.row3a[k], row4[k])

        except ImportError:
            pass


@unittest.skip("Not ready yet")
class TestRowCaseInsensitive(TestRow):
    def setUp(self, row_object=RowCaseInsensitive):
        super().setUp(row_object=row_object)

    def test_as_dict(self):
        d = self.row1a.as_dict
        for k in self.source1a:
            dk = k.lower()
            self.assertEqual(d[dk], self.source1a[k],
                              'row1[{}] returned wrong value {} != {}'.format(k, d[dk], self.source1a[k]))

    def test_getter_mixed_case(self):
        mixed_case_str = 'MixedCase'
        self.assertEqual(self.row1a[mixed_case_str], 1)

    def test_getter_mixed_case_lower(self):
        mixed_case_str = 'MixedCase'.lower()
        self.assertEqual(self.row1a[mixed_case_str], 1)

    def test_getter_mixed_case_upper(self):
        mixed_case_str = 'MixedCase'.upper()
        self.assertEqual(self.row1a[mixed_case_str], 1)

    def _test_getter_single_case(self, name, contained_value):
        # For lower case columns we can access it by any case
        self.assertEqual(self.row1a[name], contained_value)
        self.assertEqual(self.row1a[name.lower()], contained_value)
        self.assertEqual(self.row1a[name.upper()], contained_value)
        self.assertEqual(self.row1a[name.title()], contained_value)

    def test_getter_lower_case(self):
        # For lower case columns we can access it by any case
        self._test_getter_single_case('LoWeR', 'two')

    def test_getter_upper_case(self):
        # For upper case columns we can access it by any case
        self._test_getter_single_case('uPpEr', 1.5)

    def test_setter_mixed_case(self):
        test_row = self.row2a.clone()
        mixed_case_str = 'MixedCase'
        test_row[mixed_case_str] = 21
        self.assertEqual(test_row[mixed_case_str], 21)

        test_row = self.row2a.clone()
        test_row[mixed_case_str.lower()] = 21
        self.assertEqual(test_row[mixed_case_str], 21)
        self.assertEqual(test_row[mixed_case_str.lower()], 21)

    def _test_setter_single_case_example(self, name):
        # For single case columns we can access it by any case
        test_row = self.row2a.clone()
        test_row[name] = 21
        self.assertEqual(test_row[name], 21)

    def _test_setter_single_case(self, name):
        self._test_setter_single_case_example(name)
        self._test_setter_single_case_example(name.lower())
        self._test_setter_single_case_example(name.upper())

    def test_setter_lower_case(self):
        # For lower case columns we can access it by any case
        self._test_setter_single_case('LoWeR')

    def test_setter_upper_case(self):
        # For upper case columns we can access it by any case
        self._test_setter_single_case('uPpEr')

    def test_transform_mixed_case(self):
        test_row = self.row2a.clone()
        mixed_case_str = 'MixedCase'
        test_row.transform(mixed_case_str, str)
        self.assertEqual(test_row[mixed_case_str], '1')

    def test_transform_mixed_case_lower(self):
        test_row = self.row2a.clone()
        mixed_case_str = 'MixedCase'.lower()
        test_row.transform(mixed_case_str, nullif, 'not_our_value')
        self.assertEqual(test_row['MixedCase'], self.row2a[mixed_case_str])
        self.assertEqual(test_row[mixed_case_str], self.row2a['MixedCase'])

        test_row.transform(mixed_case_str, nullif, 1)
        self.assertIsNone(test_row[mixed_case_str], 'nullif transform failed in test_transform_mixed_case_lower')

    def test_transform_mixed_case_upper(self):
        test_row = self.row2a.clone()
        mixed_case_str = 'MixedCase'.upper()
        test_row.transform(mixed_case_str, nullif, ('not_our_value'))
        self.assertEqual(test_row['MixedCase'], self.row2a[mixed_case_str])
        self.assertEqual(test_row[mixed_case_str], self.row2a['MixedCase'])

    def _test_transform_single_case_example(self, name):
        # For single case columns we can access it by any case
        test_row = self.row2a.clone()
        test_row.transform(name, nullif, value_to_null='not_our_value')
        self.assertEqual(test_row[name], self.row2a[name])

        test_row.transform(name, nullif, value_to_null=self.row2a[name])
        self.assertIsNone(test_row[name], 'nullif transform failed in _test_transform_single_case_example')

    def _test_transform_single_case(self, name):
        self._test_transform_single_case_example(name)
        self._test_transform_single_case_example(name.lower())
        self._test_transform_single_case_example(name.upper())

    def test_transform_lower_case(self):
        # For lower case columns we can access it by any case
        self._test_transform_single_case('LoWeR')

    def test_transform_upper_case(self):
        # For upper case columns we can access it by any case
        self._test_transform_single_case('uPpEr')

    def _make_row_from_dict(self, row_dict):
        metadata = MockTableMeta(list(row_dict.keys()))

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

        # return sqlalchemy.engine.result.RowProxy
        return RowProxy(metadata,  # parent
                        row,
                        processors,
                        keymap
                        )

    def _make_row_from_list(self, row_list):
        columns = [t[0] for t in row_list]
        metadata = MockTableMeta(columns)

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

        # return sqlalchemy.engine.result.RowProxy
        return RowProxy(metadata,  # parent
                        row,
                        processors,
                        keymap
                        )

    def test_SA_init(self):
        self.assertEqual(self.row2a['MixedCase'], self.source2a['MixedCase'])
        self.assertEqual(self.row2a['lower'], self.source2a['lower'])
        self.assertEqual(self.row2a['lower'.upper()], self.source2a['lower'])
        self.assertEqual(self.row2a['UPPER'], self.source2a['UPPER'])
        self.assertEqual(self.row2a['UPPER'.lower()], self.source2a['UPPER'])

        metadata = MockDatabaseMeta()

        my_table = Table("mytable", metadata,
                         Column('MixedCase', Integer, primary_key=True),
                         Column('lower', String(50)),
                         Column('UPPER', Numeric),
                         )
        # Check that the column str representation is as we expect
        self.assertEqual(str(my_table.c.UPPER), 'mytable.UPPER')
        # Check that we can still get the value using the Column
        self.assertEqual(self.row2a[my_table.c.UPPER], self.source2a['UPPER'])
        # Should also work on row1 which was not built with a RowProxy
        self.assertEqual(self.row1a[my_table.c.UPPER], self.source2a['UPPER'])

    def test_subset_and_columns(self):
        full_clone = self.row1a.subset()
        self.assertEqual(full_clone.columns_in_order, self.row1a.columns_in_order)
        self.assertEqual(full_clone.column_set, self.row1a.column_set)

        clone = self.row1a.subset()
        self.assertEqual(clone.columns_in_order, self.row1a.columns_in_order)
        self.assertEqual(clone.column_set, self.row1a.column_set)

        drop_mixed = self.row1a.subset(exclude=['MixedCase'])
        self.assertIn('lower', drop_mixed)
        self.assertIn('UPPER', drop_mixed)
        self.assertEqual('upper' in drop_mixed.column_set, True)
        self.assertEqual('mixedcase' in drop_mixed.column_set, False)
        self.assertEqual(drop_mixed.column_count, 2, 'drop_mixed.column_count returned wrong value.')

        keep_lower = self.row1a.subset(keep_only=['lower'])
        self.assertIn('lower', keep_lower.column_set)
        self.assertNotIn('upper', keep_lower.column_set)
        self.assertNotIn('mixedcase', keep_lower.column_set)
        self.assertEqual(keep_lower.column_count, 1, 'keep_lower.column_count returned wrong value.')

    def test_rename_column(self):
        test_row = self.row1a.clone()
        test_row.rename_column('MixedCase', 'batman')
        self.assertIn('batman', test_row)
        self.assertIn('lower', test_row)
        self.assertIn('UPPER', test_row)
        self.assertNotIn('MixedCase', test_row.column_set)
        self.assertNotIn('MixedCase', test_row.columns_in_order)
        self.assertEqual(test_row.column_count, 3, 'test_row.column_count returned wrong value.')

    def test_rename_columns(self):
        test_row = self.row1a.clone()
        test_row.rename_columns({'lower': 'batman', 'UPPER': 'robin'})
        self.assertIn('batman', test_row)
        self.assertIn('robin', test_row)
        self.assertIn('MixedCase', test_row)
        self.assertNotIn('lower', test_row.column_set)
        self.assertNotIn('UPPER', test_row.column_set)
        self.assertEqual(test_row.column_count, 3, 'test_row.column_count returned wrong value.')

    def test_remove_columns(self):
        test_row = self.row3a.subset()
        self.assertEqual(test_row.column_set, self.row3a.column_set)

        test_row.remove_columns(['MixedCase'])
        self.assertIn('lower', test_row)
        self.assertIn('UPPER', test_row)
        self.assertNotIn('MixedCase', test_row.column_set)
        self.assertEqual(test_row.column_count, 2, 'test_row.column_count #1 returned wrong value.')
        self.assertEqual(test_row.columns_in_order, ['lower', 'upper'])

        test_row['New'] = 'New Value'
        test_row.remove_columns(['lower', 'UPPER'])
        self.assertNotIn('lower', test_row)
        self.assertNotIn('upper', test_row)
        self.assertNotIn('mixedcase', test_row)
        self.assertIn('New', test_row)
        self.assertEqual(test_row['New'], 'New Value')
        self.assertEqual(test_row.column_count, 1, 'test_row.column_count #2 returned wrong value.')
        self.assertEqual(test_row.columns_in_order, ['new'])

    def test_columns_in_order(self):
        # We have to use the list of tuple init call to maintain the ordering
        test_row = self.row3a
        columns_in_order = test_row.columns_in_order
        expected_keys = [k.lower() for k in self.columns]
        for expected_name, actual_name in zip(expected_keys, columns_in_order):
            self.assertEqual(expected_name, actual_name.lower())

    def test_by_position(self):
        test_row = self.row3a
        self.assertEqual(test_row.get_by_position(1), self.values3a[1 - 1])  # -1 because positions are 1 based
        self.assertEqual(test_row.get_by_position(2), self.values3a[2 - 1])  # -1 because positions are 1 based
        self.assertEqual(test_row.get_by_position(3), self.values3a[3 - 1])  # -1 because positions are 1 based
        test_row = self.row3a.clone()
        test_row.set_by_position(1, 'abc')
        self.assertEqual(test_row.get_by_position(1), 'abc')
        self.assertEqual(test_row[self.columns[1 - 1]], 'abc')  # -1 because positions are 1 based

    def _test_create_performance(self):
        """
        Establish a baseline of init performance to make sure it doens't get worse
        """
        timer = Timer(start_running=True)
        row_lst = list()
        for _ in range(self.create_performance_iterations):
            row_lst.append(OrderedDict(self.source1a))
        timer.stop()
        dict_seconds = timer.seconds_elapsed
        del row_lst[:]
        timer.reset()
        for _ in range(self.create_performance_iterations):
            row_lst.append(RowCaseInsensitive(self.source1a))
        timer.stop()
        row_seconds = timer.seconds_elapsed
        print("create performance {:.2f} that of OrderedDict = {:f} per call"
              .format(row_seconds / dict_seconds, row_seconds / self.create_performance_iterations))
        self.assertLessEqual(row_seconds, dict_seconds * 2, "Row init did not meet performance goal")

    def _test_get_performance(self):
        """
        Establish a baseline of get performance to make sure it doens't get worse.
        We expect the extra checks we do here to make Row slower than OrderedDict.
        """
        od = OrderedDict(self.source1a)
        timer = Timer(start_running=True)
        for _ in range(self.get_performance_iterations):
            _ = od['UPPER']
        timer.stop()
        dict_seconds = timer.seconds_elapsed

        test_row = self.row1a
        timer.reset()
        for _ in range(self.get_performance_iterations):
            _ = test_row['UPPER']
        timer.stop()
        row_seconds = timer.seconds_elapsed

        print("get performance {:.2f} that of OrderedDict = {:f} per call"
              .format(row_seconds / dict_seconds, row_seconds / self.get_performance_iterations))
        self.assertLessEqual(row_seconds, dict_seconds * 8, "Row get did not meet performance goal")

    def _test_set_existing_performance(self):
        """
        Establish a baseline of set existing value performance to make sure it doens't get worse
        We expect the extra checks we do here to make Row slower than OrderedDict.
        """
        timer = Timer(start_running=True)
        od = OrderedDict(self.source1a)
        for _ in range(self.set_existing_performance_iterations):
            od['lower'] = 'new value'
        timer.stop()
        dict_seconds = timer.seconds_elapsed
        timer.reset()
        for _ in range(self.set_existing_performance_iterations):
            self.row1a['lower'] = 'new value'
        timer.stop()
        print("set existing performance {:.2f} that of OrderedDict  = {:f} per call".format(
            timer.seconds_elapsed / dict_seconds, timer.seconds_elapsed / self.set_existing_performance_iterations))
        self.assertLessEqual(timer.seconds_elapsed, dict_seconds * 2, "Row set did not meet performance goal")

    def _test_set_new_performance(self):
        """
        Establish a baseline of set new value performance to make sure it doens't get worse.
        We expect the extra checks we do here to make Row slower than OrderedDict.
        """
        timer = Timer(start_running=True)
        od = OrderedDict(self.source1a)
        for _ in range(self.set_new_performance_rows):
            od = OrderedDict(self.source1a)
            for i in range(self.set_new_performance_columns):
                od['new key {}'.format(i)] = 'new value {}'.format(i)
        timer.stop()
        dict_seconds = timer.seconds_elapsed
        timer.reset()
        iteration_header = RowIterationHeader(logical_name='_test_set_new_performance')
        for _ in range(self.set_new_performance_rows):
            row = RowCaseInsensitive(iteration_header=iteration_header)
            for i in range(self.set_new_performance_columns):
                row['new key {}'.format(i)] = 'new value {}'.format(i)
        timer.stop()
        print("set new performance {:.2f} that of OrderedDict  = {:f} per call".format(
            timer.seconds_elapsed / dict_seconds,
            timer.seconds_elapsed / (self.set_new_performance_rows * (self.set_new_performance_columns))))
        self.assertLessEqual(timer.seconds_elapsed, dict_seconds * 2, "Row set new did not meet performance goal")


if __name__ == "__main__":
    unittest.main()
