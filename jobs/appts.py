
import datetime, pytz, httplib2, json, sys, os

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models


def get_therapist_appts():

    therapists = models.Therapist.query.filter(and_(models.Therapist.user.has(status='active'), models.Therapist.status=='active'))

    for therapist in therapists:
        credentials = client.OAuth2Credentials.from_json(therapist.user.calendar_credetials)

    return 'I\'m Done'




therapists = get_therapist_appts()

print(therapists)

    # therapist_creds = json.loads(therapist[2])
    #
    # print(therapist[0], credentials.access_token_expired)

    # print(girl[0], girl[1],tokens)
