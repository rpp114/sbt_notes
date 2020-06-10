#!/home/ray/notes/notes/bin/python

import datetime, sys, os

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
from app import app

from mileage import add_mileage

end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=3)

with app.app_context():
    mileage_appts = add_mileage(start_date, end_date)

# print('Added mileage to {} appts'.format(len(mileage_appts)))
