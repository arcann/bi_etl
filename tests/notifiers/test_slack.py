import time
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from config_wrangler.config_templates.logging_config import LoggingConfig

from bi_etl.config.bi_etl_config_base import Notifiers, BI_ETL_Config_Section, BI_ETL_Config_Base
from bi_etl.config.notifiers_config import SlackNotifier
from bi_etl.notifiers import Slack
from tests.config_for_tests import EnvironmentSpecificConfigForTests


class TestSlackMock(unittest.TestCase):
    __test__ = False

    @classmethod
    def setUpClass(cls):
        # patcher = patch('slack')
        # self.MockSlack = patcher.start()
        # self.addCleanup(patcher.stop)

        pass

    def get_slack_notifier(self):
        tmp_obj = TemporaryDirectory()
        tmp = tmp_obj.name

        class ConfigForSlackMock(BI_ETL_Config_Base):
            slack_config: SlackNotifier

        config = ConfigForSlackMock(
            logging=LoggingConfig(
                log_folder=tmp,
                log_levels={'root': 'INFO'},
            ),
            bi_etl=BI_ETL_Config_Section(
                environment_name='test'
            ),
            notifiers=Notifiers(
                failures=[],
            ),
            slack_config=SlackNotifier(
                channel='Mock',
                token='mock',
            )
        )
        return Slack(config.slack_config)

    def test_no_slack(self,):
        no_module = MagicMock()
        no_module.function.return_value = ImportError
        with patch.dict('sys.modules', slack=no_module):
            with patch.dict('sys.modules', slack_sdk=no_module):
                with self.assertRaises(ImportError):
                    notifier = self.get_slack_notifier()
                    notifier.send('Subject', 'test_send')

    def test_send_v2(self):
        try:
            from slack_sdk import WebClient
            with patch('slack_sdk.WebClient') as mock_slack_sdk:
                no_module = MagicMock()
                no_module.function.return_value = ImportError
                with patch.dict('sys.modules', slack=no_module):
                    notifier = self.get_slack_notifier()
                    notifier.send('Subject', 'test_send')
                    mock_slack_sdk.return_value.chat_postMessage.assert_called_once_with(
                        channel='Mock',
                        text=f"Subject: test_send",
                        link_names=False
                    )
        except ImportError:
            raise self.skipTest("slack_sdk not installed")


class BaseTestLiveSlack(unittest.TestCase):
    __test__ = False

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
        self._setUp('Slack_Test_direct')


class TestSlackKeyring(BaseTestLiveSlack):
    def setUp(self, slack_config=None):
        self._setUp('Slack_Test_Keyring')


class TestSlackKeePass(BaseTestLiveSlack):
    def setUp(self, slack_config=None):
        self._setUp('Slack_Test_Keepass')
