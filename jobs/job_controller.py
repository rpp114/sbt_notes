import datetime, pytz, httplib2, json, sys, os

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models

from appts import get_therapist_appts, enter_appts_to_db

from billing import build_appt_xml


d = datetime.datetime.now()
today = d.replace(tzinfo=pytz.timezone('US/Pacific'))



tomorrow = today + datetime.timedelta(days=1)

today = today.replace(day=1, month=7)

therapists = models.Therapist.query.filter(and_(models.Therapist.user.has(status='active'), models.Therapist.status=='active'))

appts = []

for t in therapists:
    raw_appts = get_therapist_appts(t, today, tomorrow)
    for appt in raw_appts:
        if 'source' in appt.get('description',''):
            appts.append(appt)

    enter_appts_to_db(appts, t)
