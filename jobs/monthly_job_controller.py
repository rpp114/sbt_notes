#!/home/ray/notes/notes/bin/python

import datetime, pytz, sys, os
from client_processor import need_new_appts, archive_eval_clients

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models

need_new_appts()

# archive_eval_clients()
