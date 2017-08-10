import sys, os, datetime

from sqlalchemy import and_, func, between
from xml.etree.ElementTree import Element, SubElement, tostring

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models



def gather_appts(regional_center, start_time, end_time):

    '''Takes regional_center object from query return from models.RegionalCenter or ClientAppt.client.regional_center and start and end date times'''

    appts = models.ClientAppt.query.filter(and_(models.ClientAppt.cancelled == 0, models.ClientAppt.billed == 0, between(models.ClientAppt.start_datetime,start_time, end_time), models.ClientAppt.client.has(regional_center_id = regional_center.id))).all()

    return appts


def build_appt_xml(appts):

    '''Takes the output obejct of gather_appts() format:{'user_id':[appt[0], appt[1]]} and will write XML file to static docs directory.'''

    appts_by_client = {}

    for appt in appts:
        appts_by_client[appt.client.id] = appts_by_client.get(appt.client.id, {})
        appts_by_client[appt.client.id][appt.appt_type.name] = appts_by_client[appt.client.id].get(appt.appt_type.id, [])
        appts_by_client[appt.client.id][appt.appt_type.id].append(appt)
        appt_days.append(appt.start_datetime.day)

    print('appts_by_client', appts_by_client)



    tai = Element('TAI')

    for client_id in appts:
        appt_days = []
        # Grab Auth to check dates and Max Visits
        # If auth is not valid Skip appt writing and leave billed.
        # If More appts then Auth Max pop last appt and leave it off.
        client = models.Client.query.get(client_id)
        client_auths = client.auths
        current_month = appts[client_id][0].start_datetime.replace(day=1)
        for auth in client_auths:
            if current_month >= auth.auth_start_date and current_month <= auth.auth_end_date:
                current_auth = auth
            else:
                # Add note about Auth Needed
                continue
        current_auth = client_auths.filter(and_(current_month >= client.auths.auth_start_date, current_month <= client.auths.auth_end_date))

        for appt_type_id in appts[client_id]:
            appt_type = models.ApptType.query.get(appt_type_id)

            invoice_data = SubElement(tai, 'invoicedata')
            RecType = SubElement(invoice_data, 'RecType')
            RecType.text = 'D'
            RCID = SubElement(invoice_data, 'RCID')
            RCID.text = client.regional_center.rc_id
            ATTN = SubElement(invoice_data, 'AttnOnlyFlag')
            UCI = SubElement(invoice_data, 'UCI')
            UCI.text = client.uci_id
            lastname = SubElement(invoice_data, 'lastname')
            lastname.text = client.last_name.upper()
            firstname = SubElement(invoice_data, 'firstname')
            firstname.text = client.first_name.upper()
            auth_number = SubElement(invoice_data, 'AuthNumber')
            auth_number.text = current_auth.auth_id
            svc_code = SubElement(invoice_data, 'SVCCode')
            svc_code.text = appt_type.service_type_code
            svcs_code = SubElement(invoice_date, 'SVCSCode')
            svcs_code.text = appt_type.service_type_code
            

    print(tostring(tai))









start = datetime.datetime.today().replace(day=1)
end = datetime.datetime.today()


for r in models.RegionalCenter.query.filter(models.RegionalCenter.id<'3'):
    appts = gather_appts(r,start, end)
    # for appt in appts:
    #     print(appt.appt_type.name)
    build_appt_xml(appts)
