import datetime, pytz, httplib2, json, sys, os

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models

from appts import get_therapist_appts, enter_appts_to_db



d = datetime.datetime.now()

today = d.replace(tzinfo=pytz.timezone('US/Pacific'))

tomorrow = today + datetime.timedelta(days=1)

# ids: Sarah = 5 Claire = 6
therapists = models.Therapist.query.filter(and_(models.Therapist.user.has(status='active'), models.Therapist.status=='active', models.Therapist.id == 5))


for t in therapists:
    print(t.user.first_name)
    appts = get_therapist_appts(t, today, tomorrow)
    print(len(appts))
    enter_appts_to_db(appts, t)
