import email
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from typing import Optional

import bi_etl.config.notifiers_config as notifiers_config
from bi_etl.notifiers.notifier_base import NotifierBase, NotifierException, NotifierAttachment


class Email(NotifierBase):
    def __init__(self, config_section: notifiers_config.SMTP_Notifier, *, name: Optional[str] = None):
        super().__init__(name=name)
        self.config_section = config_section

    def send(
            self,
            subject,
            message,
            sensitive_message=None,
            attachment: Optional[NotifierAttachment] = None,
            throw_exception=False
    ):
        distro_list = self.config_section.distro_list
        if not distro_list:
            self.log.warning(f'{self.config_section} distro_list option not found. No mail sent.')

        to_addresses = list()
        if isinstance(distro_list, list):
            to_addresses.extend(distro_list)
        elif isinstance(distro_list, str):
            for to_address in re.split(r'[,;\n]', distro_list):
                to_address = to_address.strip()
                self.log.info(f'Adding {to_address} to send list')
                to_addresses.append(to_address)
        else:
            raise ValueError(f"distro_list not list or string but {type(distro_list)} with value {distro_list}")

        server = None
        try:
            if isinstance(message, email.message.Message):
                if subject is not None:
                    message['subject'] = subject
                if 'To' not in message:
                    message['To'] = ','.join(to_addresses)
                if 'From' not in message:
                    if 'Sender' not in message:
                        message['Sender'] = self.config_section.email_from
            else:
                main_message_parts = []
                if message is None:
                    main_message_parts.append('No description')
                else:
                    main_message_parts.append(message)

                if sensitive_message is not None and self.config_section.include_sensitive:
                    main_message_parts.append(sensitive_message)

                message = MIMEText('\n'.join(main_message_parts))
                if subject is not None:
                    subject_escaped = subject
                    reserved_list = ['\n', '\r']
                    for reserved in reserved_list:
                        subject_escaped = subject_escaped.replace(reserved, ' ')

                    message['subject'] = subject_escaped
                message['Sender'] = self.config_section.email_from
                message['To'] = ','.join(to_addresses)

            if attachment is not None:
                message.attach(MIMEApplication(attachment.bytes_content, Name=attachment.filename))

            gateway = self.config_section.gateway_host
            gateway_port = self.config_section.gateway_port
            gateway_userid = self.config_section.user_id
            gateway_password = self.config_section.get_password()

            use_ssl = self.config_section.use_ssl
            if use_ssl:
                server = smtplib.SMTP_SSL(gateway, port=gateway_port)
            else:
                server = smtplib.SMTP(gateway, port=gateway_port)
            server.set_debuglevel(self.config_section.debug)
            if gateway_userid is not None:
                server.login(gateway_userid, gateway_password)

            results_of_send = server.send_message(message)
            self.log.debug(f"results_of_send = {results_of_send}")

            for recipient in results_of_send:
                self.log.warn(f"Problem sending to: {recipient}")
        except smtplib.SMTPRecipientsRefused as e:
            self.log.critical(f"All recipients were refused.\n{e.recipients}")
            if throw_exception:
                raise NotifierException(e)
        except smtplib.SMTPHeloError as e:
            self.log.critical(f"The server didn't reply properly to the HELO greeting.\n{e}")
            if throw_exception:
                raise NotifierException(e)
        except smtplib.SMTPSenderRefused as e:
            self.log.critical(f"The server didn't accept the from_addr {message.get('Sender', None)}.\n{e}")
            if throw_exception:
                raise NotifierException(e)
        except smtplib.SMTPDataError as e:
            self.log.critical(
                f"The server replied with an unexpected error code (other than a refusal of a recipient).\n{e}"
            )
            if throw_exception:
                raise NotifierException(e)
        finally:
            try:
                if server is not None:
                    reply = server.quit()
                    self.log.debug(f"server quit reply = {reply}")
                    self.log.info('Mail sent')
            except Exception as e:
                self.log.exception(e)
