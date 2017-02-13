import email
import smtplib
from email.mime.text import MIMEText

from bi_etl.notifiers.notifier import Notifier


class Email(Notifier):
    def __init__(self, config, destination_definition):
        super().__init__(config=config,
                         destination_definition=destination_definition)

    def send(self, message, subject=None):
        # Send e-mail via SMTP
        if len(self.destination_definition) > 0:
            to_addresses = list()
            if isinstance(self.destination_definition, str):
                for addr in self.destination_definition.split(','):
                    addr = addr.strip()
                    self.log.info('Adding {} to send list'.format(addr))
                    to_addresses.append(addr)
            else:
                for addr in self.destination_definition:
                    addr = addr.strip()
                    to_addresses.append(addr)

            server = None
            contents = None
            try:
                from_address = self.config.get('SMTP', 'from')
                gateway = self.config.get('SMTP', 'gateway')
                gateway_port = self.config.getint_or_default('SMTP', 'gateway_port', 0)
                gateway_userid = self.config.get_or_default('SMTP', 'gateway_userid', None)
                gateway_password = self.config.get_or_default('SMTP', 'gateway_password', None)
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
                use_ssl = self.config.getboolean_or_default('SMTP', 'use_ssl', False)
                if use_ssl:
                    server = smtplib.SMTP_SSL(gateway, port=gateway_port)
                else:
                    server = smtplib.SMTP(gateway, port=gateway_port)
                server.set_debuglevel(self.config.getboolean_or_default('SMTP', 'debug', False))
                if gateway_userid is not None:
                    server.login(gateway_userid, gateway_password)
                if isinstance(message, email.message.Message):
                    if subject is not None:
                        message['subject'] = subject
                else:
                    message = MIMEText(message)
                    if subject is not None:
                        message['subject'] = subject
                message['Sender'] = from_address
                message['To'] = ','.join(to_addresses)

                results_of_send = server.send_message(message, to_addrs=to_addresses)
                self.log.debug("results_of_send = {}".format(results_of_send))

                for recipient in results_of_send:
                    self.log.warn("Problem sending to: {}".format(recipient))
            except smtplib.SMTPRecipientsRefused as e:
                self.log.critical("All recipients were refused.\n{}".format(e.recipients))
            except smtplib.SMTPHeloError as e:
                self.log.critical("The server didn't reply properly to the HELO greeting.\n{}".format(e))
            except smtplib.SMTPSenderRefused as e:
                self.log.critical("The server didn't accept the from_addr.\n{}".format(e))
            except smtplib.SMTPDataError as e:
                self.log.critical(
                    "The server replied with an unexpected error code (other than a refusal of a recipient).\n{}".format(
                        e))
            finally:
                try:
                    if server is not None:
                        reply = server.quit()
                        self.log.debug('server quit reply = {}'.format(reply))
                        self.log.info('Mail sent')
                except Exception as e:
                    self.log.exception(e)
