from configparser import ConfigParser

from bi_etl.notifiers.notifier import Notifier


class LogNotifier(Notifier):
    def __init__(self, config: ConfigParser, config_section: str):
        super().__init__(config=config,
                         config_section=config_section)

    def send(self, message, subject=None, throw_exception=False):
        if subject:
            self.log.info(subject)
        self.log.info(message)
