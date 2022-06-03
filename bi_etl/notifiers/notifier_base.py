import logging


class NotifierBase(object):
    def __init__(self):
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        pass


class NotifierException(Exception):
    pass
