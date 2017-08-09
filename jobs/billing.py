import httplib2, json, sys, os, datetime

from apiclient import discovery
from oauth2client import client
from sqlalchemy import and_, func, between

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models



def gather_appts(regional_center, start_time, end_time):

    '''Takes regional_center object from query return from models.RegionalCenter or ClientAppt.client.regional_center and start and end date times'''

    appts = models.ClientAppt.query.filter(and_(models.ClientAppt.cancelled == 0, models.ClientAppt.billed == 0, between(models.ClientAppt.start_datetime,start_time, end_time), models.ClientAppt.client.has(regional_center_id = regional_center.id))).all()

    appts_by_client = {}


    for appt in appts:
        appts_by_client[appt.client.id] = appts_by_client.get(appt.client.id, [])
        appts_by_client[appt.client.id].append(appt)

    return appts_by_client


def bulid_appt_xml(appts):

    '''Takes the output obejct of gather_appts() and will write XML file to static directory.'''






start = datetime.datetime.today().replace(day=1)
end = datetime.datetime.today()


for r in models.RegionalCenter.query.all():
    print(gather_appts(r,start, end))
