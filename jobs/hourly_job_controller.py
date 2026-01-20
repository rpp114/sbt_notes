#!/home/ray/notes/notes/bin/python

import datetime, httplib2, json, sys, os

from datetime import datetime, UTC, timedelta
from zoneinfo import ZoneInfo

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_
from sqlalchemy.sql import func

# add system directory to pull in app & models


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from sbt_notes.app import create_app
app = create_app()

from sbt_notes.app import db
from sbt_notes.app import models
from sbt_notes.jobs.appts import enter_appts_to_db, move_appts, insert_auth_reminder
from sbt_notes.jobs.billing import build_appt_xml

from sbt_notes.jobs import emails



def get_new_appts():

    pdt = ZoneInfo("America/Los_Angeles")
    est = ZoneInfo("America/New_York")
    max_time = datetime.now(UTC).astimezone(pdt)
    #max_time = pdt.normalize(est.localize(datetime.datetime.now()))

    therapists = models.Therapist.query.filter(models.Therapist.status == 'active', models.Therapist.user.has(status = 'active')).all()

    min_times = dict(db.session\
                .query(models.ClientAppt.therapist_id,func.max(models.ClientAppt.end_datetime))\
                .join(models.Therapist).join(models.User)\
                .filter(models.Therapist.status == 'active', models.User.status == 'active')\
                .group_by(models.ClientAppt.therapist_id)\
                .all())
    
    last_meetings = dict(db.session.query(models.CompanyMeeting.company_id, func.max(models.CompanyMeeting.id)).group_by(models.CompanyMeeting.company_id).all())
    
    for i in min_times:
        min_times[i] = min_times[i].replace(tzinfo=pdt)
        
    for company in last_meetings:
        meeting = models.CompanyMeeting.query.get(last_meetings[company])
        for u in meeting.users:
            
            meeting_datetime = meeting.end_datetime.replace(tzinfo=UTC).astimezone(pdt)
            
            min_times[u.therapist.id] = max(meeting_datetime, min_times.get(u.therapist.id, max_time - timedelta(days=1)))

    for therapist in therapists:
        min_time = min_times.get(therapist.id, False)
        # print(therapist.user.first_name, min_time)
        
        if min_time:
            if min_time.tzinfo == None:
                min_time = min_time.replace(tzinfo=pdt)
        else:
             min_time = max_time - timedelta(days=1)
        # print(therapist.user)
        new_appts = enter_appts_to_db(therapist, min_time, max_time)
        # print('new appts:', len(new_appts))

        # messages = emails.get_appt_messages(new_appts)
        # emails.send_emails(therapist.user.email, messages)

        # print('Sent %s %s emails for appts from %s to %s' % (therapist.user.first_name, len(new_appts),min_time.strftime('%b %d, %Y %H:%M %p'), max_time.strftime('%b %d, %Y %H:%M %p')))


#execute jobs (No, Not Steve!!)
with app.app_context():
    get_new_appts()
