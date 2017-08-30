
import httplib2, json, sys, os, datetime, re, copy, pytz, calendar

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_, func

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models

def get_calendar_credentials(therapist):

    '''Takes a therapist object refreshes token if needed and returns access to the calendar'''

    credentials = client.OAuth2Credentials.from_json(json.loads(therapist.calendar_credentials))

    if credentials.access_token_expired:
        credentials.refresh(httplib2.Http())
        therapist.calendar_credentials = json.dumps(credentials.to_json())
        db.session.add(therapist)
        db.session.commit()

    http_auth = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http_auth)

    return service


def enter_appts_to_db(therapist, start_time, end_time):
    ''' Needs dates use standard datetime.datetime python format, and Therapist Object from the query return of models.Therapist'''

    service = get_calendar_credentials(therapist)

    # calendar = service.calendars().get(calendarId='primary').execute()

    eventsResults = service.events().list(calendarId='primary', orderBy='startTime', singleEvents=True, q='source: ', timeMin=start_time.isoformat(), timeMax=end_time.isoformat()).execute()

    appts = eventsResults.get('items', [])

    new_appts = []

    for appt in appts:

        client = models.Client.query.filter(func.lower(func.concat(models.Client.first_name, ' ', models.Client.last_name)).like(appt['summary'].strip().lower())).first()

        rc_from_appt = re.match('source:\s\w+', appt['description']).group(0)[8:]

        if client == None:
            client_name = appt['summary'].strip().split()
            rc = models.RegionalCenter.query.filter(models.RegionalCenter.appt_reference_name == rc_from_appt).first()
            # parse address for input
            new_client = models.Client( first_name=client_name[0],last_name=' '.join(client_name[1:]), therapist=therapist, regional_center=rc)
            db.session.add(new_client)
            client = new_client

        if client.status != 'active':
            client.status = 'active'
            db.session.add(client)

        if client.therapist != therapist:
            client.therapist = therapist
            db.session.add(client)

        client_address = client.address + ' ' + client.city + ', ' + client.state + ' ' + client.zipcode

        # if client.address and appt['location'] != client_address:
        #     appt['location'] = client_address
        #     service.events().update(calendarId='primary', eventId=appt['id'], body=appt).execute()

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





