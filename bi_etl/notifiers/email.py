import smtplib
from email.mime.text import MIMEText

from bi_etl.notifiers.notifier import Notifier


class Email(Notifier):
    def __init__(self, config, destination_definition):
        super().__init__(config=config, destination_definition=destination_definition)

    def send(self, subject, message):
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
            try:
                from_address = self.config.get('SMTP', 'from')
                gateway = self.config.get_or_default('SMTP', 'gateway','')
                server = smtplib.SMTP(gateway)
                server.set_debuglevel(self.config.getboolean_or_default('SMTP', 'debug', False))
                if isinstance(message, MIMEText):
                    contents = message.as_string()
                else:
                    msg = MIMEText(message)
                    msg['Subject'] = subject
                    msg['To'] = to_addresses

                results_of_send = server.sendmail(from_address, to_addresses, contents)
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
