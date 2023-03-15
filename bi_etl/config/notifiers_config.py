from typing import List

from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.credentials import Credentials
from config_wrangler.config_templates.keepass_config import KeepassConfig
from config_wrangler.config_templates.password_source import PasswordSource


class NotifierConfigBase(ConfigHierarchy):
    notifier_class: str


class LogNotifierConfig(NotifierConfigBase):
    notifier_class: str = 'bi_etl.notifiers.log_notifier.LogNotifier'


class SMTP_Notifier(NotifierConfigBase, Credentials):
    notifier_class: str = 'bi_etl.notifiers.email.Email'
    email_from: str
    gateway_host: str = None
    gateway_port: int = 0
    use_ssl: bool = False
    debug: bool = False
    distro_list: List[str]


class SlackNotifier(NotifierConfigBase):
    notifier_class: str = 'bi_etl.notifiers.slack.Slack'
    channel: str
    token: str = None
    """
    This is only used for the extremely non-secure `CONFIG_FILE` token source 
    valid values defined using `PasswordSource`.
    The token is stored directly in the config file with the setting 
    name `token`
    """

    mention: str = None

    token_source: PasswordSource = None
    """
    The source to use when getting a token for slack.  
    See :py:class:`PasswordSource` for valid values.
    """

    keyring_section: str = None
    """
    If the password_source is KEYRING, then which section (AKA system)
    should this module look for the password in.
    
    See https://pypi.org/project/keyring/
    or https://github.com/jaraco/keyring
    """
    keepass_config: str = 'keepass'
    """
    If the password_source is KEEPASS, then which root level config item contains
    the settings for Keepass (must be an instance of 
    :py:class:`config_wrangler.config_templates.keepass_config.KeepassConfig`)
    """
    keepass: KeepassConfig = None
    """
    If the password_source is KEEPASS, then load a sub-section with the 
    :py:class:`config_wrangler.config_templates.keepass_config.KeepassConfig`) settings
    """

    keepass_group: str = None
    """
    If the password_source is KEEPASS, which group in the Keepass database should
    be searched for an entry with a matching entry.
    
    If is None, then the `KeepassConfig.default_group` value will be checked.
    If that is also None, then a ValueError will be raised.
    """

    keepass_title: str = None
    """
    If the password_source is KEEPASS, this is an optional filter on the title
    of the keepass entries in the group.
    """


class JiraNotifier(NotifierConfigBase, Credentials):
    notifier_class: str = 'bi_etl.notifiers.jira.Jira'
    server: str
    project: str
    component: str = None
    comment_on_each_instance: bool
    exclude_statuses: List[str] = ['Closed']
    issue_type: str = 'Bug'
    priority: str = None
    subject_prefix: str = ''
    comment_on_each_instance: bool = True
