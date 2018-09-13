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
        self.slack_channel = config.get(config_section, 'channel', fallback=None)
        self.mention = config.get(config_section, 'mention', fallback=None)
        if self.slack_channel is None:
            self.log.warning("Slack channel not set. No slack messages will be sent.")

    def send(self, message, subject=None, throw_exception=False):
        if self.slack_channel is not None and self.slack_channel != 'OVERRIDE_THIS_SETTING':
            if subject:
                message_to_send = "{}: {}".format(subject, message)
            else:
                message_to_send = message

            if self.mention:
                message_to_send += ' ' + self.mention

            result = self.slack_client.api_call(
                "chat.postMessage",
                channel=self.slack_channel,
                text=message_to_send
            )
            if not result['ok']:
                self.log.error('slack error: {} for channel {}'.format(
                    result,
                    self.slack_channel,
                ))
        else:
            self.log.info("Slack message not sent: {}".format(message))
