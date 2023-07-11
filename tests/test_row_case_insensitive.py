"""
Created on Mar 26, 2015

@author: Derek Wood
"""

from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.sqltypes import Integer, String, Numeric

from bi_etl.components.row.row_case_insensitive import RowCaseInsensitive
from bi_etl.components.row.row_iteration_header_case_insensitive import RowIterationHeaderCaseInsensitive
from bi_etl.conversions import nullif
from tests.mock_metadata import MockDatabaseMeta
from tests.test_row import TestRow


#@unittest.skip("Not ready yet")
class TestRowCaseInsensitive(TestRow):
    def setUp(self, row_object=RowCaseInsensitive):
        super().setUp(row_object=row_object)

    def _fix_row(self, row):
        if not isinstance(row.iteration_header, RowIterationHeaderCaseInsensitive):
            new_header = RowIterationHeaderCaseInsensitive.from_other_header(
                row.iteration_header
            )
            new_row = RowCaseInsensitive(
                iteration_header=new_header,
            )
            new_row.update_from_values(row.values())
            return new_row
        else:
            return row

    def test_as_dict(self):
        d = self.row1a.as_dict
        for k in self.source1a:
            self.assertEqual(
                # RowCaseInsensitive.as_dict returns lower case names
                d[k.lower()], self.source1a[k],
                f'row1[{k}] returned wrong value {d[k]} != {self.source1a[k]}'
                )


    def test_init_iter_zip(self):
        for k in self.columns:
            for dk in [k, k.lower(), k.upper()]:
                self.assertEqual(
                    self.row1a[dk], self.row3a[dk],
                    f"Value mismatch for {k} {self.row1b[dk]} != {self.row3b[dk]} (the iter zip init)"
                    )

    def test_getter_mixed_case(self):
        k = 'MixedCase'
        for dk in [k, k.lower(), k.upper()]:
            self.assertEqual(self.row1a[dk], 1)

    def _test_getter_single_case(self, name: str, contained_value):
        # For lower case columns we can access it by any case
        for dk in [name, name.lower(), name.upper(), name.title()]:
            self.assertEqual(self.row1a[dk], contained_value)

    def test_getter_lower_case(self):
        # For lower case columns we can access it by any case
        self._test_getter_single_case('LoWeR', 'two')

    def test_getter_upper_case(self):
        # For upper case columns we can access it by any case
        self._test_getter_single_case('uPpEr', 1.5)

    def _test_getter_fail(self, row, key):
        with self.assertRaises(KeyError) as e:
            _ = row[key]
        # Check that we got a good exception message
        self.assertIn(key.lower(), str(e.exception).lower())

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
        test_row.transform(mixed_case_str, nullif, ('not_our_value',))
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

    def test_SA_init(self):
        self.assertEqual(self.row2a['MixedCase'], self.source2a.MixedCase)
        self.assertEqual(self.row2a['lower'], self.source2a.lower)
        self.assertEqual(self.row2a['lower'.upper()], self.source2a.lower)
        self.assertEqual(self.row2a['UPPER'], self.source2a.UPPER)
        self.assertEqual(self.row2a['UPPER'.lower()], self.source2a.UPPER)

        metadata = MockDatabaseMeta()

        my_table = Table("mytable", metadata,
                         Column('MixedCase', Integer, primary_key=True),
                         Column('lower', String(50)),
                         Column('UPPER', Numeric),
                         )
        # Check that the column str representation is as we expect
        self.assertEqual(str(my_table.c.UPPER), 'mytable.UPPER')
        # Check that we can still get the value using the Column
        self.assertEqual(self.row2a[my_table.c.UPPER], self.source2a.UPPER)
        # Should also work on row1 which was not built with a RowProxy
        self.assertEqual(self.row1a[my_table.c.UPPER], self.source2a.UPPER)

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
        test_row.rename_columns({'loWer': 'batman', 'UpPeR': 'robin'})
        self.assertIn('batman', test_row)
        self.assertIn('robin', test_row)
        self.assertIn('MixedCase', test_row)
        self.assertNotIn('lower', test_row.column_set)
        self.assertNotIn('loWer', test_row.column_set)
        self.assertNotIn('UPPER', test_row.column_set)
        self.assertNotIn('UpPeR', test_row.column_set)
        self.assertEqual(test_row.column_count, 3, 'test_row.column_count returned wrong value.')

    def test_remove_columns(self):
        test_row = self.row3a.subset()
        self.assertEqual(test_row.column_set, self.row3a.column_set)

        test_row.remove_columns(['MixedCase'])
        self.assertIn('lower', test_row)
        self.assertIn('UPPER', test_row)
        self.assertNotIn('MixedCase', test_row)
        self.assertEqual(test_row.column_count, 2, 'test_row.column_count #1 returned wrong value.')
        self.assertEqual(test_row.columns_in_order, ('lower', 'upper'))

        test_row['New'] = 'New Value'
        test_row.remove_columns(['lowEr', 'UppER'])
        self.assertNotIn('lower', test_row)
        self.assertNotIn('LOWER', test_row)
        self.assertNotIn('upper', test_row)
        self.assertNotIn('UPPER', test_row)
        self.assertNotIn('mixedcase', test_row)
        self.assertNotIn('MixedCase', test_row)
        self.assertIn('New', test_row)
        self.assertEqual(test_row['New'], 'New Value')
        self.assertEqual(test_row.column_count, 1, 'test_row.column_count #2 returned wrong value.')
        self.assertEqual(test_row.columns_in_order, ('new',))

    def test_columns_in_order(self):
        # We have to use the list of tuple init call to maintain the ordering
        test_row = self.row3a
        columns_in_order = test_row.columns_in_order
        expected_keys = [k.lower() for k in self.columns]
        for expected_name, actual_name in zip(expected_keys, columns_in_order):
            self.assertEqual(expected_name, actual_name.lower())

# Remove TestRow so it is not also tested here
del TestRow