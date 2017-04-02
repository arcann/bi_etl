import logging
from configparser import ConfigParser


class Notifier(object):
    def __init__(self, config: ConfigParser, destination_definition: object):
        self.log = logging.getLogger(__name__)
        self.config = config
        assert(isinstance(config, ConfigParser))
        self.destination_definition = destination_definition

    def send(self, subject, message):
        pass


class NotifierException(Exception):
    pass
