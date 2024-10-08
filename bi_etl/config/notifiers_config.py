from typing import List, Optional

from config_wrangler.config_templates.config_hierarchy import ConfigHierarchy
from config_wrangler.config_templates.credentials import Credentials
from config_wrangler.config_templates.keepass_config import KeepassConfig
from config_wrangler.config_templates.password_source import PasswordSource
from config_wrangler.validate_config_hierarchy import config_hierarchy_validator
from pydantic import PrivateAttr


class NotifierConfigBase(ConfigHierarchy):
    notifier_class: str

    include_sensitive: bool = False
    """
    Include the sensitive_message send() parameter value in this notifiers output?
    
    This allows some notifiers to include only the non-sensitive message parts while others include
    the sensitive details.
    """


class LogNotifierConfig(NotifierConfigBase):
    notifier_class: str = 'bi_etl.notifiers.log_notifier.LogNotifier'


class SMTP_Notifier(NotifierConfigBase, Credentials):
    notifier_class: str = 'bi_etl.notifiers.email.Email'
    email_from: str
    gateway_host: Optional[str] = None
    gateway_port: int = 0
    use_ssl: bool = False
    debug: bool = False
    distro_list: List[str]


class SlackNotifier(NotifierConfigBase):
    notifier_class: str = 'bi_etl.notifiers.slack.Slack'
    channel: str
    token: Optional[str] = None
    """
    This is only used for the extremely non-secure `CONFIG_FILE` token source 
    valid values defined using `PasswordSource`.
    The token is stored directly in the config file with the setting 
    name `token`
    """

    mention: Optional[str] = None
    """
    Channel notification tags to use. For example @channel for all members. 
    """

    token_source: Optional[PasswordSource] = None
    """
    The source to use when getting a token for slack.  
    See :py:class:`PasswordSource` for valid values.
    """

    keyring_section: Optional[str] = None
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

    keepass: Optional[KeepassConfig] = None
    """
    If the password_source is KEEPASS, then load a sub-section with the 
    :py:class:`config_wrangler.config_templates.keepass_config.KeepassConfig`) settings
    """

    keepass_group: Optional[str] = None
    """
    If the password_source is KEEPASS, which group in the Keepass database should
    be searched for an entry with a matching entry.
    
    If is None, then the `KeepassConfig.default_group` value will be checked.
    If that is also None, then a ValueError will be raised.
    """

    keepass_title: Optional[str] = None
    """
    If the password_source is KEEPASS, this is an optional filter on the title
    of the keepass entries in the group.
    """

    # Values to hide from config exports
    _private_value_atts = PrivateAttr(default={'token'})


class JiraNotifier(NotifierConfigBase, Credentials):
    notifier_class: str = 'bi_etl.notifiers.jira.Jira'
    server: str
    """
    HTTP previs for the Jira server to connect to (e.g. https://jira.example.net)
    """

    project: str
    """
    Project to add issues to.
    """

    component: Optional[str] = None
    """
    Component to tag on the issues created.
    """

    comment_on_each_instance: bool = True
    """
    Add a comment on each new instance of the same issue subject.
    """

    exclude_statuses: List[str] = ['Closed']
    """
    When searching for existing instances, exclude issues with these statuses.
    """

    issue_type: str = 'Bug'
    """
    Type of issues to create.
    """

    priority: Optional[str] = None
    """
    Priority to create issues with. None for project default.
    """

    subject_prefix: str = ''
    """
    Prefix to add to issue subjects.
    """

    include_sensitive: bool = True

    update_description: bool = True
    """
    Update the issue description on each incident if an issue.
    """

    add_date_to_message: bool = True
    """
    Add the current date/time to the issue description.
    """

    track_incident_count: bool = True
    """
    Add a count of the number of occurrences of an issue.  
    Only valid if update_description is True.  
    """

    incident_count_prefix: str = 'Count of incidents: '
    """
    The line prefix for the count of incidents
    """

    # Settings for comment / attachment cleanup
    keep_first_comment: bool = True
    """
    Keep the first comment made on the issue.
    Note: Only impacts comments made by the bot user id.
    """

    recent_comments_to_keep: int = 1
    """
    Only used if comment_on_each_instance = True.
    The number of recent comments to keep. It will always keep the newest
    comment, so this has no impact until it is 2 or greater.
    Note: Only impacts comments made by the bot user id.
    """

    keep_first_attachment: bool = True
    """
    Keep the first attachment saved to the issue.
    Note: Only impacts attachments made by the bot user id.
    """

    recent_attachments_to_keep: int = 1
    """
    Only used if comment_on_each_instance = True.
    The number of attachments comments to keep. It will always keep the newest
    attachment, so this has no impact until it is 2 or greater.
    Note: Only impacts attachments made by the bot user id.
    """

    auto_header_color: str = 'C1C7D0'
    """
    Color to use for automatic headers and footers (html hex format).
    """

    auto_header_begin_text: str = '— Begin Automatic Update Section —'
    auto_header_end_text: str = '— End Automatic Update Section —'

    @config_hierarchy_validator
    def _validate(self):
        if self.track_incident_count:
            if not self.update_description:
                raise ValueError(f"Can't track_incident_count without update_description = True")
