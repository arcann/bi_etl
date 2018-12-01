"""
Created on Apr 8, 2014

@author: woodd
"""
import getpass
import inspect
import logging
import os.path
import re
import sys
from configparser import NoSectionError, _UNSET
from datetime import datetime
from logging.handlers import RotatingFileHandler

from CaseInsensitiveDict import CaseInsensitiveDict

from bi_etl.conversions import str2bytes_size

from configparser import ConfigParser, ExtendedInterpolation


class BIConfigParser(ConfigParser):
    """
    The basic configuration object. When defaults is given, it is initialized into the dictionary
    of intrinsic defaults. When dict_type is given, it will be used to create the dictionary
    objects for the list of sections, for the options within a section, and for the default values.
    When allow_no_value is true (default: False), options without values are accepted; the value
    presented for these is None.

    Adds a read_config_ini function to read bi_etl_config\config.ini from C:\, E:\ or Home directory
    Adds a read_relative_config function to search from pwd up to file the config file
    """
    CONFIG_ENV = 'BI_ETL_CONFIG'

    def __init__(self, *args, **kwargs):
        super().__init__(allow_no_value=True,
                         interpolation=ExtendedInterpolation(),
                         *args,
                         **kwargs
                         )
        self.log = logging.getLogger(__name__)
        if len(self.log.root.handlers) == 0:
            logging.basicConfig(level=logging.DEBUG)
        self.config_file_read = None
        self.rootLogger = logging.getLogger()
        self.configured_loggers = dict()
        self.date_format = self.get('logging', 'date_format', fallback=None)
        self.logging_setup = False
        self.trace_logging_setup = self.getboolean('logging',
                                                   'trace_setup',
                                                   fallback=False,
                                                   )

    def merge_config(self, other_config):
        for section in other_config.sections():
            if not self.has_section(section):
                self.add_section(section)
            for option in other_config.options(section):
                if not self.has_direct_option(section, option):
                    self[section][option] = other_config[section][option]

    def merge_parent(self, directories: list, parent_file: str):
        parent_config = ConfigParser(allow_no_value=True,
                                     interpolation=ExtendedInterpolation())
        file_paths = [os.path.normpath(os.path.join(directory, parent_file)) for directory in directories]
        files_read = parent_config.read(file_paths)
        read_dirs = [os.path.dirname(file) for file in files_read]
        if files_read is not None and len(files_read) > 0:
            for file in files_read:
                if file in self.config_file_read:
                    raise RecursionError("File {} is causing a loop in parent config reading".format(file))

            self.config_file_read.extend(files_read)

            self.merge_config(parent_config)

            # Check if we need to read another level of parent files
            if parent_config.has_section('Config'):
                for setting in parent_config['Config']:
                    if setting.startswith('parent'):
                        file_name = parent_config['Config'][setting]
                        alread_read = False
                        for directory in read_dirs:
                            file_path = os.path.normpath(os.path.join(directory, file_name))
                            for read_file in self.config_file_read:
                                if file_path == read_file:
                                    alread_read = True
                        if not alread_read:
                            self.merge_parent(read_dirs, file_name)

    def read_parents(self, directories: list):
        if self.has_section('Config'):
            for setting in self['Config']:
                if setting.startswith('parent'):
                    self.merge_parent(directories, self['Config'][setting])

    def read_config_ini(self, current_path: str=None, file_name: str= 'config.ini'):
        r"""
        If the BI_ETL_CONFIG environment variable is set, read the config file(s) as specified there (; delimited).

        Otherwise, read the config file from any of the following locations
        (merging multiple files together if more than one exists.)        
        * C:\bi_etl_config\config.ini
        * D:\bi_etl_config\config.ini
        * E:\bi_etl_config\config.ini
        * ~/bi_etl_config\config.ini
        * Current Directory

        Where ~ is the users home directory.
        """

        if BIConfigParser.CONFIG_ENV in os.environ:
            config_env = os.environ[BIConfigParser.CONFIG_ENV]
            config_env = os.path.expanduser(config_env)
            expected_config_files = config_env.split(';')
            self.log.info("Using {} specified config file(s) {}".format(
                BIConfigParser.CONFIG_ENV,
                expected_config_files
            ))
        else:
            if current_path is None:
                current_path = os.getcwd()
            user_dir = os.path.expanduser('~')
            expected_config_files = [
                # These static paths are for running as a windows service
                os.path.join("C:\\", "bi_etl_config", file_name),
                os.path.join("D:\\", "bi_etl_config", file_name),
                os.path.join("E:\\", "bi_etl_config", file_name),
                # If those don't work then look in the user directory
                os.path.join(user_dir, 'bi_etl_config', file_name),

                os.path.join(current_path, file_name),
            ]
            # Finally use a file in the current directory or parents (will override other settings)
            relative_configs = list()
            done = False
            while not done:
                if os.path.isfile(os.path.join(current_path, file_name)):
                    relative_configs.append(os.path.join(current_path, file_name))
                old_path = current_path
                current_path = os.path.split(current_path)[0]
                if current_path == old_path:
                    done = True
            expected_config_files.extend(reversed(relative_configs))
        files_read = self.read(expected_config_files)
        if files_read is None or len(files_read) == 0:
            raise FileNotFoundError('None of the expected config files where found: {}'.format(expected_config_files))

        self.config_file_read = files_read

        read_dirs = [os.path.dirname(file) for file in files_read]

        self.read_parents(read_dirs)

        self.log.info('Read config file(s) {}'.format(self.config_file_read))
        return self.config_file_read

    @staticmethod
    def get_package_root(obj: object=None) -> str:
        """
        Get the root path of a package given an object (default is this module).

        Parameters:
            obj: The object to inspect for package
                 Defaults to this module

        Returns:
            The root path of the package
        """
        if obj is None:
            obj = BIConfigParser
        module_path = inspect.getfile(obj)
        (parent_path, _) = os.path.split(module_path)
        (root_path, _) = os.path.split(parent_path)
        return root_path

    def read_relative_config(self, config_file_name: str='config.ini', start_path: str=None):
        """
        Search from start_path (default current directory) up to file the configuration file

        Parameters
        ----------
        config_file_name: str
            The name of the config file to look for and read

        start_path: str
            Optional. The path to start looking in. Defaults to current directory.

        Returns
        -------
        files_read: list
            list of successfully read files.
        """
        if start_path is None:
            start_path = os.getcwd()
        # Recurse up directories looking for our config file
        path = start_path
        while not os.path.isfile(os.path.join(path, config_file_name)):
            old_path = path
            path = os.path.split(path)[0]
            if path == old_path:
                raise FileNotFoundError('File not found: ' + config_file_name)
        file_path = os.path.join(path, config_file_name)
        self.log.info('Read config file (relative) {}'.format(file_path))
        self.config_file_read = self.read(file_path)
        return self.config_file_read

    def has_direct_option(self, section, option):
        return super().has_option(section, option)

    def has_option(self, section, option):
        if super().has_option(section, option):
            return True
        else:
            if '.' in section:
                section_list = section.split('.')[:-1]
                return self.has_option(section='.'.join(section_list), option=option)
            else:
                return False

    def get(self, section, option, *, raw=False, vars=None, fallback=_UNSET):
        """
        Get an option value for a given section.

        If `vars' is provided, it must be a dictionary. The option is looked up
        in `vars' (if provided), `section', and in `DEFAULTSECT' in that order.
        If the key is not found and `fallback' is provided, it is used as
        a fallback value. `None' can be provided as a `fallback' value.

        If interpolation is enabled and the optional argument `raw' is False,
        all interpolations are expanded in the return values.

        Arguments `raw', `vars', and `fallback' are keyword only.

        The section DEFAULT is special.
        """
        try:
            if super().has_option(section, option):
                return super().get(section, option, raw=raw, vars=vars, fallback=fallback)
            else:
                if '.' in section:
                    section_list = section.split('.')[:-1]
                    return self.get(section='.'.join(section_list), option=option, raw=raw, vars=vars, fallback=fallback)
        except NoSectionError:
            pass
        return super().get(section, option, raw=raw, vars=vars, fallback=fallback)

    def get_byte_size(self, section: str, option: str, fallback: str = None) -> int:
        """
        Get a configuration option as a byte size or returns a default if that doesn't exist.
        Both the option value and default will be parsed using :func:`~bi_etl.conversions.str2bytes_size`

        Parameters
        ----------
        section: str
            The section to use.
        option: str
            The option value to get.
        fallback: str
            The default to return if the option or section is not found.
        """
        str_size = self.get(section=section,
                            option=option,
                            fallback=fallback
                            )
        return str2bytes_size(str_size)

    # noinspection PyPackageRequirements
    def get_database_connection_tuple(self, database_name, user_section=None):
        """
        Gets a tuple (userid, password) of connection information for a given database name.

        Parameters
        ----------
        database_name: str
            The name of the database to look for in the configuration.
        user_section: str
            The name of the section to use for the user ID and password.
            Optional. If not provided, the method will look for a default_user_id value in the
            section named using the database_name parameter.
        """

        self.log.debug('Getting connection info for {}'.format(database_name))

        if user_section is None:
            if not self.has_section(database_name):
                msg = "Config file does not have section {}".format(database_name)
                raise KeyError(msg)
            if self.has_option(database_name, 'default_user_id'):
                user_section = self.get(database_name, 'default_user_id')
            else:
                msg = "user_section not provided, and no default_user_id exists for {}".format(database_name)
                raise KeyError(msg)
        user_id = self.get(user_section, 'userid', fallback=user_section)
        if self.has_section(user_section) and 'password' in self[user_section]:
            password = self.get(user_section, 'password', raw=True)
        else:
            try:
                # noinspection PyUnresolvedReferences
                import keyring
                key_ring_system = database_name
                if self.has_section(database_name):
                    key_ring_system = self.get(database_name, 'key_ring_system', fallback=database_name)
                key_ring_userid = self.get(user_section, 'key_ring_userid', fallback=user_id)

                password = keyring.get_password(key_ring_system, key_ring_userid)
            except ImportError:
                msg = "Config password not provided, and keyring not installed. " \
                      "When trying to get password for {} {}".format(database_name, user_id)
                raise KeyError(msg)

            if password is None:
                msg = "Both config.ini and Keyring did not have password for {} {} os_user={}".format(
                    database_name,
                    user_id,
                    getpass.getuser()
                )
                raise KeyError(msg)

        return user_id, password

    def get_log_file_name(self):
        """
        Gets the log file name defined in the config file.
        Uses ``log_file_name`` and ``log_folder`` from the ``logging`` section ::

            [logging]
            log_file_name=my_file_name
            log_folder=/my/log/path
        """
        log_file_name = None
        if self.has_option('logging', 'log_file_name'):
            log_file_name = self.get('logging', 'log_file_name')
            if self.has_option('logging', 'log_folder'):
                folder = self.get('logging', 'log_folder')
                folder = os.path.expanduser(folder)
                if not os.path.exists(folder):
                    os.makedirs(folder)
                log_file_name = os.path.join(folder, log_file_name)
        return log_file_name

    def set_log_file_name(self, log_file_name):
        """
        Sets the log file name in the config (memory copy only)
        Specifically that is ``log_file_name`` in the ``logging`` section
        """
        self.set('logging', 'log_file_name', log_file_name)

    def set_dated_log_file_name(self, prefix='', suffix='', date_time_format='_%Y_%m_%d_at_%H_%M_%S'):
        """
        Sets the log file name in the config (memory copy only) using the current date and time.
        Specifically that is ``log_file_name`` in the ``logging`` section.

        Parameters
        ----------
        prefix: str
            The part of the log file name before the date
        suffix: str
            The part of the log file name after the date
        date_time_format: str
            Optional. The date time format to use. Defaults to '_%Y_%m_%d_at_%H_%M_%S'
        """
        log_file_name = prefix + datetime.now().strftime(date_time_format) + suffix
        self.set_log_file_name(log_file_name)

    def add_log_file_handler(self, filename=None):
        if filename is None:
            filename = self.get_log_file_name()
        file_handler = None
        if filename is not None:
            if self.trace_logging_setup:
                self.log.info('Logging filename = {}'.format(filename))
            # Setup file logging
            max_bytes = self.get_byte_size('logging', 'log_file_max_size', fallback='10M')

            backup_count = int(self.get('logging', 'log_files_to_keep', fallback=0))

            # Make sure the directory exists
            dir_name = os.path.dirname(filename)
            if dir_name != '':
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)

            file_handler = RotatingFileHandler(filename=filename,
                                               maxBytes=max_bytes,
                                               backupCount=backup_count,
                                               encoding='utf8',
                                               )

            default_entry_format = '%(asctime)s - %(levelname)-8s - %(name)s: %(message)s'
            log_file_entry_format = self.get('logging',
                                             'log_file_entry_format',
                                             fallback=default_entry_format)
            log_file_entry_formatter = logging.Formatter(log_file_entry_format, self.date_format)
            file_handler.setFormatter(log_file_entry_formatter)
            file_handler_level = self.get('logging', 'file_log_level', fallback='DEBUG').upper()
            file_handler.setLevel(file_handler_level)
            self.rootLogger.addHandler(file_handler)
            self.log.info('File log level = {}'.format(file_handler_level))
        else:
            if self.trace_logging_setup:
                self.log.info('No log filename defined. File logging skipped.')
        return file_handler

    def remove_log_file_handler(self, filename=None):
        if filename is None:
            filename = self.get_log_file_name()
        log = self.rootLogger
        for handler in list(log.handlers):
            if isinstance(handler, logging.FileHandler):
                if filename in handler.baseFilename:
                    log.removeHandler(handler)

    def replace_log_file_handler(self, filename=None):
        log = self.rootLogger
        for handler in list(log.handlers):
            if isinstance(handler, logging.FileHandler):
                log.removeHandler(handler)
        self.add_log_file_handler(filename=filename)

    def setup_log_levels(self):
        no_loggers_found = False

        try:
            for logger_class in self.options('loggers'):
                if logger_class.lower() == 'root':
                    logger = self.rootLogger
                else:
                    logger = logging.getLogger(logger_class)
                self.configured_loggers[logger_class] = logger
                logger.propagate = True
                desired_level_name = self.get('loggers', logger_class, fallback=None)
                if desired_level_name is None:
                    desired_level_name = 'INFO'
                else:
                    desired_level_name = desired_level_name.upper()
                if self.trace_logging_setup:
                    print('Setting logger {} to {}'.format(logger.name, desired_level_name))
                logger.setLevel(desired_level_name)
        except NoSectionError:
            no_loggers_found = True

        if no_loggers_found:
            self.log.warning('The config file had no [loggers] section')
        else:
            # Will not include root logger
            for logger_class in sorted(logging.Logger.manager.loggerDict):  # @UndefinedVariable
                logger = logging.getLogger(logger_class)
                if self.trace_logging_setup:
                    print('Logger {} handlers {}'.format(logger_class, logger.handlers))
                if logger_class not in self.configured_loggers:
                    if self.trace_logging_setup:
                        print('Checking existing logger {} level {}'.format(logger_class, logging.getLevelName(
                            logger.getEffectiveLevel())))
                    for compare_logger in sorted(self.configured_loggers):
                        if logger_class.startswith(compare_logger):
                            parent_logger = self.configured_loggers[compare_logger]
                            level = parent_logger.getEffectiveLevel()
                            logger.setLevel(level)
                            if self.trace_logging_setup:
                                print('Existing logger {} re-setup with {} settings {}'.format(logger_class,
                                                                                               parent_logger.name,
                                                                                               logging.getLevelName(
                                                                                                   level)))
                            logger.propagate = True

        if self.trace_logging_setup:
            print('Root logging level is {}'.format(logging.getLevelName(self.rootLogger.getEffectiveLevel())))
            print('Root logging handlers are {}'.format(self.rootLogger.handlers))

    def setup_logging(self, console_output=None, use_log_file_setting=True):
        """
        Setup logging configuration.

        Based on the [logging] and [loggers] sections of the configuration file.
        """

        if not self.logging_setup:
            self.logging_setup = True

            # Close out any existing handlers
            for handler in self.rootLogger.handlers:
                handler.flush()
                handler.close()

            # Reset the handlers
            self.rootLogger.handlers.clear()

            # Monkey-patch getLogger's dict to be case-insensitive by lower casing all names
            # We really need this because the config options from [loggers] will be returned
            # in lower case

            logger_dict = CaseInsensitiveDict(logging.Logger.manager.loggerDict)  # @UndefinedVariable
            logging.Logger.manager.loggerDict = logger_dict

            if self.trace_logging_setup:
                print('[logging].trace_setup is True}')
                print('Starting root logger handlers {}'.format(self.rootLogger.handlers))

            # Modify the root logger level to at least INFO for now
            self.rootLogger.setLevel(self.get('logging', 'root_level', fallback=logging.INFO))

            if console_output is None:
                error_output = sys.stderr
                debug_output = sys.stdout
            else:
                error_output = console_output
                debug_output = console_output

            def non_error(record):
                return record.levelno != logging.ERROR

            console_error_log = logging.StreamHandler(error_output)
            console_error_log.setLevel(logging.ERROR)
            self.rootLogger.addHandler(console_error_log)

            console_log = logging.StreamHandler(debug_output)
            console_log.setLevel(self.get('logging', 'console_log_level', fallback='DEBUG').upper())
            # Errors go to console_error_log above
            console_log.addFilter(non_error)
            self.rootLogger.addHandler(console_log)

            console_entry_format = self.get('logging', 'console_entry_format', fallback=None)
            if console_entry_format:
                console_entry_formater = logging.Formatter(console_entry_format, self.date_format)
                console_log.setFormatter(console_entry_formater)
                console_error_log.setFormatter(console_entry_formater)

            self.setup_log_levels()

            # Switch to this modules logger
            log = logging.getLogger(__name__)

            logging.captureWarnings(True)

            log_level_name = logging.getLevelName(log.getEffectiveLevel())
            if self.trace_logging_setup:
                log.info('This modules logging level is {}'.format(log_level_name))
            # Record the config file that is in use.
            # The log statement in read_config_ini will not have been logged to the file
            self.log.info('Config file in use = {}'.format(self.config_file_read))

        if use_log_file_setting:
            self.add_log_file_handler()
        else:
            if self.trace_logging_setup:
                self.log.info('use_log_file_setting = False. setup_log_file not called.')


