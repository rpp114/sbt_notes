
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
            appointment_type=appointment_type,
            appt_type_id=appt_type_id
        )
        db.session.add(new_appt)
        new_appts.append(new_appt)

    db.session.commit()

    return new_appts



def move_appts(from_therapist, to_therapist, client_name):

    '''Moves the appointments of a client from one therapist to another.'''


    from_credentials = client.OAuth2Credentials.from_json(json.loads(from_therapist.calendar_credentials))

    if from_credentials.access_token_expired:
        from_credentials.refresh(httplib2.Http())
        from_therapist.calendar_credentials = json.dumps(from_credentials.to_json())
        db.session.add(from_therapist)
        db.session.commit()

    to_credentials = client.OAuth2Credentials.from_json(json.loads(to_therapist.calendar_credentials))

    if to_credentials.access_token_expired:
        to_credentials.refresh(httplib2.Http())
        to_therapist.calendar_credentials = json.dumps(to_credentials.to_json())
        db.session.add(to_therapist)
        db.session.commit()


    from_http_auth = from_credentials.authorize(httplib2.Http())
    from_service = discovery.build('calendar', 'v3', http=from_http_auth)

    to_http_auth = to_credentials.authorize(httplib2.Http())
    to_service = discovery.build('calendar', 'v3', http=to_http_auth)

    eventsResults = from_service.events().list(calendarId='primary', q=client_name).execute()

    events = eventsResults.get('items', [])

    to_calendar = to_service.calendarList().list().execute()
    from_calendar = from_service.calendarList().list().execute()

    for i in from_calendar['items']:
        if i.get('primary', False):
            from_user = i['id']
    for i in to_calendar['items']:
        if i.get('primary', False):
            write_calendar = i['id']

    rule = {'scope':{'type': 'user', 'value': from_user}, 'role': 'writer'}

    acl_rule = to_service.acl().insert(calendarId='primary', body=rule).execute()

    print(acl_rule['id'])

    for event in events:
        # print(event['id'], event['summary'])
        moved_event = from_service.events().move(calendarId='primary', eventId=event['id'], destination=write_calendar).execute()
        # print('moved_event: ', moved_event)




    return events
