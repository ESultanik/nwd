from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import getpass
import os
import socket
import sys
import time

import keyring

from .notify import Notifier

KEYRING_NAME='NotifyWhenDone'

def prompt(message, yes_options = ('y', 'yes'), no_options = ('n', 'no'), default=True):
    if default:
        yes_options = yes_options + ('',)
    else:
        no_options = no_options + ('',)
    while True:
        ret = input(message).strip().lower()
        if ret in yes_options:
            return True
        elif ret in no_options:
            return False

def save_email_credentials(sender_name, sender_email, sender_password, smtp_server, smtp_port=587):
    keyring.set_password(KEYRING_NAME, 'sender_name', sender_name)
    keyring.set_password(KEYRING_NAME, 'sender_email', sender_email)
    keyring.set_password(KEYRING_NAME, 'sender_password', sender_password)
    keyring.set_password(KEYRING_NAME, 'smtp_server', smtp_server)
    keyring.set_password(KEYRING_NAME, 'smtp_port', str(smtp_port))

def prompt_for_email_credentials(sender_name=None, sender_email=None, sender_password=None, smtp_server=None, smtp_port=None):
    if sender_name is None:
        sender_name = keyring.get_password(KEYRING_NAME, 'sender_name')
    if sender_name is None:
        sender_name = getpass.getuser()
    new_sender_name = input(f"Sender Name: [{sender_name}] ")
    if new_sender_name == '':
        new_sender_name = sender_name

    if sender_email is None:
        sender_email = keyring.get_password(KEYRING_NAME, 'sender_email')
    while True:
        if sender_email is None:
            new_sender_email = input('Sender E-Mail: ')
        else:
            new_sender_email = input(f"Sender E-Mail: [{sender_email}] ")
            if new_sender_email == '':
                new_sender_email = sender_email
        if '@' in new_sender_email:
            break

    if sender_password is None:
        sender_password = keyring.get_password(KEYRING_NAME, 'sender_password')
    if sender_password is not None and new_sender_email == sender_email:
        if prompt(f"Would you like to update the password for {new_sender_email}? [yN] ", default=False):
            change_password = True
        else:
            change_password = False
            new_sender_password = sender_password
    else:
        change_password = True
    if change_password:
        new_sender_password = getpass.getpass(f"Password for {new_sender_email}: ")

    normalized_email = new_sender_email.strip().lower()
    if smtp_server is None:
        if normalized_email.endswith('@gmail.com'):
            smtp_server = 'smtp.gmail.com'
        elif normalized_email.endswith('@hotmail.com') or normalized_email.endswith('@live.com') or normalized_email.endswith('@outlook.com'):
            smtp_server = 'smtp-mail.outlook.com'
        else:
            smtp_server = keyring.get_password(KEYRING_NAME, 'smtp_server')
            if smtp_server is None:
                smtp_server = f"mail.{normalized_email[normalized_email.find('@')+1:]}"
    new_smtp_server = input(f"SMTP Server: [{smtp_server}] ")
    if new_smtp_server == '':
        new_smtp_server = smtp_server
    if new_smtp_server == 'smtp.gmail.com':
        sys.stderr.write('Note: If you have two factor authentication enabled on your Gmail account, you may need to set up an app password for NWD at https://security.google.com/settings/security/apppasswords\n')

    if smtp_port is None:
        smtp_port = keyring.get_password(KEYRING_NAME, 'smtp_port')
    if smtp_port is None:
        smtp_port = '587'
    new_smtp_port = input(f"SMTP Port: [{smtp_port}] ")
    if new_smtp_port == '':
        new_smtp_port = smtp_port

    return new_sender_name, new_sender_email, new_sender_password, new_smtp_server, int(new_smtp_port)

def prompt_and_save_email_credentials(*args, **kwargs):
    prev_creds = get_keychain_credentials()
    creds = prompt_for_email_credentials(*args, **kwargs)
    if creds[1] is None:
        raise Exception('Error loading e-mail credentials!')
    if prev_creds != creds and prompt('Save these e-mail credentials to the system keychain? [Yn] '):
        save_email_credentials(*creds)
    return creds

def get_keychain_credentials():
    sender_email = keyring.get_password(KEYRING_NAME, 'sender_email')
    sender_name = keyring.get_password(KEYRING_NAME, 'sender_name')
    sender_password = keyring.get_password(KEYRING_NAME, 'sender_password')
    smtp_server = keyring.get_password(KEYRING_NAME, 'smtp_server')
    smtp_port = keyring.get_password(KEYRING_NAME, 'smtp_port')
    if smtp_port is None:
        smtp_port = 587
    else:
        smtp_port = int(smtp_port)
    return sender_name, sender_email, sender_password, smtp_server, smtp_port    

def get_email_credentials(*args, **kwargs):
    creds = get_keychain_credentials()
    if creds[1] is None:
        return prompt_and_save_email_credentials(*args, **kwargs)
    else:
        return creds

def get_default_recipient():
    return keyring.get_password(KEYRING_NAME, 'default_recipient')

def save_default_recipient(recipient_email):
    keyring.set_password(KEYRING_NAME, 'default_recipient', recipient_email)

def get_recipient(default_recipient=None):
    default = get_default_recipient()
    if default is None:
        default = default_recipient
    while True:
        if default is None:
            recipient = input('E-Mail Address to Notify: ')
        else:
            recipient = input(f"E-Mail Address to Notify: [{default}] ")
            if recipient == '':
                recipient = default
        if '@' in recipient:
            break
    if recipient != default:
        if prompt(f"Would you like to make {recipient} the default notification recipient? [Yn] "):
            save_default_recipient(recipient)
    return recipient

class EmailNotifier(Notifier):
    def __init__(self, sender_name=None, sender_email=None, sender_password=None, smtp_server=None, smtp_port=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender_name, self.sender_email, self.sender_password, self.smtp_server, self.smtp_port = get_email_credentials(sender_name, sender_email, sender_password, smtp_server, smtp_port)
        self.to_email = get_recipient(self.sender_email)

    def notify(self):
        # Need to import smtplib here, otherwise it will segfault if we import it before the fork()
        import smtplib
        msg = MIMEMultipart()
        msg['Subject'] = f"NWD: {self.name} finished!"
        msg['From'] = f"{self.sender_name} <{self.sender_email}>"
        msg['To'] = self.to_email
        if self.stdout or self.stderr:
            attachment_msg = '\n\nProgram output logs are attached.'
        else:
            attachment_msg = ''
        msg.attach(MIMEText(f"Process {self.pid} on {socket.gethostname()} finished at {time.ctime(self.end_time)}.\n\n`{' '.join(self.commandline)}`{attachment_msg}."))

        for logstream, name, mirror_to in ((self.stdout, 'stdout.txt'), (self.stderr, 'stderr.txt')):
            if logstream is not None:
                with open(logstream.name, "rb") as f:
                    part = MIMEApplication(
                        f.read(),
                        Name=name
                    )
                try:
                    os.unlink(logstream.name)
                except Exception as e:
                    print(e)
                part['Content-Disposition'] = f"attachment; filename=\"{name}\""
                msg.attach(part)

        server = smtplib.SMTP(f"{self.smtp_server}:{self.smtp_port}")
        server.starttls()
        server.login(self.sender_email, self.sender_password)
        server.sendmail(self.sender_email,
                        [self.to_email],
                        msg.as_string())
        server.quit()
