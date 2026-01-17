#!/home/ray/notes/notes/bin/python

import datetime, pytz, sys, os
from client_processor import need_new_appts, archive_eval_clients

# add system directory to pull in app & models

# sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from sbt_notes.app import create_app
app = create_app()

from sbt_notes.app import db, Models

with app.app_context():
    need_new_appts()

    archive_eval_clients()
