import logging
from io import BytesIO, RawIOBase, BufferedIOBase, BufferedReader, TextIOBase, StringIO
from typing import Optional, Union, BinaryIO, TextIO

from bi_etl.config import notifiers_config


class NotifierAttachment:
    def __init__(
        self,
        content: Union[RawIOBase, BinaryIO, TextIO, bytes, str] = None,
        *,
        filename: Optional[str] = None,
    ):
        """

        Parameters
        ----------
        content:
            Content of the attachment.
        filename:
            Optional only if content is a FileIO type object that has name.
            Note: If this name is provided, it overrides content.name value if that also exists.
        """
        if hasattr(content, 'read'):
            try:
                # noinspection PyUnresolvedReferences
                self.filename = content.name
            except AttributeError:
                self.filename = None

            if filename is not None:
                self.filename = filename
            if self.filename is None:
                raise ValueError("filename must be specified in either content.name or filename parameter")
            self._content = content
        else:
            if filename is None:
                raise ValueError("filename must be specified if content is not a BufferedReader")
            self._content = content
            self.filename = filename

    @property
    def binary_reader(self) -> BufferedIOBase:
        if hasattr(self._content, 'read'):
            if hasattr(self._content, 'seek'):
                self._content.seek(0)
            if isinstance(self._content, TextIOBase) or isinstance(self._content, StringIO):
                return BytesIO(self._content.read().encode('utf-8'))
            else:
                return BufferedReader(self._content)
        elif isinstance(self._content, bytes):
            io_reader = BytesIO(self._content)
            return io_reader
        else:
            io_reader = BytesIO(str(self._content).encode("utf-8"))
            return io_reader

    @property
    def str_content(self) -> str:
        if hasattr(self._content, 'read'):
            if hasattr(self._content, 'seek'):
                self._content.seek(0)
            content = self._content.read()
            if isinstance(content, bytes):
                return content.decode("utf-8")
            elif isinstance(content, str):
                return content
            else:
                raise ValueError("content from content.read() was not str or bytes")
        elif isinstance(self._content, bytes):
            return self._content.decode("utf-8")
        else:
            return str(self._content)

    @property
    def bytes_content(self) -> bytes:
        if hasattr(self._content, 'read'):
            if hasattr(self._content, 'seek'):
                self._content.seek(0)
            content = self._content.read()
            if isinstance(content, bytes):
                return content
            elif isinstance(content, str):
                return content.encode("utf-8")
            else:
                raise ValueError("content from content.read() was not str or bytes")
        elif isinstance(self._content, bytes):
            return self._content
        else:
            return str(self._content).encode("utf-8")


class NotifierBase(object):
    def __init__(self, *, name: Optional[str] = None):
        class_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        self.log = logging.getLogger(class_name)
        self.name = name or class_name
        self.config_section = notifiers_config.NotifierConfigBase(notifier_class=class_name)

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
