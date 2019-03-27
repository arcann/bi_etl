from configparser import ConfigParser
from time import sleep

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

        if self.slack_channel is not None and self.slack_channel.lower().startswith('get from'):
            channel_section = self.slack_channel[9:]
            self.slack_channel = config.get(channel_section, 'channel', fallback=None)

        if self.slack_channel is None or self.slack_channel == 'OVERRIDE_THIS_SETTING':
            self.log.warning("Slack channel not set. No slack messages will be sent.")
            self.slack_channel = None

    def send(self, subject, message, throw_exception=False):
        if self.slack_channel is not None and self.slack_channel != '':
            if subject and message:
                message_to_send = "{}: {}".format(subject, message)
            else:
                if message:
                    message_to_send = message
                else:
                    message_to_send = subject

            if self.mention:
                message_to_send += ' ' + self.mention
                link_names = True
            else:
                link_names = False

            retry = True

            while retry:
                result = self.slack_client.api_call(
                    "chat.postMessage",
                    channel=self.slack_channel,
                    text=message_to_send,
                    link_names=link_names
                )
                if result['ok']:
                    retry = False
                else:
                    if result['error'] == 'ratelimited':
                        self.log.info('Waiting for ratelimited to clear')
                        sleep(1.5)
                        retry = True
                    else:
                        self.log.error('slack error: {} for channel {}'.format(
                            result,
                            self.slack_channel,
                        ))
                        retry = False
        else:
            self.log.info("Slack message not sent: {}".format(message))
