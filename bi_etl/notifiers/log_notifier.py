from bi_etl.notifiers.notifier_base import NotifierBase


class LogNotifier(NotifierBase):
    def __init__(self):
        super().__init__()

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        if subject is not None:
            self.log.info(subject)
        if message is not None:
            self.log.info(message)
