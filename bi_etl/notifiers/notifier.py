import logging
from configparser import ConfigParser


class Notifier(object):
    def __init__(self, config: ConfigParser, config_section: str):
        self.log = logging.getLogger("{mod}.{cls}".format(mod=self.__class__.__module__, cls=self.__class__.__name__))
        self.config = config
        assert(isinstance(config, ConfigParser))
        self.config_section = config_section

    def send(self, subject, message, throw_exception=False):
        pass


class NotifierException(Exception):
    pass
