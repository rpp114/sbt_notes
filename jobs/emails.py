import sys, os, datetime, smtplib, urllib

from email.message import Message
from email.mime.text import MIMEText

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from secret_info import EMAIL_CONFIG
from app import db, models



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

        html = '''<html><head></head><body>
        <a href="http://notes.sarahbryantherapy.com/client/note?appt_id=%s">%s</a><br/>
        </body></html>''' % (appt.id, subject)
        message = MIMEText(html, 'html')
        message['Subject'] = subject
        messages.append(message)

    return messages

def send_service_start_alert(client, appt_datetime):

    '''Takes a client and appt_datetime that has no appt history
        and sends an email to company admins about start of service date.
        Including Service Coordinator Info and start date.'''

    subject = 'Service Start Date for {} {}'.format(client.first_name, client.last_name)

    html = '''<html><head></head><body>
    <p>Contact {} {} @ {}</p>
    <table>
    <tr><td>Client Name:</td><td>{} {}</td></tr>
    <tr><td>Start Date:</td><td>{}</td></tr>
    <tr><td>Therapist:</td><td>{} {}</td></tr>
    </table>
    </body></html>'''.format(client.case_worker.first_name, client.case_worker.last_name,
                             client.case_worker.email,
                             client.first_name, client.last_name,
                             appt_datetime.strftime('%B %d, %Y'),
                             client.therapist.user.first_name, client.therapist.user.last_name
                             )

    message = MIMEText(html, 'html')
    message['Subject'] = subject

    admins = [a.email for a in client.therapist.company.users.filter(models.User.status == 'active', models.User.role_id == 2).all()]
    to_emails = ', '.join(admins)

    send_emails(to_emails, [message])