def move_appts(from_therapist, to_therapist, client_name, from_date='', to_date=''):

    '''Takes two Therapist Objects, a string client name and to and from Python DateTimes and moves the appointments of a client from one therapist to another.'''

    from_service = get_calendar_credentials(from_therapist)

    to_service = get_calendar_credentials(to_therapist)

    if not from_date:
        from_date = datetime.datetime.now().replace(tzinfo=pytz.timezone('US/Pacific'))

    from_date_iso = from_date.isoformat()

    if to_date:
        to_date_iso = to_date.isoformat()
        eventsResults = from_service.events().list(calendarId='primary', q=client_name, timeMin=from_date_iso, timeMax=to_date_iso).execute()
    else:
        eventsResults = from_service.events().list(calendarId='primary', q=client_name, timeMin=from_date_iso).execute()

    events = eventsResults['items']

    to_calendar = to_service.calendars().get(calendarId='primary').execute()
    from_calendar = from_service.calendars().get(calendarId='primary').execute()

    from_user = from_calendar['id']
    write_calendar = to_calendar['id']

    has_acl = False
    acl_rules = to_service.acl().list(calendarId='primary').execute()

    for acl_rule in acl_rules['items']:
        if acl_rule['id'] == 'user:%s' % from_user:
            has_acl = True
            break

    if not has_acl:
        rule = {'scope':{'type': 'user', 'value': from_user}, 'role': 'writer'}
        acl_rule = to_service.acl().insert(calendarId='primary', body=rule).execute()

    for event in events:
        if event.get('recurrence', False):

            time_format = '%Y-%m-%dT%H:%M:%S'
            event_start_time = datetime.datetime.strptime(event['start']['dateTime'][:-6], time_format)
            event_end_time = datetime.datetime.strptime(event['end']['dateTime'][:-6], time_format)
            timezone_info = event['start']['dateTime'][-6:]

        # Create a appointment series with the start date at From and add a recurrence if there is a end date

            event_dow = event_start_time.weekday()

            if from_date > event_start_time:
                to_event_start_time = event_start_time.replace(year=from_date.year, month=from_date.month, day=from_date.day)
                to_event_end_time = event_end_time.replace(year=from_date.year, month=from_date.month, day=from_date.day)
            else:
                to_event_start_time = event_start_time
                to_event_end_time = event_end_time

            while to_event_start_time.weekday() != event_dow:
                to_event_start_time += datetime.timedelta(1)
                to_event_end_time += datetime.timedelta(1)

            to_event = copy.deepcopy(event)

            to_event.pop('id')
            to_event.pop('htmlLink')
            to_event.pop('etag')
            to_event.pop('iCalUID')
            to_event['summary'] = 'I\'m the to Ray Test event'
            to_event['start']['dateTime'] = to_event_start_time.isoformat() + timezone_info
            to_event['end']['dateTime'] = to_event_end_time.isoformat() + timezone_info

            if to_date:
                for i, recurr in enumerate(to_event['recurrence']):
                    if recurr[:5] == 'RRULE':
                        recur_split = recurr.split(';')
                        has_until = False
                        for j, recur_filter in enumerate(recur_split):
                            if recur_filter[:5] == 'UNTIL':
                                recur_split[j] = 'UNTIL=%s' % to_date.strftime('%Y%m%d')
                                has_until = True

                        to_event['recurrence'][i] = ';'.join(recur_split)
                        if not has_until:
                            to_event['recurrence'][i] += ';UNTIL=%s' % to_date.strftime('%Y%m%d')

        # Create a new appointment series after the to date if needed
            if to_date:
                new_event = copy.deepcopy(event)

                new_event_start_time  = event_start_time.replace(year=to_date.year, month=to_date.month, day=to_date.day)
                new_event_end_time  = event_end_time.replace(year=to_date.year, month=to_date.month, day=to_date.day)

                while new_event_start_time.weekday() != event_dow:
                    new_event_start_time += datetime.timedelta(1)
                    new_event_end_time += datetime.timedelta(1)

                new_event.pop('id')
                new_event.pop('htmlLink')
                new_event.pop('etag')
                new_event.pop('iCalUID')
                new_event['summary'] = 'I\'m the new Ray Test event'
                new_event['start']['dateTime'] = new_event_start_time.isoformat() + timezone_info
                new_event['end']['dateTime'] = new_event_end_time.isoformat() + timezone_info


        # Adjust the current event to end on the From change date
            for i, recurr in enumerate(event['recurrence']):
                if recurr[:5] == 'RRULE':
                    recur_split = recurr.split(';')
                    has_until = False
                    for j, recur_filter in enumerate(recur_split):
                        if recur_filter[:5] == 'UNTIL':
                            recur_split[j] = 'UNTIL=%s' % from_date.strftime('%Y%m%d')
                            has_until = True
                            event['recurrence'][i] = ';'.join(recur_split)
                            if not has_until:
                                event['recurrence'][i] += ';UNTIL=%s' % from_date.strftime('%Y%m%d')


        # Add all the apointments into the respective calendars
            adjust_current_event = from_service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
            insert_to_event = to_service.events().insert(calendarId='primary', body=to_event).execute()

            if to_date:
                insert_new_event = from_service.events().insert(calendarId='primary', body=new_event).execute()
        else:
            # Just move the single appointments Don't have to worry about duplicating and building new ones.  Easy!
            from_service.events().move(calendarId='primary', eventId=event['id'], destination=write_calendar).execute()


def insert_auth_reminder(auth):

    '''Takes a new auth and inserts a recurring note on mondays in the month of expiration'''

    service = get_calendar_credentials(auth.client.therapist)

    client_name = ' '.join([auth.client.first_name, auth.client.last_name])

    auth_event_date = auth.auth_end_date.replace(day=1, hour=00, tzinfo=pytz.timezone('US/Pacific'))

    while auth_event_date.weekday() != 0:
        auth_event_date += datetime.timedelta(1)

    eventResults = service.events().list(calendarId='primary', q=client_name, timeMin=auth_event_date.isoformat(), timeMax=(auth_event_date + datetime.timedelta(1)).isoformat()).execute()

    auth_exists = False

    for event in eventResults['items']:
        if 'Auth' in event['summary']:
            auth_exists = True

    if not auth_exists:
        auth_event = {}

        auth_event['start'] = {'date': auth_event_date.strftime('%Y-%m-%d')}
        auth_event['end'] = {'date': (auth_event_date + datetime.timedelta(1)).strftime('%Y-%m-%d')}
        auth_event['summary'] = 'Auth Expires for %s' % client_name
        eom_day = calendar.monthrange(auth_event_date.year, auth_event_date.month)[1]
        auth_event['recurrence'] = ['RRULE:FREQ=WEEKLY;UNTIL=%s;BYDAY=MO' % auth_event_date.replace(day=eom_day).strftime('%Y%m%d')]

        insert_auth_event = service.events().insert(calendarId='primary', body=auth_event).execute()
