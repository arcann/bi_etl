import email
import re
import smtplib
from configparser import ConfigParser
from email.mime.text import MIMEText

from bi_etl.notifiers.notifier import Notifier, NotifierException


class Email(Notifier):
    def __init__(self, config: ConfigParser, config_section: str):
        super().__init__(config=config,
                         config_section=config_section)

    def send(self, subject, message, sensitive_message=None, attachment=None, throw_exception=False):
        smtp_to = self.config.get(self.config_section, 'distro_list', fallback=None)
        if not smtp_to:
            self.log.warning("{} distro_list option not found. No mail sent.".format(self.config_section))
        else:
            to_addresses = list()
            for addr in re.split(r'[,;\n]', smtp_to):
                addr = addr.strip()
                self.log.info('Adding {} to send list'.format(addr))
                to_addresses.append(addr)

            server = None
            try:
                if isinstance(message, email.message.Message):
                    if subject is not None:
                        message['subject'] = subject
                    if 'To' not in message:
                        message['To'] = ','.join(to_addresses)
                    if 'From' not in message:
                        if 'Sender' not in message:
                            message['Sender'] = self.config.get('SMTP', 'from')
                else:
                    if message is None:
                        message = ''
                    message = MIMEText(message)
                    if subject is not None:
                        subject_escaped = subject
                        reserved_list = ['\n', '\r']
                        for reserved in reserved_list:
                            subject_escaped = subject_escaped.replace(reserved, ' ')

                        message['subject'] = subject_escaped
                    message['Sender'] = self.config.get('SMTP', 'from')
                    message['To'] = ','.join(to_addresses)

                gateway = self.config.get('SMTP', 'gateway')
                gateway_port = self.config.getint('SMTP', 'gateway_port', fallback=0)
                gateway_userid = self.config.get('SMTP', 'gateway_userid', fallback=None)
                gateway_password = self.config.get('SMTP', 'gateway_password', fallback=None)
                if gateway_userid is not None and gateway_password is None:
                    try:
                        # noinspection PyUnresolvedReferences
                        import keyring
                        gateway_password = keyring.get_password(gateway, gateway_userid)
                        if gateway_password is None:
                            raise KeyError("Config SMTP gateway_password not provided, "
                                           "and {}.{} not found in keyring password storage"
                                           .format(gateway, gateway_userid))
                    except ImportError:
                        raise KeyError("Config SMTP gateway_password not provided, and keyring not installed. "
                                       "When trying to get password for {}.{}".format(gateway, gateway_userid))
                use_ssl = self.config.getboolean('SMTP', 'use_ssl', fallback=False)
                if use_ssl:
                    server = smtplib.SMTP_SSL(gateway, port=gateway_port)
                else:
                    server = smtplib.SMTP(gateway, port=gateway_port)
                server.set_debuglevel(self.config.getboolean('SMTP', 'debug', fallback=False))
                if gateway_userid is not None:
                    server.login(gateway_userid, gateway_password)

                results_of_send = server.send_message(message)
                self.log.debug("results_of_send = {}".format(results_of_send))

                for recipient in results_of_send:
                    self.log.warn("Problem sending to: {}".format(recipient))
            except smtplib.SMTPRecipientsRefused as e:
                self.log.critical("All recipients were refused.\n{}".format(e.recipients))
                if throw_exception:
                    raise NotifierException(e)
            except smtplib.SMTPHeloError as e:
                self.log.critical("The server didn't reply properly to the HELO greeting.\n{}".format(e))
                if throw_exception:
                    raise NotifierException(e)
            except smtplib.SMTPSenderRefused as e:
                self.log.critical("The server didn't accept the from_addr {}.\n{}".format(
                    message.get('Sender', None),
                    e
                ))
                if throw_exception:
                    raise NotifierException(e)
            except smtplib.SMTPDataError as e:
                self.log.critical(
                    "The server replied with an unexpected error code (other than a refusal of a recipient).\n{}".format(
                        e))
                if throw_exception:
                    raise NotifierException(e)
            finally:
                try:
                    if server is not None:
                        reply = server.quit()
                        self.log.debug('server quit reply = {}'.format(reply))
                        self.log.info('Mail sent')
                except Exception as e:
                    self.log.exception(e)
