import base64, json

from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sqlalchemy import select, func
# from flask_login import current_user

from sbt_notes.app import db, models


def get_gmail_service(current_user):
    # creds = Credentials(**session['credentials'])
    data = json.loads(json.loads(current_user.therapist.calendar_credentials))

    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )
    
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        current_user.therapist.calendar_credentials = json.dumps(creds.to_json())
        db.session.add(current_user)
        db.session.commit()
        print(f'Refreshed Creds')
    
    return build('gmail', 'v1', credentials=creds)

def create_message(email_message):
    message = MIMEText(email_message['body'])
    message['to'] = email_message['to_email']
    message['subject'] = email_message['subject']

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_email_message(to_user, email_type=None, current_user=None):

    service = get_gmail_service(current_user)
    
    email_types = {
        'auth_reminder': auth_reminder_email(to_user, current_user)
                   }
    
    message = email_types[email_type]
    
    encoded_message = create_message(message)
    
    sent = service.users().messages().send(
        userId='me',
        body=encoded_message
    ).execute()

    return message
    # return message

def auth_reminder_email(case_worker, current_user):
    query = (
       			db.session.query(models.ClientAppt)
    			.filter(
						models.ClientAppt.cancelled == 0,			
						models.ClientAppt.billing_xml_id == None,
						models.ClientAppt.client.has(models.Client.case_worker_id == case_worker.id)
					).order_by(models.ClientAppt.start_datetime)
				)
    appts_needing_auth = query.all()
    
    email_appts = ['\n'.join(
        [appt.client.full_name, 
         f'UCI#: {appt.client.uci_id}', 
         f'Appt Type: {appt.appointment_type.capitalize()}',
         f'Appt Date: {appt.start_datetime.strftime('%m/%d/%Y')}']) for appt in appts_needing_auth]
    
    message = {
        'to_email': 'ray@sarahbryantherapy.com', #case_worker.email,
        'subject' : 'POS Status Update Request',
        'body': f'Hey {case_worker.first_name},\n\nI just wanted to check on the status of the following POS\'s:\n\n{'\n\n'.join(email_appts)}\n\nThanks\n\n{current_user.therapist.signature}'
    }
    
    return message