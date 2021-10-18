from configparser import ConfigParser

import keyring

from bi_etl.notifiers.notifier import Notifier


class Jira(Notifier):
    def __init__(self, config: ConfigParser, config_section: str = 'Jira'):
        super().__init__(config=config,
                         config_section=config_section)
        # https://jira.pepfar.net/browse/DMA-1465
        # BEGIN New code to fix jira.client
        import jira.client
        # Jira Client 2.0 comes with a faulty version of CaseInsensitiveDict.
        # Replace it with a better implementation
        # Note: The jira github version at https://github.com/pycontribs/jira
        #       has a fix for this, but that is not available on pypi https://pypi.org/project/jira/#history
        from CaseInsensitiveDict import CaseInsensitiveDict
        jira.client.CaseInsensitiveDict = CaseInsensitiveDict
        # END New code to fix jira.client

        import jira.client
        # Jira Client 2.0 comes with a faulty version of CaseInsensitiveDict.
        # Replace it with a better implementation
        # Note: The jira github version at https://github.com/pycontribs/jira
        #       has a fix for this, but that is not available on pypi https://pypi.org/project/jira/#history
        from CaseInsensitiveDict import CaseInsensitiveDict
        jira.client.CaseInsensitiveDict = CaseInsensitiveDict
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

    def search(self, subject):
        # Find already opened case, if there is one
        found_issues = list()
        # Remove any special characters that break JQL parsing
        # https://support.atlassian.com/jira-software-cloud/docs/search-syntax-for-text-fields/
        subject_escaped = subject
        reserved_list = [
            '\\', '+', '-', '[', ']', '(', ')', '{', '}',
            'AND', 'OR', 'NOT',
            '"', "'", '|', '&&', '!', '*', ':',
            '?', '~', '^', '%',
            '\t', '\n', '\r',
        ]
        for reserved in reserved_list:
            subject_escaped = subject_escaped.replace(reserved, ' ')

        issues = self.jira_conn.search_issues(
            f'project="{self.project}" '
            f'AND summary~"{subject_escaped}" '
            f'AND status not in ({self.exclude_statuses_filter})'
        )
        for iss in issues:
            # Double check that name matches since JIRA does a wildcard search and word stemming
            if iss.fields.summary.strip() == subject:
                # self.log.debug('Potential match:')
                # self.log.debug(p.fields.status)
                # self.log.debug(p.fields.summary)
                # self.log.debug(p.fields.description)
                found_issues.append(iss)
                case_number = iss.key
        return found_issues

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

        if message is None:
            message = "_No Description Provided_"

        message_parts = [
            message,
        ]
        if sensitive_message is not None:
            message_parts.append(sensitive_message)

        existing_issues = self.search(subject)
        if len(existing_issues) > 1:
            self.log.warning(f"Found multiple open issues with subject {subject}. Finding newest...")
            newest_case_number = 0
            newest_iss = None
            for iss in existing_issues:
                case_number = iss.key
                self.log.info(f"One of multiple existing open cases is {case_number}.")
                # https: // jira.pepfar.net / browse / DMA - 1465
                # Fixed the issue in the file by getting the int value for case_number
                if int(case_number.replace('DMA-','')) > newest_case_number:
                    newest_case_number = int(case_number.replace('DMA-',''))
                    newest_iss = iss
            existing_issues = [newest_iss]
            # Allow the section below to comment on the newest issue

        if len(existing_issues) == 1:
            iss = existing_issues[0]
            case_number = iss.key
            self.log.info(f"Found existing open case {case_number}.")
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
