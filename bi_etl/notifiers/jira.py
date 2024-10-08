import warnings
from datetime import datetime
from enum import Enum, auto
from typing import Optional, List

import bi_etl.config.notifiers_config as notifiers_config
from bi_etl.notifiers.notifier_base import NotifierBase, NotifierAttachment


class Jira(NotifierBase):

    def __init__(self, config_section: notifiers_config.JiraNotifier, *, name: Optional[str] = None):
        super().__init__(name=name)
        self.config_section = config_section

        # On-instance import since jira is an optional requirement
        # noinspection PyUnresolvedReferences
        from jira.client import JIRA
        # noinspection PyUnresolvedReferences
        from jira.exceptions import JIRAError

        self.config_section = config_section
        options = dict()
        options['server'] = self.config_section.server
        user_id = self.config_section.user_id
        self.project = self.config_section.project
        password = self.config_section.get_password()
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
        priority_name = self.config_section.priority
        if priority_name is not None:
            for priority_object in self.jira_conn.priorities():
                if priority_object.name == priority_name:
                    self.priority_id = priority_object.id
            self.log.debug(f'priority_name = {priority_name} priority_id={self.priority_id}')
        else:
            self.priority_id = None
            self.log.debug('priority not specified in config')

        self.subject_prefix = self.config_section.subject_prefix
        self.comment_on_each_instance = self.config_section.comment_on_each_instance
        self.component = self.config_section.component
        self.issue_type = self.config_section.issue_type
        exclude_statuses = self.config_section.exclude_statuses
        exclude_statuses_filter_list = []
        for status in exclude_statuses:
            exclude_statuses_filter_list.append(f'"{status}"')
        self.exclude_statuses_filter = ','.join(exclude_statuses_filter_list)

        self.auto_color_open_tag = f"{{color:#{self.config_section.auto_header_color}}}"
        self.auto_color_close_tag = "{color}"
        self.begin_auto_search_part = self.config_section.auto_header_begin_text
        self.begin_auto_line = ' '.join([self.auto_color_open_tag, self.begin_auto_search_part, self.auto_color_close_tag])
        self.end_auto_search_part = self.config_section.auto_header_end_text
        self.end_auto_line = ' '.join([self.auto_color_open_tag, self.end_auto_search_part, self.auto_color_close_tag])

    def add_attachment(
            self,
            issue,
            attachment: NotifierAttachment,
    ):
        """
        Attach an attachment to an issue and returns a Resource for it.
        """
        if isinstance(attachment, tuple):
            warnings.warn(
                "tuple attachment (BufferedReader, filename) to Jira notifier is deprecated. "
                "Send NotifierAttachment instance instead."
            )
            io_reader, filename = attachment
            attachment = NotifierAttachment(io_reader, filename=filename)

        return self.jira_conn.add_attachment(issue=issue, attachment=attachment.binary_reader, filename=attachment.filename)

    def cleanup_attachments(
            self,
            issue,
            keep_first_attachment: bool,
            recent_attachments_to_keep: int,
    ):
        all_attachments = issue.fields.attachment
        user_attachments = []
        for attachment in all_attachments:
            if attachment.author.name == self.config_section.user_id:
                user_attachments.append(attachment)
        self.log.debug(f"Found {len(user_attachments)} user attachments")
        if len(user_attachments) > 0:
            self.log.debug(f"First user attachment = {user_attachments[0]}")
            self.log.debug(f"Last user attachment = {user_attachments[-1]}")
            keep_set = set()
            if keep_first_attachment:
                keep_set.add(user_attachments[0])
            if recent_attachments_to_keep > 0:
                keep_set.update(user_attachments[-1 * recent_attachments_to_keep:])
            for attachment in user_attachments:
                if attachment not in keep_set:
                    self.log.info(f"Deleting attachment {attachment}")
                    attachment.delete()

    def cleanup_comments(
            self,
            issue,
            keep_first_comment: bool,
            recent_comments_to_keep: int,
    ):
        all_comments = issue.fields.comment.comments
        user_comments = []
        for comment in all_comments:
            if comment.author.name == self.config_section.user_id:
                user_comments.append(comment)
        self.log.debug(f"Found {len(user_comments)} user comments")
        if len(user_comments) > 0:
            self.log.debug(f"First user comment = {user_comments[0].created}")
            self.log.debug(f"Last user comment = {user_comments[-1].created}")
            keep_set = set()
            # TODO: The first comment is not comments[0]. It is in the description text.
            #       However we need to not wipe out the human edits to that.
            #       Maybe add an HR ---- and/or h6. Smallest heading
            #       With a note that everything between that and the next marker will be
            #       removed by the bot.
            # issue.fields.description
            if keep_first_comment:
                keep_set.add(user_comments[0])
            if recent_comments_to_keep > 0:
                keep_set.update(user_comments[-1 * recent_comments_to_keep:])
            for comment in user_comments:
                if comment not in keep_set:
                    self.log.info(f"Deleting comment #{comment} from {comment.created}")
                    comment.delete()

    def update_description(
            self,
            issue,
            new_message_parts: List[str],
    ):
        class SearchStage(Enum):
            before_auto = auto()
            inside_auto = auto()
            after_auto = auto()

        description = issue.fields.description
        lines_before = list()
        auto_lines = list()
        lines_after = list()
        stage = SearchStage.before_auto
        previous_count = 1
        for num, line in enumerate(description.split('\n')):
            match stage:
                case SearchStage.before_auto:
                    if self.begin_auto_search_part in line:
                        stage = SearchStage.inside_auto
                        auto_lines.append(line)
                    else:
                        lines_before.append(line)
                case SearchStage.inside_auto:
                    if self.config_section.track_incident_count:
                        if self.config_section.incident_count_prefix in line:
                            prefix_pos = line.find(self.config_section.incident_count_prefix)
                            count_pos = prefix_pos + len(self.config_section.incident_count_prefix)
                            count_str = line[count_pos:]
                            try:
                                previous_count = int(count_str)
                            except ValueError:
                                previous_count = None
                    auto_lines.append(line)
                    if self.end_auto_search_part in line:
                        stage = SearchStage.after_auto
                case SearchStage.after_auto:
                    lines_after.append(line)

        if self.config_section.track_incident_count:
            # Update the new message with the incremented counter
            updated_new_message_parts = []
            for line in new_message_parts:
                if self.config_section.incident_count_prefix in line:
                    if previous_count is None:
                        count_str = 'Error'
                    else:
                        count_str = previous_count + 1
                    updated_new_message_parts.append(f"{self.config_section.incident_count_prefix}{count_str}")
                else:
                    updated_new_message_parts.append(line)
            new_message_parts = updated_new_message_parts

        # Build the new description with any manual text found + the new automated message
        new_description_lines = list()
        if len(lines_before) > 0:
            new_description_lines.extend(lines_before)
            new_description_lines.append("\n")
        new_description_lines.extend(new_message_parts)
        new_description_lines.extend(lines_after)

        new_description = '\n'.join(new_description_lines)

        self.log.debug(f"Updating {issue} description:\n{new_description}")
        issue.update(description=new_description)

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
        return found_issues

    def send(
            self,
            subject,
            message,
            sensitive_message=None,
            attachment: Optional[NotifierAttachment] = None,
            throw_exception=False
    ):
        """
        Log a Jira issue

        To use special formatting codes please see
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

        if message is None or message == '':
            message = "_No Description Provided_"

        main_message_parts = [message]
        if sensitive_message is not None and self.config_section.include_sensitive:
            main_message_parts.append(sensitive_message)
        main_message = '\n'.join(main_message_parts)

        message_parts = [
            self.begin_auto_line,
        ]
        if self.config_section.add_date_to_message:
            message_parts.append(f"Content from: {datetime.now().isoformat()}")

        if self.config_section.update_description:
            if self.config_section.track_incident_count:
                message_parts.append(f"{self.config_section.incident_count_prefix}1")

        message_parts.append(main_message)

        message_parts.append(self.end_auto_line)

        existing_issues = self.search(subject)
        if len(existing_issues) > 1:
            self.log.warning(f"Found multiple open issues with subject {subject}. Finding newest...")
            newest_case_number = 0
            newest_iss = None
            for iss in existing_issues:
                case_number = iss.key
                self.log.info(f"One of multiple existing open cases is {case_number}.")
                # Fixed the issue in the file by getting the int value for case_number
                proj_code, case_num = case_number.split('-')
                case_num_int = int(case_num)
                if case_num_int > newest_case_number:
                    newest_case_number = case_num_int
                    newest_iss = iss
            existing_issues = [newest_iss]
            # Allow the section below to comment on the newest issue

        if len(existing_issues) == 1:
            iss = existing_issues[0]
            case_number = iss.key
            self.log.info(f"Found existing open case {case_number}.")
            if self.config_section.update_description:
                self.update_description(iss, message_parts)

            if self.comment_on_each_instance:
                # Cleanup existing comments and attachments
                self.cleanup_comments(
                    issue=iss,
                    keep_first_comment=self.config_section.keep_first_comment,
                    # Keep one less recent comment since we are about to add one
                    recent_comments_to_keep=self.config_section.recent_comments_to_keep - 1,
                )
                self.cleanup_attachments(
                    issue=iss,
                    keep_first_attachment=self.config_section.keep_first_attachment,
                    # Keep one less recent attachment since we are about to add one
                    recent_attachments_to_keep=self.config_section.recent_attachments_to_keep - 1,

                )
                if attachment is not None:
                    attachment_object = self.add_attachment(iss, attachment)
                    self.log.debug(f"Created attachment {attachment_object}")
                message_parts.insert(0, "New occurrence with message(s):")
                if main_message != '':
                    self.jira_conn.add_comment(iss, main_message)
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

            self.log.debug(f'issue_dict={issue_dict}')

            new_issue = self.jira_conn.create_issue(fields=issue_dict)
            case_number = new_issue.key
            self.log.info(f"Created new case {case_number}")

            if attachment is not None:
                attachment_object = self.add_attachment(new_issue, attachment)
                self.log.debug(f"Created attachment {attachment_object}")

            # If we want to keep the first incident message it needs to be in a comment
            # Note: We could disable this if update_description is false.
            #       However, the update_description setting could be later changed.
            #       There isn't a good way to go back and add the comment with the correct date.
            #       So best to just add it with the new issue
            if self.config_section.keep_first_comment:
                if main_message != '':
                    self.jira_conn.add_comment(new_issue, main_message)
