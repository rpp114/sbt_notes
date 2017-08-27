#!/home/titlow/notes.sarahbryantherapy.com/sbt_notes/notes/bin/python

import datetime, pytz, httplib2, json, sys, os

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_
from sqlalchemy.sql import func

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models

from appts import get_therapist_appts, enter_appts_to_db, move_appts

from billing import build_appt_xml

import emails



def get_new_appts():

    min_times = db.session\
                .query(models.ClientAppt.therapist_id,func.max(models.ClientAppt.end_datetime))\
                .join(models.Therapist).join(models.User)\
                .filter(models.Therapist.status == 'active', models.User.status == 'active')\
                .group_by(models.ClientAppt.therapist_id)\
                .all()

    d = datetime.datetime.now()

    max_time = d.replace(tzinfo=pytz.timezone('US/Pacific'))

    for t in min_times:
        min_time = t[1].replace(tzinfo=pytz.timezone('US/Pacific'))
        therapist = models.Therapist.query.get(t[0])

        appts = get_therapist_appts(therapist, min_time, max_time)
        new_appts = enter_appts_to_db(appts, therapist)
        messages = emails.get_appt_messages(new_appts)
        emails.send_emails(therapist.user.email, messages)


#execute jobs (No, Not Steve!!)

# get_new_appts()

d = datetime.datetime.now()

max_time = d.replace(tzinfo=pytz.timezone('US/Pacific')).replace(day=1) - datetime.timedelta(1)

min_date = max_time.replace(day=1)

f = models.Therapist.query.get(2)
t = models.Therapist.query.get(3)

appts = move_appts(f,t, 'Ray Test' )

# for a in appts:
#     print(a['id'])
#
# enter_appts_to_db(appts, t)
