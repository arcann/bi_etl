from bi_etl.notifiers.email import Email
from bi_etl.notifiers.jira import Jira
from bi_etl.notifiers.log_notifier import LogNotifier
from bi_etl.notifiers.slack import Slack

NOTIFIER_CLASES = {
        'Email': Email,
        'LogNotifier': LogNotifier,
        'Slack': Slack,
        'Jira': Jira,
    }
