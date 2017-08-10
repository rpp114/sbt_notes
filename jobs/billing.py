import sys, os, datetime

from sqlalchemy import and_, func, between
from xml.etree.ElementTree import Element, SubElement, tostring

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models



def gather_appts(regional_center, start_time, end_time):

    '''Takes regional_center object from query return from models.RegionalCenter or ClientAppt.client.regional_center and start and end date times'''

    appts = models.ClientAppt.query.filter(and_(models.ClientAppt.cancelled == 0, models.ClientAppt.billing_xml_id == None, between(models.ClientAppt.start_datetime,start_time, end_time), models.ClientAppt.client.has(regional_center_id = regional_center.id))).all()
    return appts


def build_appt_xml(appts):

    '''Takes an array of Appt Objects and will write XML file to static docs directory.'''
    appts_by_client = {}

    for appt in appts:
        appts_by_client[appt.client.id] = appts_by_client.get(appt.client.id, {})
        appts_by_client[appt.client.id][appt.appt_type.id] = appts_by_client[appt.client.id].get(appt.appt_type.id, [])
        appts_by_client[appt.client.id][appt.appt_type.id].append(appt)


    tai = Element('TAI')
    current_month = appts[0].start_datetime.replace(day=1)
    xml_invoice = models.BillingXml(
                regional_center_id=appts[0].client.regional_center_id,
                billing_month=current_month
                )

    for client_id in appts_by_client:
        # Grab Auth to check dates and Max Visits
        # If auth is not valid Skip appt writing and leave billed.
        # If More appts then Auth Max pop last appt and leave it off.
        client = models.Client.query.get(client_id)
        client_auths = client.auths
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

            # Finds if # of Appts is more than Max Appts and truncates those appointments from the array for processing
            if len(appts_by_client[client_id][appt_type_id]) > current_auth.monthly_visits:
                for appt in appts_by_client[client_id][appt_type_id][current_auth.monthly_visits:]:
                    note = models.BillingNote()
                    note.note = 'Max Number of Appts Reached. Not Billing for: ' + ' '.join(appt.client.first_name, appt.client.last_name) + ' on ' + appt.start_datetime.strftime('%b %d, %y')
                    note.client_appt_id = appt.id
                    xml_invoice.notes = xml_invoice.notes.all() + note
                appts_by_client[client_id][appt_type_id] = appts_by_client[client_id][appt_type_id][:current_auth.monthly_visits]
                appt_days = appt_days[:current_auth.monthly_visits]

            # Looks to find Duplicate days and moves the second appt to the next open day, starting over if at end of month
            new_days = []

            for i, day in enumerate(appt_days):
                if day in new_days:
                    while day in appt_days[i:] and day in new_days:
                        day = (day+1) % (current_month.replace(month=(current_month+1)%12) - datetime.timedelta(1))
                    note = models.BillingNote()
                    note.note = 'Duplicate Appts on ' + appts_by_client[client_id][appt_type_id][i].start_datetime.strftime('%b %d, %y') + '. Moved to ' + appts_by_client[client_id][appt_type_id][i].start_datetime.replace(day=day)
                    note.client_appt_id = appts_by_client[client_id][appt_type_id][i].id
                    xml_invoice.notes = xml_invoice.notes.all() + note

                new_days.append(day)

            for i in range(1, 32):
                day = SubElement(invoice_data, 'Day' + str(i))
                if i in new_days:
                    day.text = '1'


    print(tostring(tai, encoding='utf8', method='xml'))
    # write to file, add link, appts and notes to xml_invoice and commit()









start = datetime.datetime.today().replace(day=1)
end = datetime.datetime.today()


for r in models.RegionalCenter.query.filter(models.RegionalCenter.id<'3'):
    appts = gather_appts(r,start, end)
    # for appt in appts:
    #     print(appt.appt_type.name)
    if len(appts) > 0:
        build_appt_xml(appts)
