from configparser import ConfigParser

from bi_etl.notifiers.notifier import Notifier


class LogNotifier(Notifier):
    def __init__(self, config: ConfigParser, config_section: str):
        super().__init__(config=config,
                         config_section=config_section)

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        if subject is not None:
            self.log.info(subject)
        if message is not None:
            self.log.info(message)
