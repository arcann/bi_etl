from configparser import ConfigParser

import keyring

from bi_etl.notifiers.notifier import Notifier


class Jira(Notifier):
    def __init__(self, config: ConfigParser, config_section: str = 'Jira'):
        super().__init__(config=config,
                         config_section=config_section)

        from jira.client import JIRA
        from jira.exceptions import JIRAError
        self.config_section = config_section
        options = dict()
        options['server'] = config.get(self.config_section, 'server')
        user_id = config.get(self.config_section, 'user_id')
        self.project = config.get(self.config_section, 'project')
        self.keyring_section = config.get(self.config_section, 'keyring_section')
        password = keyring.get_password(self.keyring_section, user_id)
        if password is None or password == '':
            raise ValueError(f'Jira password not provided in keyring {self.keyring_section} {user_id}')
        self.log.debug(f"user id={user_id}")
        self.log.debug(f"server={options['server']}")
        self.log.debug(f'project={self.project}')

        try:
            self.jira_conn = JIRA(options, basic_auth=(user_id, password))
        except JIRAError as e:
            if 'CAPTCHA_CHALLENGE' in e.text:
                raise RuntimeError(f'Jira Login requests passing CAPTCHA CHALLENGE.  {e.text}')
            else:
                self.log.error(f'Error connecting to JIRA')
                self.log.exception(e)
                raise
        priority_name = config.get(self.config_section, 'priority', fallback=None)
        if priority_name is not None:
            for priority_object in self.jira_conn.priorities():
                if priority_object.name == priority_name:
                    self.priority_id = priority_object.id
            self.log.debug(f'priority_name = {priority_name} priority_id={self.priority_id}')
        else:
            self.priority_id = None
            self.log.debug('priority not specified in config')

        self.subject_prefix = self.config.get(self.config_section, 'subject_prefix', fallback='')
        self.comment_on_each_instance = self.config.getboolean(self.config_section, 'comment_on_each_instance', fallback=True)
        self.component = self.config.get(self.config_section, 'component', fallback=None)
        self.issue_type = self.config.get(self.config_section, 'issue_type', fallback='Bug')
        exclude_statuses = self.config.get_list(self.config_section, 'exclude_statuses', fallback='Closed')
        exclude_statuses_filter_list = []
        for status in exclude_statuses:
            exclude_statuses_filter_list.append(f'"{status}"')
        self.exclude_statuses_filter = ','.join(exclude_statuses_filter_list)

    def add_attachment(self, issue, attachment):
        """Attach an attachment to an issue and returns a Resource for it.

        The client will *not* attempt to open or validate the attachment; it expects a file-like object to be ready
        for its use. The user is still responsible for tidying up (e.g., closing the file, killing the socket, etc.)

        :param issue: the issue to attach the attachment to
        :param attachment:
            file-like object to attach to the issue, also works if it is a string with the filename,
            or a tuple with a file-like object and a filename.

            If the (file, filename) tuple is not used the file object's ``name`` attribute
            is used. If you acquired the file-like object by any other method than ``open()``, make sure
            that a name is specified in one way or the other.
        :rtype: an Attachment Resource
        """
        if isinstance(attachment, tuple):
            attachment, filename = attachment
        else:
            filename = None

        return self.jira_conn.add_attachment(issue=issue, attachment=attachment, filename=filename)

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        """
        Log a Jira issue

        To use special formatting codes plesae see
        https://jira.atlassian.com/secure/WikiRendererHelpAction.jspa?section=all

        :param subject:
        :param message:
        :param sensitive_message:
        :param attachment:
        :param throw_exception:
        :return:
        """
        if subject is None:
            raise ValueError(f"Jira notifier requires a valid subject. Message was {message}")
        else:
            subject = self.subject_prefix + subject.strip()
        self.log.debug(f'subject={subject}')
        self.log.debug(f'message={message}')

        message_parts = [
            message,
        ]
        if sensitive_message is not None:
            message_parts.append(sensitive_message)

        found = False
        # Find already opened case, if there is one
        subject_escaped = subject.replace('\\', '\\\\')
        subject_escaped = subject_escaped.replace('"', '\"')
        subject_escaped = subject_escaped.replace("'", "\'")

        issues = self.jira_conn.search_issues(
            f'project="{self.project}" '
            f'AND summary~"{subject_escaped}" '
            f'AND status not in ({self.exclude_statuses_filter})'
        )
        for iss in issues:
            # Double check that name matches since JIRA does a wildcard search
            if iss.fields.summary.strip() == subject:
                # self.log.debug(p.fields.status)
                # self.log.debug(p.fields.summary)
                # self.log.debug(p.fields.description)
                found = True
                case_number = iss.key
                if self.comment_on_each_instance:
                    if attachment is not None:
                        attachment_object = self.add_attachment(iss, attachment)
                        self.log.debug(f"Created attachment {attachment_object}")
                    message_parts.insert(0, "New occurrence with message(s):")
                    if message or sensitive_message:
                        comment = '\n'.join(message_parts)
                        self.jira_conn.add_comment(iss, comment)
                        self.log.info(f"Added comment to case {case_number}.")
                    else:
                        self.log.info(f"Found existing open case {case_number}.")
        if not found:
            description = '\n'.join(message_parts)

            issue_dict = {
                'project': {'key': self.project},
                'summary': subject,
                'description': description,
            }
            if self.issue_type is not None:
                issue_dict['issuetype'] = {'name': self.issue_type}
            if self.priority_id:
                issue_dict['priority'] = {'id': self.priority_id}
            if self.component:
                issue_dict['components'] = [{'name': self.component}, ]

            self.log.debug('issue_dict={}'.format(issue_dict))

            new_issue = self.jira_conn.create_issue(fields=issue_dict)
            case_number = new_issue.key
            self.log.info("Created new case {}".format(case_number))

            if attachment is not None:
                attachment_object = self.add_attachment(new_issue, attachment)
                self.log.debug(f"Created attachment {attachment_object}")
