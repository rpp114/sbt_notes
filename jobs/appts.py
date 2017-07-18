
import httplib2, json, sys, os

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db #, models


def get_therapist_appts(therapist, start_time, end_time):

    ''' Needs dates use standard datetime.datetime python format, and Therapist Object from the query return of models.Therapist'''

    credentials = client.OAuth2Credentials.from_json(json.loads(therapist.user.calendar_credentials))

    if credentials.access_token_expired:
        credentials.refresh(httplib2.Http())
        therapist.user.calendar_credentials = json.dumps(credentials.to_json())
        db.session.add(therapist)
        db.session.commit()


    http_auth = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http_auth)

    # calendar = service.calendars().get(calendarId='primary').execute()


    eventsResults = service.events().list(calendarId='primary', timeMin=start_time.isoformat(), timeMax=end_time.isoformat(), orderBy='startTime', singleEvents=True).execute()

    return eventsResults.get('items', [])


def enter_appts_to_db(appts, therapist):

    for appt in appts:
