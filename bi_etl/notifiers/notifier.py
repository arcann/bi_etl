import logging

from bi_etl.bi_config_parser import BIConfigParser


class Notifier(object):
    def __init__(self, config: BIConfigParser, destination_definition: object):
        self.log = logging.getLogger(__name__)
        self.config = config
        assert(isinstance(config, BIConfigParser))
        self.destinations = destination_definition

    def send(self, subject, message):
        pass
