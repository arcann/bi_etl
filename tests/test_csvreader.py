# -*- coding: utf-8 -*-
"""
Created on Nov 30, 2015

@author: Derek Wood
"""
import inspect
import os
import unittest

from bi_etl.components.csvreader import CSVReader
from bi_etl.scheduler.task import ETLTask
from tests.config_for_tests import build_config


class Test(unittest.TestCase):
    @staticmethod
    def get_package_path():
        module_path = inspect.getfile(Test)
        (tests_path, _) = os.path.split(module_path)
        return tests_path

    @staticmethod
    def get_test_files_path():
        return os.path.join(Test.get_package_path(), 'test_files')

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

    @staticmethod
    def getUTF8filepath():
        return os.path.join(Test.get_test_files_path(), 'utf8_with_header.csv')

    # noinspection PyTypeChecker
    def testUTF8_CSV_with_header_where(self):
        src_file = self.getUTF8filepath()
        # print(srcFile)
        logical_name = os.path.basename(src_file)
        quoted_src_file = repr(src_file)
        # print(quotedSrcFile)
        self.maxDiff = None
        # Test passing opened file
        with open(src_file, mode='rt', encoding='utf-8') as srcFileData:
            with CSVReader(self.task, srcFileData) as src:
                self.assertEqual(src.column_names, ['str', 'int', 'float', 'date', 'unicode'])
                expected_repr = (
                    f"CSVReader(task={self.task},logical_name={logical_name},"
                    f"filedata=<_io.TextIOWrapper name={quoted_src_file} mode='rt' encoding='utf-8'>,"
                    f"primary_key=[],column_names=['str', 'int', 'float', 'date', 'unicode'])"
                )
                self.assertEqual(repr(src), expected_repr)
                src_iter = src.where(criteria_dict={'str': 'Bob'})
                row = next(src_iter)
                self.assertEqual(src.rows_read, 1, 'rows_read error')
                self.assertEqual(row['str'], 'Bob')
                self.assertEqual(row['int'], '1')
                self.assertEqual(row['float'], '1.5')
                self.assertEqual(row['date'], '1/1/2000')
                self.assertEqual(row['unicode'], u'©Me')
                try:
                    _ = next(src_iter)
                    self.fail('StopIteration expected at end of file')
                except StopIteration:
                    pass

    def testUTF8_pipe_with_header(self):
        src_file = os.path.join(self.test_files_path, 'utf8_with_header.pipe')
        logical_name = os.path.basename(src_file)
        # print(srcFile)
        quoted_src_file = repr(src_file)
        # print(quotedSrcFile)
        self.maxDiff = None
        # Test passing string filename and encoding
        with CSVReader(self.task, src_file, encoding='utf-8') as src:
            src.delimiter = '|'
            self.assertEqual(src.column_names, ['str', 'int', 'float', 'date', 'unicode'])
            expected_repr = (
                f"CSVReader(task={self.task},logical_name={logical_name},"
                f"filedata=<_io.TextIOWrapper name={quoted_src_file} mode='rt' encoding='utf-8'>,"
                f"primary_key=[],column_names=['str', 'int', 'float', 'date', 'unicode'])"
            )
            self.assertEqual(repr(src), expected_repr)
            src_iter = iter(src)
            row = next(src_iter)
            self.assertEqual(src.line_num, 2, 'line_num error')
            self.assertEqual(row['str'], 'Bob')
            self.assertEqual(row['int'], '1')
            self.assertEqual(row['float'], '1.5')
            self.assertEqual(row['date'], '1/1/2000')
            self.assertEqual(row['unicode'], u'©Me')
            row = next(src_iter)
            self.assertEqual(src.line_num, 3, 'line_num error')
            self.assertEqual(row['str'], 'Jane')
            self.assertEqual(row['int'], '100')
            self.assertEqual(row['float'], '02.123')
            self.assertEqual(row['date'], '2/3/2010')
            self.assertEqual(row['unicode'], u'∞ diversity')
            row = next(src_iter)
            self.assertEqual(src.line_num, 4, 'line_num error')
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['int'], '100000')
            self.assertEqual(row['float'], '5.12312')
            self.assertEqual(row['date'], '3/4/2015')
            self.assertEqual(row['unicode'], u'Middlӭ Ёarth')
            try:
                _ = next(src_iter)
                self.fail('StopIteration expected at end of file')
            except StopIteration:
                pass

    def testUTF8_large_file(self):
        src_file = os.path.join(self.test_files_path, 'utf8_large_field.pipe')
        # Test passing string filename and encoding
        with CSVReader(self.task, src_file, encoding='utf-8') as src:
            src.large_field_support = True
            src.delimiter = '|'
            self.assertEqual(src.column_names, ['str', 'unicode', 'after'])
            src_iter = iter(src)
            row = next(src_iter)
            long_value = row['unicode']
            self.assertEqual(len(long_value), 140000)
            # Ending char is !
            assert (long_value.startswith(u'Middlӭ Ёarth'))
            self.assertEqual(long_value[-1], '!')
            self.assertEqual(row['after'], 'after_val')

    def testUTF8_tab_no_header(self):
        src_file = os.path.join(self.test_files_path, 'utf8_no_header.tab')
        logical_name = os.path.basename(src_file)
        # print(srcFile)
        quoted_src_file = repr(src_file)
        # print(quotedSrcFile)
        self.maxDiff = None
        # Test passing string filename and encoding
        with CSVReader(self.task, src_file, encoding='utf-8') as src:
            src.delimiter = '\t'
            src.column_names = ['str', 'int', 'float', 'date', 'unicode']
            self.assertEqual(src.column_names, ['str', 'int', 'float', 'date', 'unicode'])
            expected_repr = (
                f"CSVReader(task={self.task},logical_name={logical_name},"
                f"filedata=<_io.TextIOWrapper name={quoted_src_file} mode='rt' encoding='utf-8'>,"
                f"primary_key=[],column_names=['str', 'int', 'float', 'date', 'unicode'])"
            )
            self.assertEqual(repr(src), expected_repr)
            src_iter = iter(src)
            row = next(src_iter)
            self.assertEqual(row['str'], 'Bob')
            self.assertEqual(row['int'], '1')
            self.assertEqual(row['float'], '1.5')
            self.assertEqual(row['date'], '1/1/2000')
            self.assertEqual(row['unicode'], u'©Me')
            row = next(src_iter)
            self.assertEqual(row['str'], 'Jane')
            self.assertEqual(row['int'], '100')
            self.assertEqual(row['float'], '02.123')
            self.assertEqual(row['date'], '2/3/2010')
            self.assertEqual(row['unicode'], u'∞ diversity')
            row = next(src_iter)
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['int'], '100000')
            self.assertEqual(row['float'], '5.12312')
            self.assertEqual(row['date'], '3/4/2015')
            self.assertEqual(row['unicode'], u'Middlӭ Ёarth')
            # Past end of rows
            with self.assertRaises(StopIteration):
                _ = next(src_iter)

    def testUTF8_tab_no_header_start_3(self):
        src_file = os.path.join(self.test_files_path, 'utf8_no_header.tab')
        logical_name = os.path.basename(src_file)
        # print(srcFile)
        quoted_src_file = repr(src_file)
        # print(quotedSrcFile)
        self.maxDiff = None
        # Test passing string filename and encoding
        with CSVReader(self.task, src_file, encoding='utf-8') as src:
            src.start_row = 3
            src.delimiter = '\t'
            src.restkey = 'extraStuff'
            src.column_names = ['str', 'int', 'float', 'date', 'unicode']
            self.assertEqual(src.column_names, ['str', 'int', 'float', 'date', 'unicode'])
            expected_repr = f"CSVReader(task={self.task},logical_name={logical_name}," \
                            f"filedata=<_io.TextIOWrapper name={quoted_src_file} mode='rt' encoding='utf-8'>," \
                            f"primary_key=[],column_names=['str', 'int', 'float', 'date', 'unicode'])"
            self.assertEqual(repr(src), expected_repr)
            src_iter = iter(src)
            row = next(src_iter)
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['int'], '100000')
            self.assertEqual(row['float'], '5.12312')
            self.assertEqual(row['date'], '3/4/2015')
            self.assertEqual(row['unicode'], u'Middlӭ Ёarth')
            # Past end of rows
            with self.assertRaises(StopIteration):
                _ = next(src_iter)

    def testUTF8_pipe_utf8_with_header_mixed_row_len(self):
        src_file = os.path.join(self.test_files_path, 'utf8_with_header_mixed_row_len.pipe')
        logical_name = os.path.basename(src_file)
        # print(srcFile)
        quoted_src_file = repr(src_file)
        # print(quotedSrcFile)
        self.maxDiff = None
        # Test passing string filename and encoding
        with CSVReader(self.task, src_file, encoding='utf-8') as src:
            src.delimiter = '|'
            self.assertEqual(src.column_names, ['str', 'col2', 'col3'])
            expected_repr = f"CSVReader(task={self.task},logical_name={logical_name}," \
                            f"filedata=<_io.TextIOWrapper name={quoted_src_file} mode='rt' encoding='utf-8'>," \
                            f"primary_key=[],column_names=['str', 'col2', 'col3'])"
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
            restval = '<Blank>'
            src.restval = restval
            row = next(src_iter)
            self.assertEqual(row['str'], 'Jane')
            self.assertEqual(row['col2'], '100')
            self.assertEqual(row['col3'], restval)
            with self.assertRaises(KeyError):
                _ = row[src.restkey]
            # Row 3 after header = Row 4 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'Amanda')
            self.assertEqual(row['col2'], '100000')
            self.assertEqual(row['col3'], 'abc')
            with self.assertRaises(KeyError):
                _ = row[src.restkey]
            # Row 4 after header = Row 5 in file
            row = next(src_iter)
            self.assertEqual(row['str'], 'big row')
            self.assertEqual(row['col2'], '1234567891234567890')
            self.assertEqual(row['col3'], 'abcdefhijlmnopqrstuvwxyzABCDEFHIJLMNOPQRSTUVWXYZ')
            extra_col_list = ['extraColVal']
            self.assertEqual(row[src.restkey], extra_col_list)
            # Row 5 after header = Row 6 in file
            src.restkey = 'extraCol'
            row = next(src_iter)
            self.assertEqual(row['str'], 'really big row')
            self.assertEqual(row['col2'], '2')
            self.assertEqual(row['col3'], '3')
            extra_col_list = ['extraColVal1', 'extraColVal2']
            self.assertEqual(row[src.restkey], extra_col_list)
            # Past end of rows
            with self.assertRaises(StopIteration):
                row = next(src_iter)
            _ = row


if __name__ == "__main__":
    unittest.main()
