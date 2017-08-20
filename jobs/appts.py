
import httplib2, json, sys, os, datetime, re

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_, func

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models


def get_therapist_appts(therapist, start_time, end_time):

    ''' Needs dates use standard datetime.datetime python format, and Therapist Object from the query return of models.Therapist'''

    credentials = client.OAuth2Credentials.from_json(json.loads(therapist.calendar_credentials))

    if credentials.access_token_expired:
        credentials.refresh(httplib2.Http())
        therapist.calendar_credentials = json.dumps(credentials.to_json())
        db.session.add(therapist)
        db.session.commit()


    http_auth = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http_auth)

    # calendar = service.calendars().get(calendarId='primary').execute()

    eventsResults = service.events().list(calendarId='primary', orderBy='startTime', singleEvents=True, q='source: ', timeMin=start_time.isoformat(), timeMax=end_time.isoformat()).execute()

    return eventsResults.get('items', [])


def enter_appts_to_db(appts, therapist):
    # What is this???  Why New Clients?
    new_appts = []

    for appt in appts:

        client = models.Client.query.filter(func.lower(func.concat(models.Client.first_name, ' ', models.Client.last_name)).like(appt['summary'].strip().lower())).first()

        rc_from_appt = re.match('source:\s\w+', appt['description']).group(0)[8:]

        if client == None:
            client_name = appt['summary'].strip().split()
            rc = models.RegionalCenter.query.filter(models.RegionalCenter.appt_reference_name == rc_from_appt).first()
            new_client = models.Client( first_name=client_name[0],last_name=' '.join(client_name[1:]), therapist=therapist, regional_center=rc)
            db.session.add(new_client)
            client = new_client

        if client.status != 'active':
            client.status = 'active'
            db.session.add(client)

        time_format = '%Y-%m-%dT%H:%M:%S'
        start_time = datetime.datetime.strptime(appt['start']['dateTime'][:-6], time_format)
        end_time = datetime.datetime.strptime(appt['end']['dateTime'][:-6], time_format)

        appointment_type='treatment' if ((end_time - start_time).seconds/60) == 60 else 'evaluation'


        appt_type_id = db.session.query(models.ApptType.id)\
                    .join(models.RegionalCenter)\
                    .filter(models.RegionalCenter.appt_reference_name == rc_from_appt,\
                            models.ApptType.name == appointment_type).first()[0]

        new_appt = models.ClientAppt(
            therapist=therapist,
            client=client,
            start_datetime=start_time,
            end_datetime=end_time,
            cancelled=1 if 'CNX' in appt['description'] else 0,
            # need to find appt_type_id for client from Regional Center
            appointment_type=appointment_type,
            appt_type_id=appt_type_id
        )
        db.session.add(new_appt)
        new_appts.append(new_appt)

    db.session.commit()

    return new_appts
