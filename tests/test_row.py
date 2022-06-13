"""
Created on Mar 26, 2015

@author: Derek Wood
"""
import unittest
from collections import OrderedDict
from dataclasses import dataclass
from typing import NamedTuple

from pydantic import BaseModel
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.sqltypes import Integer, String, Numeric

from bi_etl.components.row.row import Row
from bi_etl.components.row.row_case_insensitive import RowCaseInsensitive
from bi_etl.components.row.row_iteration_header import RowIterationHeader
from bi_etl.components.row.row_iteration_header_case_insensitive import RowIterationHeaderCaseInsensitive
from bi_etl.conversions import nullif
from tests.dummy_etl_component import DummyETLComponent
from tests.mock_metadata import MockDatabaseMeta


class TestRow(unittest.TestCase):
    # Iteration counts tuned so that tests take less than a second
    create_performance_iterations = 5 * 10 ** 4
    get_performance_iterations = 10 ** 6
    set_existing_performance_iterations = 5 * 10 ** 4
    set_new_performance_rows = 5 * 10 ** 3
    set_new_performance_columns = 50

    def setUp(self, row_object=None):
        if row_object is None:
            self.Row_class = Row
            self.RowIterationHeader_class = RowIterationHeader
        else:
            self.Row_class = row_object
            if row_object == RowCaseInsensitive:
                self.RowIterationHeader_class = RowIterationHeaderCaseInsensitive
            else:
                self.RowIterationHeader_class = RowIterationHeader

        self.longMessage = True
        self.source1a = {
            'MixedCase': 1,
            'lower': 'two',
            'UPPER': 1.5,
        }
        self.source1b = {
            'MixedCase': 2,
            'lower': 'beta',
            'UPPER': 1234.567,
        }
        # Row1 will have a random (or unknown) column order based on the dict ordering
        self.source1_rows = [self.source1a, self.source1b]
        self.parent_component1 = DummyETLComponent(data=self.source1_rows)
        self.parent_component1.row_object = self.Row_class
        self.rows1 = [self._fix_row(row) for row in self.parent_component1]
        self.row1a = self.rows1[0]
        self.row1b = self.rows1[1]

        # Make a SQLAlchemy type of row (RowProxy)
        self.columns = ['MixedCase', 'lower', 'UPPER']

        # Row2 will have a known column order

        # noinspection PyPep8Naming
        class Row2_NT(NamedTuple):
            MixedCase: int
            lower: str
            UPPER: float

        self.source2a = Row2_NT(*self.source1a.values())
        self.source2b = Row2_NT(*self.source1b.values())
        self.source2_rows = [self.source2a, self.source2b]
        self.sa_row_name = 'sa_row'
        iteration_header = self.RowIterationHeader_class(logical_name=self.sa_row_name, columns_in_order=self.columns)
        self.parent_component2 = DummyETLComponent(iteration_header=iteration_header, data=self.source2_rows)
        self.parent_component2.row_object = self.Row_class
        self.rows2 = [self._fix_row(row) for row in self.parent_component2]
        self.row2a = self.rows2[0]
        self.row2b = self.rows2[1]

        # Row3 will have a known column order
        self.values3a = [1, 'two', 1.5]
        self.values3b = [2, 'beta', 1234.567]
        self.source3_rows = list()
        self.source3_rows.append(list(zip(self.columns, self.values3a)))
        self.source3_rows.append(list(zip(self.columns, self.values3b)))
        self.parent_component3 = DummyETLComponent(
            logical_name='row3',
            primary_key=['MixedCase'],
            data=self.source3_rows
            )
        self.parent_component3.row_object = self.Row_class
        self.rows3 = [self._fix_row(row) for row in self.parent_component3]
        self.row3a = self.rows3[0]
        self.row3b = self.rows3[1]

    def tearDown(self):
        pass

    def _fix_row(self, row):
        return row

    def test_as_dict(self):
        d = self.row1a.as_dict
        for k in self.source1a:
            self.assertEqual(
                d[k], self.source1a[k],
                f'row1[{k}] returned wrong value {d[k]} != {self.source1a[k]}'
                )

    def test_init_iter_zip(self):
        for k in self.columns:
            self.assertEqual(
                self.row1a[k], self.row3a[k],
                f"Value mismatch for {k} {self.row1b[k]} != {self.row3b[k]} (the iter zip init)"
                )

    def test_init_iter_zip_b(self):
        for k in self.columns:
            self.assertEqual(
                self.row1b[k], self.row3b[k],
                f"Value mismatch for {k} {self.row1b[k]} != {self.row3b[k]} (the iter zip init)"
                )

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

    def test_SA_init(self):
        self.assertEqual(self.row2a.name, self.sa_row_name, "row.name didn't return correct value")
        self.assertIn(self.sa_row_name, str(self.row2a), "str(Row) didn't return row name")

        self.assertEqual(self.row2a['MixedCase'], self.source2a.MixedCase)
        self.assertEqual(self.row2a['lower'], self.source2a.lower)
        self._test_getter_fail(self.row2a, 'LOWER')
        self.assertEqual(self.row2a['UPPER'], self.source2a.UPPER)
        self._test_getter_fail(self.row2a, 'upper')

        metadata = MockDatabaseMeta()

        mytable = Table(
            "mytable", metadata,
            Column('MixedCase', Integer, primary_key=True),
            Column('lower', String(50)),
            Column('UPPER', Numeric),
            )
        # Check that the column str representation is as we expect
        self.assertEqual(str(mytable.c.UPPER), 'mytable.UPPER')
        # Check that we can still get the value using the Column
        self.assertEqual(self.row2a[mytable.c.UPPER], self.source2a.UPPER)
        # Should also work on row1 which was not built with a RowProxy
        self.assertEqual(self.row1a[mytable.c.UPPER], self.source2a.UPPER)

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
        test_row.rename_columns({'lower': 'batman', 'UPPER': 'robin'})
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
        iteration_header = self.RowIterationHeader_class(columns_in_order=self.columns)
        row_list = list()
        for _ in range(desired_row_count):
            row_list.append(Row(iteration_header, data=self.source1a))
        return row_list

    def test_from_pandas(self):
        try:
            import pandas
            iteration_header = self.RowIterationHeader_class(logical_name='row4', primary_key=['MixedCase'])
            pandas_series = pandas.Series(data=self.values3a, index=self.columns)
            row4 = Row(iteration_header, pandas_series)
            for k in self.columns:
                self.assertIn(k, row4.column_set)
                self.assertEqual(self.row3a[k], row4[k])

        except ImportError:
            pass

    def test_from_dataclass(self):
        @dataclass
        class Row3_DC:
            MixedCase: int
            lower: str
            UPPER: float

        source = Row3_DC(**self.source1a)

        iteration_header = self.RowIterationHeader_class(logical_name='row5', primary_key=['MixedCase'])
        row5 = self.Row_class(iteration_header, data=source)
        for k in self.columns:
            self.assertIn(k, row5)
            self.assertEqual(self.source1a[k], row5[k])

    def test_from_pydantic(self):
        class Row3_PD(BaseModel):
            MixedCase: int
            lower: str
            UPPER: float

        source = Row3_PD(**self.source1a)

        iteration_header = self.RowIterationHeader_class(logical_name='row5', primary_key=['MixedCase'])
        row5 = self.Row_class(iteration_header, data=source)
        for k in self.columns:
            self.assertIn(k, row5)
            self.assertEqual(self.source1a[k], row5[k])

    def test_from_pydantic_explicit(self):
        class Row3_PD(BaseModel):
            MixedCase: int
            lower: str
            UPPER: float

        source = Row3_PD(**self.source1a)

        iteration_header = self.RowIterationHeader_class(logical_name='row5', primary_key=['MixedCase'])
        row5 = self.Row_class(iteration_header)
        row5.update_from_pydantic(source)
        for k in self.columns:
            self.assertIn(k, row5)
            self.assertEqual(self.source1a[k], row5[k])


if __name__ == "__main__":
    unittest.main()
