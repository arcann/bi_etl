from typing import List

from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.credentials import Credentials


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
    token: str
    mention: str = None


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
