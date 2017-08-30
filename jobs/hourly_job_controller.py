#!/home/titlow/notes.sarahbryantherapy.com/sbt_notes/notes/bin/python

import datetime, pytz, httplib2, json, sys, os

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_
from sqlalchemy.sql import func

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models

from appts import enter_appts_to_db, move_appts, insert_auth_reminder

from billing import build_appt_xml

import emails



def get_new_appts():

    min_times = db.session\
                .query(models.ClientAppt.therapist_id,func.max(models.ClientAppt.end_datetime))\
                .join(models.Therapist).join(models.User)\
                .filter(models.Therapist.status == 'active', models.User.status == 'active')\
                .group_by(models.ClientAppt.therapist_id)\
                .all()

    d = datetime.datetime.now() - datetime.timedelta(hours=3)

    max_time = d.replace(tzinfo=pytz.timezone('US/Pacific'))

    for t in min_times:
        min_time = t[1].replace(tzinfo=pytz.timezone('US/Pacific'))
        therapist = models.Therapist.query.get(t[0])

        new_appts = enter_appts_to_db(therapist, min_time, max_time)
        messages = emails.get_appt_messages(new_appts)
        emails.send_emails(therapist.user.email, messages)

    print('Finished importing emails at: ', d)


#execute jobs (No, Not Steve!!)

get_new_appts()

# d = datetime.datetime.now()
# #
# max_date = d.replace(tzinfo=pytz.timezone('US/Pacific')).replace(month=9, day=15)
#
# min_date = d.replace(tzinfo=pytz.timezone('US/Pacific')).replace(month=9, day=1)
# #
# sarah = models.Therapist.query.get(2)
# ray = models.Therapist.query.get(3)
#
#
# appts = get_therapist_appts(sarah, min_date, max_date)
#
# for a in appts:
#     print(a['location'])
# # #
# enter_appts_to_db(appts, t)