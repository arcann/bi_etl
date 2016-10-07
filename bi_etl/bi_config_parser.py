"""
Created on Apr 8, 2014

@author: woodd
"""
import inspect
import logging
import os.path
import re
import sys
from configparser import NoSectionError
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

    def __init__(self, *args, **kwargs):
        super().__init__(allow_no_value=True,
                         interpolation=ExtendedInterpolation(),
                         *args,
                         **kwargs
                         )
        self.log = logging.getLogger(__name__)
        self.config_file_read = None
        self.rootLogger = logging.getLogger()
        self.configured_loggers = dict()
        self.datefmt = self.get_or_None('logging', 'date_format')
        self.trace_logging_setup = self.getboolean_or_default('logging',
                                                              'trace_setup',
                                                              False
                                                              )

    def read_config_ini(self):
        # pylint: disable=invalid-name
        r"""
        Read the config file from any of the following locations
        * C:\bi_etl_config\config.ini
        * E:\bi_etl_config\config.ini
        * ~/bi_etl_config\config.ini
        * ~/.BI_utils.ini
        * ~/BI_utils.ini

        Where ~ is the users home directory.

        """
        userDir = os.path.expanduser('~')
        expected_config_files = [
            # These first two paths are for
            # running as a windows service
            os.path.join(r"C:\bi_etl_config\config.ini"),
            os.path.join(r"D:\bi_etl_config\config.ini"),
            os.path.join(r"E:\bi_etl_config\config.ini"),
            # If those don't work then look in the user directory
            os.path.join(userDir, 'bi_etl_config', 'config.ini'),
            # Legacy names
            os.path.join(userDir, '.BI_utils.ini'),
            os.path.join(userDir, 'BI_utils.ini')
        ]
        read_ok = self.read(expected_config_files)
        if read_ok is None or len(read_ok) == 0:
            raise FileNotFoundError('None of the expected config files where found: {}'.format(expected_config_files))

        self.config_file_read = read_ok
        self.log.info('Read config file {}'.format(self.config_file_read))
        return read_ok

    @staticmethod
    def get_package_root(obj=None):
        """
        Get the root path of a package given an object (default is this module).

        Parameters
        ----------
        obj: Object to inspect for package
            Defaults to this module

        Returns
        -------
        root_path: str
            The root path of the package
        """
        if obj is None:
            obj = BIConfigParser
        module_path = inspect.getfile(obj)
        (parent_path, _) = os.path.split(module_path)
        (root_path, _) = os.path.split(parent_path)
        return root_path

    def read_relative_config(self, config_file_name, start_path=os.getcwd()):
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
        # Recurse up directories looking for our config file
        path = start_path
        while not os.path.isfile(os.path.join(path, config_file_name)):
            old_path = path
            path = os.path.split(path)[0]
            if path == old_path:
                raise FileNotFoundError('File not found: ' + config_file_name)
        filepath = os.path.join(path, config_file_name)
        self.log.info('Read config file (relative) {}'.format(filepath))
        return self.read(filepath)

    def get_method_or_default(self, method, section, option, default):
        """
        Get a configuration option using the supplied method (e.g. getint) or returns a default if that doesn't exist.

        Parameters
        ----------
        method: method
            A method of his config class to use (e.g. getint).
        section: str
            The section to use.
        option: str
            The option value to get.
        default: any
            The default to return if the option or section is not found.
        """
        option_value = default
        if self.has_section(section) and option:
            if self.has_option(section, option):
                option_value = method(section, option)
        return option_value

    def get_or_default(self, section, option, default):
        """
        Get a configuration option or returns a default if that doesn't exist.

        Parameters
        ----------
        section: str
            The section to use.
        option: str
            The option value to get.
        default: any
            The default to return if the option or section is not found.
        """
        return self.get_method_or_default(method=self.get,
                                          section=section,
                                          option=option,
                                          default=default
                                          )

    def getboolean_or_default(self, section, option, default):
        """
        Get a configuration option as a boolean or returns a default if that doesn't exist.

        Parameters
        ----------
        section: str
            The section to use.
        option: str
            The option value to get.
        default: boolean
            The default to return if the option or section is not found.
        """
        return self.get_method_or_default(method=self.getboolean,
                                          section=section,
                                          option=option,
                                          default=default
                                          )

    def getint_or_default(self, section, option, default):
        """
        Get a configuration option as an int or returns a default if that doesn't exist.

        Parameters
        ----------
        section: str
            The section to use.
        option: str
            The option value to get.
        default: int
            The default to return if the option or section is not found.
        """
        return self.get_method_or_default(self.getint,
                                          section=section,
                                          option=option,
                                          default=default
                                          )

    def getfloat_or_default(self, section, option, default):
        """
        Get a configuration option as a float or returns a default if that doesn't exist.

        Parameters
        ----------
        section: str
            The section to use.
        option: str
            The option value to get.
        default: float
            The default to return if the option or section is not found.
        """
        return self.get_method_or_default(self.getfloat,
                                          section=section,
                                          option=option,
                                          default=default
                                          )

    def getByteSize_or_default(self, section: str, option: str, default: str) -> int:
        """
        Get a configuration option as a byte size or returns a default if that doesn't exist.
        Both the option value and default will be parsed using :func:`~bi_etl.conversions.str2bytes_size`

        Parameters
        ----------
        section: str
            The section to use.
        option: str
            The option value to get.
        default: str
            The default to return if the option or section is not found.
        """
        str_size = self.get_method_or_default(method=self.get,
                                              section=section,
                                              option=option,
                                              default=default
                                              )
        return str2bytes_size(str_size)

    def get_or_None(self, section, option):
        """
        Get a configuration option as or returns None if that doesn't exist.

        Parameters
        ----------
        section: str
            The section to use.
        option: str
            The option value to get.
        """
        return self.get_or_default(section, option, None)

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
        userid = self.get_or_default(user_section, 'userid', default=user_section)
        if self.has_section(user_section) and 'password' in self[user_section]:
            password = self.get(user_section, 'password', raw=True)
        else:
            try:
                # noinspection PyUnresolvedReferences
                import keyring
                key_ring_system = database_name
                if self.has_section(database_name):
                    key_ring_system = self.get(database_name, 'key_ring_system', fallback=database_name)
                key_ring_userid = self.get(user_section, 'key_ring_userid', fallback=userid)

                password = keyring.get_password(key_ring_system, key_ring_userid)
            except ImportError:
                msg = "Config password not provided, and keyring not installed. " \
                      "When trying to get password for {}.{}".format(database_name, userid)
                raise KeyError(msg)

            if password is None:
                msg = "Both config.ini and Keyring did not have password for {}.{}".format(database_name, userid)
                raise KeyError(msg)

        return userid, password

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
                    os.mkdir(folder)
                log_file_name = os.path.join(folder, log_file_name)
        return log_file_name

    def set_log_file_name(self, log_file_name):
        """
        Sets the log file name in the config (memory copy only)
        Specifically that is ``log_file_name`` in the ``logging`` section
        """
        self.set('logging', 'log_file_name', log_file_name)

    def set_dated_log_file_name(self, prefix, suffix, date_time_format='_%Y_%m_%d_at_%H_%M_%S'):
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

    def setup_log_file(self):
        filename = self.get_log_file_name()
        if filename is not None:
            # Setup file logging
            max_bytes = self.getByteSize_or_default('logging', 'log_file_max_size', '10M')

            backup_count = int(self.get_or_default('logging', 'log_files_to_keep', 0))
            file_handler = RotatingFileHandler(filename=filename,
                                               maxBytes=max_bytes,
                                               backupCount=backup_count,
                                               encoding='utf8',
                                               )

            default_entry_format = '%(asctime)s - %(levelname)-8s - %(name)s: %(message)s'
            log_file_entry_format = self.get_or_default('logging',
                                                        'log_file_entry_format',
                                                        default_entry_format)
            log_file_entry_formater = logging.Formatter(log_file_entry_format, self.datefmt)
            file_handler.setFormatter(log_file_entry_formater)
            file_handler_level = self.get_or_default('logging', 'file_log_level', 'DEBUG').upper()
            file_handler.setLevel(file_handler_level)
            self.rootLogger.addHandler(file_handler)

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
                desired_level_name = self.get_or_None('loggers', logger_class)
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
        self.rootLogger.setLevel(self.get_or_default('logging', 'root_level', logging.INFO))

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
        console_log.setLevel(self.get_or_default('logging', 'console_log_level', 'DEBUG').upper())
        console_log.addFilter(non_error)
        self.rootLogger.addHandler(console_log)

        console_entry_format = self.get_or_None('logging', 'console_entry_format')
        if console_entry_format:
            console_entry_formater = logging.Formatter(console_entry_format, self.datefmt)
            console_log.setFormatter(console_entry_formater)
            console_error_log.setFormatter(console_entry_formater)

        if use_log_file_setting:
            self.setup_log_file()

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


def build_example():
    """
    Builds an example config file from the currently active one in the users folder
    """
    from bi_etl.utility.ask import yes_no

    my_config = BIConfigParser()
    ini_path = my_config.read_config_ini()
    my_config.setup_logging()
    log = logging.getLogger(__name__)
    log.info('Logging level is {}'.format(logging.getLevelName(log.getEffectiveLevel())))

    root_path = BIConfigParser.get_package_root()

    example_ini_file = os.path.join(root_path, 'example_config_files', 'config.ini')
    log.info("Starting")

    response = yes_no("Proceed with rebuilding example in {}?".format(example_ini_file))
    if response:
        log.info("Building example_ini_file = {}".format(example_ini_file))
        with open(ini_path[0], 'r') as source:
            with open(example_ini_file, 'w') as target:
                for line in source:
                    password_match = re.match(r'(.*password.*)=', line, re.IGNORECASE)
                    if password_match:
                        password_line = "{password_attr}=*******************\n".format(
                            password_attr=password_match.group(1))
                        target.write(password_line)
                    else:
                        target.write(line)

        log.info("Done")
    else:
        log.info("Cancelled")


# =============================================
if __name__ == "__main__":
    build_example()
