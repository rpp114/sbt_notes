import sys, os, datetime, calendar, json

from sqlalchemy import and_, func, between

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models
