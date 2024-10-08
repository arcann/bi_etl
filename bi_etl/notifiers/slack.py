import warnings
from time import sleep
from typing import Optional

from config_wrangler.config_templates.credentials import Credentials

import bi_etl.config.notifiers_config as notifiers_config
from bi_etl.notifiers.notifier_base import NotifierBase


class Slack(NotifierBase):
    def __init__(self, config_section: notifiers_config.SlackNotifier, *, name: Optional[str] = None):
        super().__init__(name=name)
        self.config_section = config_section

        try:
            from slack_sdk import WebClient
            self.log.debug("Using slack_sdk import")
            self._client_version = 3
            from slack_sdk.errors import SlackApiError
        except ImportError:
            try:
                # noinspection PyUnresolvedReferences
                from slack import WebClient
                self.log.debug("Using WebClient v2+ import")
                self._client_version = 2
                from slack.errors import SlackApiError
            except ImportError:
                raise ImportError("Slack notifier requires either slack-sdk or slackclient to be installed")
        self.SlackApiError = SlackApiError

        # We need to support putting the token in keepass/keyring
        # slack_token = self.config_section.token
        if self.config_section.token is None or self.config_section.token == '':
            slack_token_credentials = Credentials(
                user_id='slack',
                password_source=self.config_section.token_source,
                raw_password=self.config_section.token,
                keyring_section=self.config_section.keyring_section,
                # keepass_config=self.config_section.keepass_config,
                keepass=self.config_section.keepass,
                keepass_group=self.config_section.keepass_group,
                keepass_title=self.config_section.keepass_title,
            )
            config_section.add_child('slack_token_credentials', slack_token_credentials)
            slack_token = slack_token_credentials.get_password()
        else:
            slack_token = self.config_section.token

        self.slack_client = WebClient(slack_token)
        self.slack_channel = self.config_section.channel
        self.mention = self.config_section.mention
        self._status_channel = None
        self._status_ts = None

        if self.slack_channel is None or self.slack_channel == 'OVERRIDE_THIS_SETTING':
            self.log.warning("Slack channel not set. No slack messages will be sent.")
            self.slack_channel = None

    def _post_message(self, text: str, link_names: bool = False):
        retry = True
        result_data = None
        while retry:
            # https://api.slack.com/methods/chat.postMessage
            try:
                result = self.slack_client.chat_postMessage(
                    channel=self.slack_channel,
                    text=text,
                    link_names=link_names,
                )
                retry = False
                try:
                    result_data = result.data
                    if result_data is None:
                        self.log.error(f"API result has result.data of None {result}")
                except (AttributeError, TypeError):
                    result_data = None
                    self.log.error(f"API result did not include data: {result}")

            except self.SlackApiError as e:
                self.log.error(e)
                if e.response['error'] == 'ratelimited':
                    self.log.info('Waiting for slack ratelimited to clear')
                    sleep(1.5)
                    # See retry loop above
                else:
                    raise
        return result_data

    def _post_update(
            self,
            channel: str,  # Note this does not accept the friendly channel names (see send results)
            ts: str,
            text: str,
            link_names: bool = False
    ):
        # Updates are considered non-critical so we don't retry
        try:
            self.slack_client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                link_names=link_names,
            )
        except self.SlackApiError as e:
            self.log.error(e)
            if e.response['error'] == 'ratelimited':
                # Updates are considered non-critical so rate limiting means we skip the update
                pass
            else:
                raise

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        # Clear the status timestamp so that we create a new status message below this non-status message
        self._status_ts = None
        if self.slack_channel is not None and self.slack_channel != '':
            if subject and message:
                message_to_send = f"{subject}: {message}"
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

            self._post_message(text=message_to_send, link_names=link_names)
            if sensitive_message is not None and self.config_section.include_sensitive:
                self._post_message(text=sensitive_message)

        else:
            self.log.info(f"Slack message not sent: {message}")

    def post_status(self, status_message):
        """
        Send a temporary status messages that gets overwritten with the next status message that is sent.

        Parameters
        ----------
        status_message

        Returns
        -------

        """
        if self._client_version == 1:
            warnings.warn(f"Slack client v1 not supported for post_status")
            return None

        if self.slack_channel is None or self.slack_channel == '':
            self.log.warning(f"slack_channel = '{self.slack_channel}'")
            return None

        if self._status_ts is None:
            result_data = self._post_message(text=status_message)
            if result_data is not None:
                if 'ts' in result_data and 'channel' in result_data:
                    self._status_ts = result_data['ts']
                    self._status_channel = result_data['channel']
        else:
            self._post_update(
                channel=self._status_channel,
                ts=self._status_ts,
                text=status_message
            )
