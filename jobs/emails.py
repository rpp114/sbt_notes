
import sys, os, datetime, smtplib

from email.message import Message
from email.mime.text import MIMEText

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from secret_info import EMAIL_CONFIG



def send_emails(to_email, messages, from_email=EMAIL_CONFIG['username']):

    '''Defauls to send from notes@sbt.com.  Takes a to email and an array of messages'''

    user = EMAIL_CONFIG['username']
    password = EMAIL_CONFIG['password']
    server = EMAIL_CONFIG['server']
    port = EMAIL_CONFIG['port']

    server = smtplib.SMTP_SSL(server, port)

    server_response = server.ehlo()

    if server_response[0] == 250:
        server.login(user, password)
        for message in messages:
            message['From'] = from_email
            message['To'] = to_email
            server.sendmail(from_email, to_email, message.as_string())

    server.quit()


def get_appt_messages(appts):

    messages = []

    for appt in appts:
        if appt.cancelled == 1:
            continue

        subject = 'Notes Needed for: %s %s on %s at %s' % (appt.client.first_name, appt.client.last_name, appt.start_datetime.strftime('%b %d, %Y'), appt.start_datetime.strftime('%-I:%M %p'))

        html = '''<html><head></head><body><a href="http://notes.sarahbryantherapy.com/client/note?appt_id=%s">%s</a><br/>
        <form action="http://notes.sarahbyrantherapy.com/client/note?appt_id=%s" method="post">
        <input type="text" name="notes">
        <input type="submit" value="Press Me Please">
        </form>
        </body></html>''' % (appt.id, subject, appt.id)
        message = MIMEText(html, 'html')
        message['Subject'] = subject
        messages.append(message)

    return messages









# send_emails('rpputt@hotmail.com', ['hello'])
