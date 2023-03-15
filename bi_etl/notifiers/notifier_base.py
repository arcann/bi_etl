import logging


class NotifierBase(object):
    def __init__(self):
        self.log = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

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
