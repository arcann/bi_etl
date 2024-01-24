import logging
from typing import Optional


class NotifierBase(object):
    def __init__(self, *, name: Optional[str] = None):
        class_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        self.log = logging.getLogger(class_name)
        self.name = name or class_name

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        pass

    def post_status(self, status_message):
        """
        Send a temporary status messages that gets overwritten with the next status message that is sent.

        Parameters
        ----------
        status_message

        Returns
        -------

        """
        raise NotImplementedError("This Notifier does not implement post_status")


class NotifierException(Exception):
    pass
