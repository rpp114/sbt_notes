#!/home/ray/notes/notes/bin/python

import datetime, sys, os

# add system directory to pull in app & models

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from sbt_notes.app import create_app

from sbt_notes.jobs.mileage import add_mileage

end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=3)

app = create_app()

with app.app_context():
    mileage_appts = add_mileage(start_date, end_date)

# print('Added mileage to {} appts'.format(len(mileage_appts)))
