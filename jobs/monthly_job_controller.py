
#!/home/ray/notes/notes/bin/python3.5

import datetime, pytz, sys, os

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models

def need_new_appts():

    pdt = pytz.timezone('America/Los_Angeles')

    today = pdt.localize(datetime.datetime.now())

    auths_need_appts = models.ClientAuth.query.filter(models.ClientAuth.status == 'active', models.ClientAuth.monthly_visits <= 2, models.ClientAuth.is_eval_only == 0, models.ClientAuth.auth_start_date <= today, models.ClientAuth.auth_end_date >= today, models.ClientAuth.client.has(status = 'active')).all()

    for auth in auths_need_appts:
        client = auth.client
        client.needs_appt_scheduled = 1
        db.session.add(client)

    db.session.commit()

#    print('need appts for {} clients'.format(len(auths_need_appts)))

need_new_appts()
