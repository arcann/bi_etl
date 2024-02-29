import time
import unittest
from unittest import mock, SkipTest

from bi_etl.config.notifiers_config import SlackNotifier
from bi_etl.notifiers import Slack
from tests.config_for_tests import EnvironmentSpecificConfigForTests


class TestSlackMock(unittest.TestCase):
    def test_send_config_token(self):
        notifier_config = SlackNotifier(
            channel='test',
            token='secret_token'
        )
        try:
            with mock.patch('slack_sdk.WebClient') as client_class:
                notifier = Slack(notifier_config)
                client_class.assert_called_with('secret_token')
                client = client_class.return_value
                notifier.send('Subject', 'test_send')
                client.chat_postMessage.assert_called_with(
                    channel='test',
                    text='Subject: test_send',
                    link_names=False
                )
        except ModuleNotFoundError as e:
            raise SkipTest(f"Slack mock failed {e}")

    # TODO: Mock response['error'] == 'ratelimited'
    # TODO: Mock post_status scenarios
    # TODO: Test with keepass / keyring. Do we mock those?


class BaseTestLiveSlack(unittest.TestCase):
    def setUp(self, slack_config=None):
        raise unittest.SkipTest(f"Skip BaseTestLiveSlack")

    def _setUp(self, slack_config_name: str):
        # Note use tox.ini to test using different slack libraries
        self.slack_config = None
        self.env_config = None
        try:
            self.env_config = EnvironmentSpecificConfigForTests()
            # Inherited classes should set slack_config
            self.slack_config = getattr(self.env_config, slack_config_name)
            if self.slack_config is None:
                raise unittest.SkipTest(f"Skip {self} due to no {slack_config_name} section")
            else:
                self.notifier = Slack(self.slack_config)
        except ValueError as e:
            raise unittest.SkipTest(f"Skip {self} due to config error {e}")
        except FileNotFoundError as e:
            raise unittest.SkipTest(f"Skip {self} due to not finding config {e}")
        except ImportError as e:
            raise unittest.SkipTest(f"Skip {self} due to not finding required module {e}")

    def test_send(self):
        self.notifier.send('Subject', 'test_send')

    def test_status(self):
        for i in range(1, 3):
            self.notifier.post_status(f'test_status {i}')
            time.sleep(0.1)
        self.notifier.send('Send', 'interrupts status')
        for i in range(3, 5):
            self.notifier.post_status(f'test_status {i}')
            time.sleep(0.1)


class TestSlackDirect(BaseTestLiveSlack):
    def setUp(self, slack_config=None):
        # Use the config in section Slack_Test_direct of tests/test_config.ini
        self._setUp('Slack_Test_direct')


class TestSlackKeyring(BaseTestLiveSlack):
    def setUp(self, slack_config=None):
        # Use the config in section Slack_Test_Keyring of tests/test_config.ini
        self._setUp('Slack_Test_Keyring')


class TestSlackKeePass(BaseTestLiveSlack):
    def setUp(self, slack_config=None):
        # Use the config in section Slack_Test_Keepass of tests/test_config.ini
        self._setUp('Slack_Test_Keepass')
