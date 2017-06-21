"""
Created on Apr 8, 2014

@author: woodd
"""
import configparser
from datetime import datetime
import os.path
import shutil
import tempfile
import unittest
from unittest import mock

import bi_etl.bi_config_parser

# pylint: disable=missing-docstring, protected-access, redefined-builtin

# Python 2 & 3 compatibility. If Python 3 FileNotFoundError exists, we'll use it
# if not we'll make it.
try:
    FileNotFoundError
except NameError:
    class FileNotFoundError(IOError):  # @ReservedAssignment
        pass


class Test(unittest.TestCase):
    def setUp(self):
        self.longMessage = True

        cp = configparser.ConfigParser()
        section = 'section1'
        cp.add_section(section)
        cp.set(section, 'option', 'value')
        logging_section = 'logging'
        cp.add_section(logging_section)
        self.log_folder = tempfile.TemporaryDirectory(prefix='log')
        cp.set(logging_section, 'log_folder', self.log_folder.name)

        cp.set(logging_section, 'log_file_name', 'my_log_file')
        cp.set(logging_section, 'log_folder', 'my_folder')
        cp.set(logging_section, 'file_handler', 'file_handler')
        self.test_logger_name = 'test_logger_name'
        cp.add_section('loggers')
        cp.set('loggers', self.test_logger_name, 'DEBUG')

        self.config_parser = cp

        self.tempDir = tempfile.mkdtemp()
        self.origDir = os.getcwd()
        os.chdir(self.tempDir)
        os.mkdir(os.path.join(self.tempDir, 'my_folder'))
        self.tempFile = os.path.join(self.tempDir, '.BI_utils.ini')
        with open(self.tempFile, 'w') as temp_file_handle:
            cp.write(temp_file_handle)

    def tearDown(self):
        self.log_folder.cleanup()
        os.chdir(self.origDir)
        os.remove(self.tempFile)
        try:
            shutil.rmtree(self.tempDir)
        except PermissionError:
            pass

    def test_read_config_ini_NF(self):
        config = bi_etl.bi_config_parser.BIConfigParser()

        with mock.patch('bi_etl.bi_config_parser.BIConfigParser.read') as read:
            # Mock read function to return empty list (as if not found)
            read.return_value = []
            self.assertRaises(FileNotFoundError,
                              config.read_config_ini
                              )

    def test_read_config_ini_OK(self):
        # This version will try and find the example config file.
        # Will fail if it doesn't exist.
        config = bi_etl.bi_config_parser.BIConfigParser()

        try:
            # Make sure the current working dir is the bi_etl home dir
            # (where example_config.ini can be found)
            dir_path = os.path.dirname(os.path.realpath(__file__))
            # Parent dir
            dir_path = os.path.dirname(dir_path)
            # Parent dir again
            dir_path = os.path.dirname(dir_path)
            with mock.patch('os.getcwd', autospec=True) as getcwd:
                getcwd.return_value = dir_path
                # TODO: use Mock to patch os.getcwd to return dir_path without using chdir
                #os.chdir(dir_path)
                config.read_config_ini('example_config.ini')
        except FileNotFoundError as e:
            self.fail(e)

    def test_read_relative_config_OK(self):
        config = bi_etl.bi_config_parser.BIConfigParser()

        try:
            config.read_relative_config('.BI_utils.ini', start_path=self.tempDir)
        except FileNotFoundError as e:
            self.fail(e)

        self.assertEqual(
            config.get('section1', 'option', fallback='default'),
            self.config_parser.get('section1', 'option'),
            "Config parser didn't return expected value"
        )
        self.assertEqual(
            config.get('section1', 'option2', fallback='default'),
            'default',
            "Config parser didn't return expected default value"
        )
        self.assertEqual(
            config.get('section1', 'option2', fallback=None),
            None,
            "Config parser didn't return expected default value"
        )

    def test_read_relative_config_NF(self):
        config = bi_etl.bi_config_parser.BIConfigParser()

        try:
            _ = config.read_relative_config('I_AM_NOT_HERE'),
            self.fail("Did not raise FileNotFoundError as expected")
        except FileNotFoundError as e:
            self.assertEqual('File not found: I_AM_NOT_HERE', str(e),
                             "FileNotFoundError messsage not as expected '{}'".format(e))

    def test_logfilename(self):
        config = bi_etl.bi_config_parser.BIConfigParser()

        try:
            config.read_relative_config('.BI_utils.ini', start_path=self.tempDir)
        except FileNotFoundError as e:
            self.fail(e)
        logfilename = config.get_log_file_name()
        self.assertIn(self.config_parser.get('logging', 'log_file_name'),
                      logfilename,
                      )
        self.assertIn(self.config_parser.get('logging', 'log_folder'),
                      logfilename,
                      )
        new_log_file_name = 'bob_file.txt'
        config.set_log_file_name(new_log_file_name)
        self.assertIn(new_log_file_name,
                      config.get_log_file_name(),
                      )
        config.set_dated_log_file_name('my_new_file', '.csv')
        logfilename = config.get_log_file_name()
        self.assertIn('my_new_file',
                      config.get_log_file_name(),
                      )
        self.assertIn('.csv',
                      config.get_log_file_name(),
                      )
        self.assertIn(str(datetime.now().year),
                      config.get_log_file_name(),
                      )


if __name__ == "__main__":
    unittest.main()
