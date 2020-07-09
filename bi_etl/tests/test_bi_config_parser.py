"""
Created on Apr 8, 2014

@author: Derek Wood
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

        self.generated_ini_file = '.BI_utils.ini'
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
        os.mkdir(os.path.join(self.tempDir, 'my_folder'))
        self.generated_ini_file_path = os.path.join(self.tempDir, self.generated_ini_file)
        with open(self.generated_ini_file_path, 'w') as temp_file_handle:
            cp.write(temp_file_handle)

        self.generated_child_ini_file = 'config.ini'
        os.mkdir(os.path.join(self.tempDir, 'child'))
        self.generated_child_ini_file_path = os.path.join(self.tempDir, 'child', self.generated_child_ini_file)
        generated_parent_ini_file = 'test_shared_config.ini'
        generated_parent_dir = os.path.join(self.tempDir, 'parent')
        os.mkdir(generated_parent_dir)
        self.generated_parent_ini_file_path = os.path.join(generated_parent_dir, generated_parent_ini_file)
        child_cp = configparser.ConfigParser()
        child_cp.add_section('Config')
        child_cp['Config']['parent'] = self.generated_parent_ini_file_path
        child_cp.add_section('Settings')
        child_cp['Settings']['child'] = '1'
        child_cp['Settings']['child_override'] = '2'
        with open(self.generated_child_ini_file_path, 'w') as temp_file_handle:
            child_cp.write(temp_file_handle)
        parent_cp = configparser.ConfigParser()
        parent_cp.add_section('Settings')
        parent_cp['Settings']['parent'] = 'abc'
        parent_cp['Settings']['child_override'] = '1'
        with open(self.generated_parent_ini_file_path, 'w') as temp_file_handle:
            parent_cp.write(temp_file_handle)

    def tearDown(self):
        self.log_folder.cleanup()
        os.remove(self.generated_ini_file_path)
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

    def test_read_config_ini_NF2(self):
        config = bi_etl.bi_config_parser.BIConfigParser()
        self.assertRaises(FileNotFoundError,
                          config.read_config_ini,
                          'does_not_exist.ini',
                          )

    def test_read_config_ini_OK(self):
        # This version will try and find the example config file.
        # Will fail if it doesn't exist.
        config = bi_etl.bi_config_parser.BIConfigParser()

        try:
            # Make sure the current working dir is the bi_etl home dir
            # (where example_config.ini can be found)
            dir_path = os.path.dirname(os.path.realpath(__file__))
            with mock.patch('os.getcwd', autospec=True) as getcwd:
                getcwd.return_value = dir_path
                config.read_config_ini(file_name='example_config.ini')
        except FileNotFoundError as e:
            self.fail(e)

    def test_read_child_config_ini_ok(self):
        # This version will try and find the generated config file
        # using the current working directory
        # Will fail if it doesn't exist.
        config = bi_etl.bi_config_parser.BIConfigParser()

        try:
            dir_path = os.path.dirname(self.generated_child_ini_file_path)
            with mock.patch('os.getcwd', autospec=True) as getcwd:
                getcwd.return_value = dir_path
                config.read_config_ini(file_name='config.ini')
            self.assertEqual(config['Settings']['child'], '1')
            self.assertEqual(config['Settings']['child_override'], '2')
            self.assertEqual(config['Settings']['parent'], 'abc')
        except FileNotFoundError as e:
            self.fail(e)

    def test_read_child_config_ini_env_ok(self):
        # This version will try and find the generated config file
        # using the environment variable
        # Will fail if it doesn't exist.
        config = bi_etl.bi_config_parser.BIConfigParser()

        try:
            os.environ[config.CONFIG_ENV] = self.generated_child_ini_file_path
            config.read_config_ini()
            del os.environ[config.CONFIG_ENV]
            self.assertEqual(config['Settings']['child'], '1')
            self.assertEqual(config['Settings']['child_override'], '2')
            self.assertEqual(config['Settings']['parent'], 'abc')
        except FileNotFoundError as e:
            self.fail(e)

    def test_read_relative_config_OK(self):
        config = bi_etl.bi_config_parser.BIConfigParser()

        try:
            with mock.patch('os.getcwd', autospec=True) as getcwd:
                getcwd.return_value = self.tempDir
                config.read_relative_config(self.generated_ini_file, start_path=self.tempDir)
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

    def test_inherit_1(self):
        config = bi_etl.bi_config_parser.BIConfigParser()
        config.add_section('level1')
        config.add_section('level1.level2')
        config.set('level1', 'A', '1')
        config.set('level1', 'B', '2')
        config.set('level1.level2', 'A', '10')

        self.assertEqual(config['level1.level2']['A'], '10')
        self.assertEqual(config.get('level1.level2', 'A'), '10')

        self.assertEqual(config['level1.level2']['B'], '2')
        self.assertEqual(config.get('level1.level2', 'B'), '2')

        self.assertEqual(config.get('level1.level2', 'C', fallback='3'), '3')

        self.assertEqual(config.get('level1', 'C', fallback='4'), '4')

        try:
            config.get('level1', 'C')
            self.fail("Did not raise NoOptionError")
        except configparser.NoOptionError:
            pass

        try:
            config.get('level1.level2', 'C')
            self.fail("Did not raise NoOptionError")
        except configparser.NoOptionError:
            pass


if __name__ == "__main__":
    unittest.main()
