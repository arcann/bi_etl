from time import sleep

import bi_etl.config.notifiers_config as notifiers_config
from bi_etl.notifiers.notifier_base import NotifierBase


class Slack(NotifierBase):
    def __init__(self, config_section: notifiers_config.SlackNotifier):
        super().__init__()
        self.config_section = config_section

        try:
            # noinspection PyUnresolvedReferences
            from slack import WebClient as SlackClient
            self.log.debug("Using slackclient v2+ import")
            self._client_version = 2
            from slack.errors import SlackApiError
            self.SlackApiError = SlackApiError
        except ImportError:
            self.log.debug("Trying slackclient v1 import")
            # noinspection PyUnresolvedReferences
            from slackclient import SlackClient
            # noinspection PyUnresolvedReferences
            from slackclient.exceptions import SlackClientError
            self.SlackApiError = SlackClientError
            self._client_version = 1

        slack_token = self.config_section.token
        self.slack_client = SlackClient(slack_token)
        self.slack_channel = self.config_section.channel
        self.mention = self.config_section.mention

        if self.slack_channel is None or self.slack_channel == 'OVERRIDE_THIS_SETTING':
            self.log.warning("Slack channel not set. No slack messages will be sent.")
            self.slack_channel = None

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
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
                if self._client_version == 1:
                    # noinspection PyArgumentList
                    result = self.slack_client.api_call(
                        "chat.postMessage",
                        channel=self.slack_channel,
                        text=message_to_send,
                        link_names=link_names,
                    )
                    # Slack API v1 doeesn't raise errors instead returns error result
                    if result['ok']:
                        retry = False
                    else:
                        if result['error'] == 'ratelimited':
                            self.log.info('Waiting for slack ratelimited to clear')
                            sleep(1.5)
                            retry = True
                        else:
                            self.log.error('slack error: {} for channel {}'.format(
                                result,
                                self.slack_channel,
                            ))
                            retry = False
                else:
                    # https://api.slack.com/methods/chat.postMessage
                    try:
                        self.slack_client.chat_postMessage(
                            channel=self.slack_channel,
                            text=message_to_send,
                            link_names=link_names,
                        )
                        retry = False
                    except self.SlackApiError as e:
                        self.log.error(e)
                        if e.response['error'] == 'ratelimited':
                            self.log.info('Waiting for slack ratelimited to clear')
                            sleep(1.5)
                            # See retry loop above
                        else:
                            raise
        else:
            self.log.info("Slack message not sent: {}".format(message))
