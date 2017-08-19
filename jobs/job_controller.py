import datetime, pytz, httplib2, json, sys, os

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_
from sqlalchemy.sql import func

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models

from appts import get_therapist_appts, enter_appts_to_db

from billing import build_appt_xml



def get_new_appts():

    min_times = db.session\
                .query(models.ClientAppt.therapist_id,func.max(models.ClientAppt.end_datetime))\
                .join(models.Therapist).join(models.User)\
                .filter(models.Therapist.status == 'active', models.User.status == 'active')\
                .group_by(models.ClientAppt.therapist_id)\
                .all()

    d = datetime.datetime.now()

    max_time = d.replace(tzinfo=pytz.timezone('US/Pacific'))

    # print(max_time)

    # appts = []

    for t in min_times:
        min_time = t[1].replace(tzinfo=pytz.timezone('US/Pacific'))
        therapist = models.Therapist.query.get(t[0])
        print('min_time: ', min_time)
        print('max_time: ', max_time)
        appts = get_therapist_appts(therapist, min_time, max_time)

    for appt in appts:
        print(appt['summary'])


# get_new_appts()

d = datetime.datetime.now()

max_time = d.replace(tzinfo=pytz.timezone('US/Pacific'))

max_time = max_time.replace(day=2)

min_time = max_time - datetime.timedelta(1)

t = models.Therapist.query.get(2)

appts = get_therapist_appts(t, min_time, max_time)

enter_appts_to_db(appts, t)


#
#
# for t in therapists:
#     raw_appts = get_therapist_appts(t, today, tomorrow)
#     for appt in raw_appts:
#         if 'source' in appt.get('description',''):
#             appts.append(appt)
#
#     # enter_appts_to_db(appts, t)
