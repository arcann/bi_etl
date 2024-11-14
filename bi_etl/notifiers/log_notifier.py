from typing import Optional

from bi_etl.notifiers.notifier_base import NotifierBase, NotifierAttachment
import bi_etl.config.notifiers_config as notifiers_config


class LogNotifier(NotifierBase):
    def __init__(self, *, name: Optional[str] = None):
        super().__init__(name=name)
        self.config_section = notifiers_config.LogNotifierConfig()

    def send(
            self,
            subject: str,
            message: str,
            sensitive_message: str = None,
            attachment: Optional[NotifierAttachment] = None,
            throw_exception: bool = False,
            **kwargs
    ):
        self.warn_kwargs(**kwargs)
        if subject is not None:
            self.log.info(subject)
        if message is not None:
            self.log.info(message)
        if sensitive_message is not None and self.config_section.include_sensitive:
            self.log.info(sensitive_message)
