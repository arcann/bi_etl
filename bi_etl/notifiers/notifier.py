import logging
from configparser import ConfigParser


class Notifier(object):
    def __init__(self, config: ConfigParser, config_section: str):
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.config = config
        assert(isinstance(config, ConfigParser))
        self.config_section = config_section

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        pass


class NotifierException(Exception):
    pass
