
import datetime, pytz, httplib2, json

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_

from app import db, models


def get_therapists():

    therapists = [(t.user.first_name, t.user.last_name, t.user.calendar_credentials) for t in models.Therapist.query.filter(and_(models.Therapist.user.has(status='active'), models.Therapist.status=='active'))]

    return therapists




girls = get_therapists()

for girl in girls:
    credentials = client.OAuth2Credentials.from_json(json.loads(girls[2]))

    print(credentials)

    # print(girl[0], girl[1],tokens)
