# -*- coding: utf-8 -*-
"""
Created on Nov 30, 2015

@author: Derek Wood
"""
import inspect
import os
import shutil
import unittest
from tempfile import TemporaryDirectory

from bi_etl.components.xlsx_reader import XLSXReader
from bi_etl.scheduler.task import ETLTask
from tests.config_for_tests import build_config


class TestXLSReader(unittest.TestCase):
    @staticmethod
    def get_package_path():
        module_path = inspect.getfile(TestXLSReader)
        (tests_path, _) = os.path.split(module_path)
        return tests_path

    @staticmethod
    def get_test_files_path():
        return os.path.join(TestXLSReader.get_package_path(), 'test_files_xlsx')

    def assertRegexMsg(self, actual, expected_re):
        expected_str = expected_re.replace('\n', '\\n\n')
        actual_str = actual.replace('\n', '\\n\n')
        msg = f"---\nexpected:\n{expected_str}\n---\ngot:\n{actual_str}\n---\n"
        self.assertRegex(actual, expected_re, msg)

    def setUp(self):
        config = build_config()
        self.task = ETLTask(config=config)
        self.test_files_path = self.get_test_files_path()

    def tearDown(self):
        pass

    # noinspection PyTypeChecker
    def test_simple_with_where(self):
        src_file = os.path.join(self.test_files_path, 'simple.xlsx')
        # print(srcFile)
        logical_name = os.path.basename(src_file)
        quoted_src_file = repr(src_file)
        # print(quotedSrcFile)
        self.maxDiff = None
        # Test passing opened file
        with XLSXReader(self.task, src_file) as src:
            self.assertEqual(src.column_names, ['str', 'int', 'float', 'date', 'unicode'])
            expected_repr = "XLSXReader(simple.xlsx)"
            self.assertEqual(repr(src), expected_repr)
            src_iter = src.where(criteria_dict={'str': 'Bob'})
            row = next(src_iter)
            self.assertEqual(src.rows_read, 1, 'rows_read error')
            self.assertEqual(row['str'], 'Bob')
            self.assertEqual(row['int'], 1)
            self.assertAlmostEqual(row['float'], 1.5, places=5)
            self.assertEqual(row['date'], '1/1/2000')
            self.assertEqual(row['unicode'], u'©Me')
            try:
                _ = next(src_iter)
                self.fail('StopIteration expected at end of file')
            except StopIteration:
                pass

    def test_simple(self):
        src_file = os.path.join(TestXLSReader.get_test_files_path(), 'simple.xlsx')
        logical_name = os.path.basename(src_file)
        # print(srcFile)
        quoted_src_file = repr(src_file)
        # print(quotedSrcFile)
        self.maxDiff = None
        # Test passing string filename and encoding
        with XLSXReader(self.task, src_file, encoding='utf-8') as src:
            self.assertEqual(src.column_names, ['str', 'int', 'float', 'date', 'unicode'])
            expected_repr = "XLSXReader(simple.xlsx)"
            self.assertEqual(repr(src), expected_repr)
            src_iter = iter(src)
            row = next(src_iter)
            self.assertEqual(src.line_num, 2, 'line_num error')
            self.assertEqual(row['str'], 'Bob')
            self.assertEqual(row['int'], 1)
            self.assertAlmostEqual(row['float'], 1.5, places=5)
            self.assertEqual(row['date'], '1/1/2000')
            self.assertEqual(row['unicode'], u'©Me')
            row = next(src_iter)
            self.assertEqual(src.line_num, 3, 'line_num error')
            self.assertEqual(row['str'], 'Jane')
            self.assertEqual(row['int'], 100)
            self.assertAlmostEqual(row['float'], 2.123, places=5)
            self.assertEqual(row['date'], '2/3/2010')
            self.assertEqual(row['unicode'], u'∞ diversity')
            row = next(src_iter)
            self.assertEqual(src.line_num, 4, 'line_num error')
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['int'], 100000)
            self.assertAlmostEqual(row['float'], 5.12312, places=5)
            self.assertEqual(row['date'], '3/4/2015')
            self.assertEqual(row['unicode'], u'Middlӭ Ёarth')
            try:
                _ = next(src_iter)
                self.fail('StopIteration expected at end of file')
            except StopIteration:
                pass

    def test_large_values(self):
        src_file = os.path.join(self.test_files_path, 'large_values.xlsx')
        # Test passing string filename and encoding
        with XLSXReader(self.task, src_file) as src:
            self.assertEqual(['str', 'unicode', 'after'], src.column_names)
            src_iter = iter(src)
            row = next(src_iter)
            long_value = row['unicode']
            self.assertEqual(32767, len(long_value))
            # Ending char is !
            assert (long_value.startswith(u'Middlӭ Ёarth'))
            self.assertEqual(long_value[-1], '!')
            self.assertEqual(row['after'], 'after_val')

    def test_simple_start_middle(self):
        src_file = os.path.join(self.test_files_path, 'simple.xlsx')
        self.maxDiff = None
        with XLSXReader(self.task, src_file) as src:
            src.start_row = 4
            src.restkey = 'extraStuff'
            src.column_names = ['str', 'int', 'float', 'date', 'unicode']
            self.assertEqual(src.column_names, ['str', 'int', 'float', 'date', 'unicode'])
            expected_repr = f"XLSXReader(simple.xlsx)"
            self.assertEqual(repr(src), expected_repr)
            src_iter = iter(src)
            row = next(src_iter)
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['int'], 100000)
            self.assertAlmostEqual(row['float'], 5.12312, places=5)
            self.assertEqual(row['date'], '3/4/2015')
            self.assertEqual(row['unicode'], u'Middlӭ Ёarth')
            # Past end of rows
            with self.assertRaises(StopIteration):
                _ = next(src_iter)

    def test_mixed_row_len(self):
        src_file = os.path.join(self.test_files_path, 'mixed_row_len.xlsx')
        self.maxDiff = None
        with XLSXReader(self.task, src_file) as src:
            self.assertEqual(src.column_names, ['str', 'col2', 'col3', 'un_named_col_3', 'un_named_col_4'])
            expected_repr = f"XLSXReader(mixed_row_len.xlsx)"
            self.assertEqual(repr(src), expected_repr)
            src_iter = iter(src)
            # Row 1 after header = Row 2 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'Bob')
            self.assertEqual(row['col2'], None)
            self.assertEqual(row['col3'], None)
            with self.assertRaises(KeyError):
                _ = row[src.restkey]
            # Row 2 after header = Row 3 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'Jane')
            self.assertEqual(row['col2'], 100)
            self.assertEqual(row['col3'], None)
            with self.assertRaises(KeyError):
                _ = row[src.restkey]
            # Row 3 after header = Row 4 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['col2'], 100000)
            self.assertEqual(row['col3'], 'abc')
            with self.assertRaises(KeyError):
                _ = row[src.restkey]
            # Row 4 after header = Row 5 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'big row')
            self.assertAlmostEqual(row['col2'], float(1234567891234567890), delta=10000)
            self.assertEqual(row['col3'], 'abcdefhijlmnopqrstuvwxyzABCDEFHIJLMNOPQRSTUVWXYZ')
            self.assertEqual(row['un_named_col_3'], 'extraColVal')
            # Row 5 after header = Row 6 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'really big row')
            self.assertEqual(row['col2'], 2)
            self.assertEqual(row['col3'], 3)
            self.assertEqual(row['un_named_col_4'], 'extraColVal2')
            # Past end of rows
            with self.assertRaises(StopIteration):
                row = next(src_iter)
            _ = row

    def test_multiple_sheets(self):
        src_file = os.path.join(TestXLSReader.get_test_files_path(), 'multiple_sheets.xlsx')
        logical_name = os.path.basename(src_file)
        # print(srcFile)
        quoted_src_file = repr(src_file)
        # print(quotedSrcFile)
        self.maxDiff = None
        # Test passing string filename and encoding
        with XLSXReader(self.task, src_file, encoding='utf-8') as src:
            self.assertEqual(src.column_names, ['str', 'int', 'float', 'date', 'unicode'])
            src_iter = iter(src)
            row = next(src_iter)
            self.assertEqual(src.line_num, 2, 'line_num error')
            self.assertEqual(row['str'], 'Bob')
            self.assertEqual(row['int'], 1)
            self.assertEqual(row['float'], 1.5)
            self.assertEqual(row['date'], '1/1/2000')
            self.assertEqual(row['unicode'], u'©Me')
            row = next(src_iter)
            self.assertEqual(src.line_num, 3, 'line_num error')
            self.assertEqual(row['str'], 'Jane')
            self.assertEqual(row['int'], 100)
            self.assertAlmostEqual(row['float'], 2.123, places=5)
            self.assertEqual(row['date'], '2/3/2010')
            self.assertEqual(row['unicode'], u'∞ diversity')
            row = next(src_iter)
            self.assertEqual(src.line_num, 4, 'line_num error')
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['int'], 100000)
            self.assertAlmostEqual(row['float'], 5.12312, places=5)
            self.assertEqual(row['date'], '3/4/2015')
            self.assertEqual(row['unicode'], u'Middlӭ Ёarth')
            try:
                _ = next(src_iter)
                self.fail('StopIteration expected at end of file')
            except StopIteration:
                pass

            # Test read from the next tab
            src.set_active_worksheet_by_name('mixed')
            src_iter = iter(src)
            self.assertEqual(src.column_names, ['str', 'col2', 'col3', 'un_named_col_3', 'un_named_col_4'])
            # Row 1 after header = Row 2 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'Bob')
            self.assertEqual(row['col2'], None)
            self.assertEqual(row['col3'], None)
            with self.assertRaises(KeyError):
                _ = row[src.restkey]
            # Row 2 after header = Row 3 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'Jane')
            self.assertEqual(row['col2'], 100)
            self.assertEqual(row['col3'], None)
            with self.assertRaises(KeyError):
                _ = row[src.restkey]
            # Row 3 after header = Row 4 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['col2'], 100000)
            self.assertEqual(row['col3'], 'abc')
            with self.assertRaises(KeyError):
                _ = row[src.restkey]
            # Row 4 after header = Row 5 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'big row')
            self.assertAlmostEqual(row['col2'], float(1234567891234567890), delta=10000)
            self.assertEqual(row['col3'], 'abcdefhijlmnopqrstuvwxyzABCDEFHIJLMNOPQRSTUVWXYZ')
            self.assertEqual(row['un_named_col_3'], 'extraColVal')
            # Row 5 after header = Row 6 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'really big row')
            self.assertEqual(row['col2'], 2)
            self.assertEqual(row['col3'], 3)
            self.assertEqual(row['un_named_col_4'], 'extraColVal2')
            # Past end of rows
            with self.assertRaises(StopIteration):
                row = next(src_iter)
            _ = row

    def test_open_twice(self):
        src_file = os.path.join(self.test_files_path, 'simple.xlsx')
        with XLSXReader(self.task, src_file) as src:
            self.assertEqual(['str', 'int', 'float', 'date', 'unicode'], src.column_names)

        with XLSXReader(self.task, src_file) as src:
            self.assertEqual(['str', 'int', 'float', 'date', 'unicode'], src.column_names)

    def test_close(self):
        src_file = os.path.join(self.test_files_path, 'simple.xlsx')
        with TemporaryDirectory() as tmp:
            file_to_open = os.path.join(tmp, 'simple.xlsx')
            shutil.copy(src_file, file_to_open)
            with XLSXReader(self.task, file_to_open) as src:
                self.assertEqual(['str', 'int', 'float', 'date', 'unicode'], src.column_names)
            os.remove(file_to_open)


if __name__ == "__main__":
    unittest.main()