def build_example(config: BIConfigParser=None, config_file_name: str='config.ini', example_config_dir: str='example_config_files'):
    """
    Builds an example config file from the currently active one in the users folder
    """
    from bi_etl.utility.ask import yes_no

    if config is None:
        config = BIConfigParser()
        config.read_config_ini()
        config.setup_logging()
    log = logging.getLogger(__name__)
    log.info('Logging level is {}'.format(logging.getLevelName(log.getEffectiveLevel())))

    if not os.path.exists(example_config_dir):
        response = yes_no("{} does not exist. Create it?".format(example_config_dir))
        if response:
            os.makedirs(example_config_dir)
        else:
            raise FileNotFoundError("{} does not exist.".format(example_config_dir))

    example_ini_file = os.path.join(example_config_dir, config_file_name)
    log.info("Starting")

    response = yes_no("Proceed with rebuilding example in {}?".format(example_ini_file))
    if response:
        log.info("Building example_ini_file = {}".format(example_ini_file))
        if isinstance(config.config_file_read, str):
            config.config_file_read = [config.config_file_read]
        with open(example_ini_file, 'w') as target:
            for section in config.sections():
                for option in config.options(section):
                    password_match = re.match(r'(.*password.*)=', option, re.IGNORECASE)
                    if password_match:
                        config.set(section, option, '*'*40)
            config.write(target)
        log.info("Done")
    else:
        log.info("Cancelled")


# =============================================
if __name__ == "__main__":
    build_example()
