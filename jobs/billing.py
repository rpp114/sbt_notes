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

    '''Takes an array of Appt Objects and will write XML file to static docs directory.'''
    appts_by_client = {}

    for appt in appts:
        appts_by_client[appt.client.id] = appts_by_client.get(appt.client.id, {})
        appts_by_client[appt.client.id][appt.appt_type.id] = appts_by_client[appt.client.id].get(appt.appt_type.id, [])
        appts_by_client[appt.client.id][appt.appt_type.id].append(appt)

    tai = Element('TAI')

    for client_id in appts_by_client:
        # Grab Auth to check dates and Max Visits
        # If auth is not valid Skip appt writing and leave billed.
        # If More appts then Auth Max pop last appt and leave it off.
        client = models.Client.query.get(client_id)
        client_auths = client.auths
        current_month = appts[0].start_datetime.replace(day=1)
        current_auth = None
        for auth in client_auths:
            if current_month >= auth.auth_start_date and current_month <= auth.auth_end_date:
                current_auth = auth

        if current_auth == None:
            continue

        for appt_type_id in appts_by_client[client_id]:
            appt_type = models.ApptType.query.get(appt_type_id)
            appt_days = [d.start_datetime.day for d in appts_by_client[client_id][appt_type_id]]

            invoice_data = SubElement(tai, 'invoicedata')

            RecType = SubElement(invoice_data, 'RecType')
            RecType.text = 'D'
            RCID = SubElement(invoice_data, 'RCID')
            RCID.text = str(client.regional_center.rc_id)
            ATTN = SubElement(invoice_data, 'AttnOnlyFlag')
            UCI = SubElement(invoice_data, 'UCI')
            UCI.text = str(client.uci_id)
            lastname = SubElement(invoice_data, 'lastname')
            lastname.text = client.last_name.upper()
            firstname = SubElement(invoice_data, 'firstname')
            firstname.text = client.first_name.upper()
            auth_number = SubElement(invoice_data, 'AuthNumber')
            auth_number.text = str(current_auth.auth_id)
            svc_code = SubElement(invoice_data, 'SVCCode')
            svc_code.text = appt_type.service_type_code
            svcs_code = SubElement(invoice_data, 'SVCSCode')
            svcs_code.text = appt_type.service_type_code
            svc_mn_yr = SubElement(invoice_data, 'SVCMnYr')
            svc_mn_yr.text = current_month.strftime('%Y-%m-%d')
            industry_type = SubElement(invoice_data, 'IndustryType')
            wage_amt = SubElement(invoice_data, 'WageAmt')
            wage_type = SubElement(invoice_data, 'WageType')

            print(appt_days)

    # print(tostring(tai, encoding='utf8', method='xml'))









start = datetime.datetime.today().replace(day=1)
end = datetime.datetime.today()


for r in models.RegionalCenter.query.filter(models.RegionalCenter.id<'3'):
    appts = gather_appts(r,start, end)
    # for appt in appts:
    #     print(appt.appt_type.name)
    build_appt_xml(appts)
