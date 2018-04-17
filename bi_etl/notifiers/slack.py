from configparser import ConfigParser

from bi_etl.notifiers.notifier import Notifier


class Slack(Notifier):
    def __init__(self, config: ConfigParser, config_section: str):
        # noinspection PyUnresolvedReferences
        from slackclient import SlackClient

        super().__init__(config=config,
                         config_section=config_section)
        slack_token = config[config_section]['token']
        self.slack_client = SlackClient(slack_token)
        self.slack_channel = config[config_section]['channel']

    def send(self, message, subject=None, throw_exception=False):
        if subject:
            message_to_send = "{}: {}".format(subject, message)
        else:
            message_to_send = message
        result = self.slack_client.api_call(
            "chat.postMessage",
            channel=self.slack_channel,
            text=message_to_send
        )
        if not result['ok']:
            self.log.error(result)
