import sys, os, datetime

from sqlalchemy import and_, func, between
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models


def build_appt_xml(appts, write=False):

    '''Takes an array of Appt Objects From Same Regional Center and will write XML file to static docs directory.'''

    appts_by_client = build_billing_obj(appts)

    invoices = []

    for regional_center_id in appts_by_client:
        for billing_month in appts_by_client[regional_center_id]:
            tai = Element('TAI')
            invoice = ElementTree(element=tai)
            current_month = datetime.datetime.strptime(billing_month,'%Y-%m-%d')

            appts_by_rc_by_month = appts_by_client[regional_center_id][billing_month]

            for client_id in appts_by_rc_by_month:
                client = models.Client.query.get(client_id)
                client_auths = client.auths
                current_auth = None

                for auth in client_auths:
                    if current_month >= auth.auth_start_date and current_month <= auth.auth_end_date:
                        current_auth = auth

                if current_auth == None:
                    print('Need New Auth for: ', ' '.join([client.first_name, client.last_name]))
                    continue

                for appt_type_id in appts_by_rc_by_month[client_id]:
                    list_of_appts = appts_by_rc_by_month[client_id][appt_type_id]
                    appt_type = models.ApptType.query.get(appt_type_id)
                    appt_days = [d.start_datetime.day for d in list_of_appts]

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
                    svc_code.text = str(appt_type.service_code)
                    svcs_code = SubElement(invoice_data, 'SVCSCode')
                    svcs_code.text = appt_type.service_type_code
                    svc_mn_yr = SubElement(invoice_data, 'SVCMnYr')
                    svc_mn_yr.text = current_month.strftime('%Y-%m-%d')
                    industry_type = SubElement(invoice_data, 'IndustryType')
                    wage_amt = SubElement(invoice_data, 'WageAmt')
                    wage_type = SubElement(invoice_data, 'WageType')

                    # Finds if # of Appts is more than Max Appts and truncates those appointments from the array for processing

                    notes = []

                    if len(list_of_appts) > auth.monthly_visits:
                        unbilled_appts = list_of_appts[current_auth.monthly_visits:]
                        list_of_appts = list_of_appts[:current_auth.monthly_visits]

                        for unbilled_appt in unbilled_appts:
                            note = models.BillingNote()
                            note.note = 'Max Number of Appts Reached. Not Billing for: ' + ' '.join([unbilled_appt.client.first_name, unbilled_appt.client.last_name]) + ' on ' + unbilled_appt.start_datetime.strftime('%b %d, %y')
                            note.client_appt_id = unbilled_appt.id
                            notes.append(note)


                    # Looks to find Duplicate days and moves the second appt to the next open day, starting over if at end of month

                    new_days = []

                    for i, day in enumerate(appt_days):
                        if day in new_days:
                            while day in appt_days[i:] and day in new_days:
                                day = (day+1) % (current_month.replace(month=(current_month+1)%12) - datetime.timedelta(1))
                            note = models.BillingNote()
                            note.note = ' '.join([list_of_appts[i].client.first_name, list_of_appts[i].client.last_name]) + 'had duplicate appts on ' + list_of_appts[i].start_datetime.strftime('%b %d, %y') + '. Moved to ' + list_of_appts[i].start_datetime.replace(day=day)
                            note.client_appt_id = list_of_appts[i].id
                            notes.append(note)

                        new_days.append(day)

                    appts_total = 0
                    for i in range(1, 32):
                        day = SubElement(invoice_data, 'Day' + str(i))
                        if i in new_days:
                            day.text = '1'
                            appts_total += 1
                    appt_total = SubElement(invoice_data, 'EnteredUnits')
                    appt_total.text = str(appts_total)
                    total_amount = SubElement(invoice_data, 'EnteredAmount')
                    total_amount.text = str(appts_total * appt_type.rate)

        # print(regional_center_id, billing_month)
        # print(tostring(tai, encoding='utf8', method='xml'))
        # write to file, add link, appts and notes to xml_invoice and commit()

        if write:
            xml_invoice = models.BillingXml(
                        regional_center_id=regional_center_id,
                        billing_month=current_month
                        )
            xml_invoice.appts = list_of_appts
            xml_invoice.notes = notes
            db.session.add(xml_invoice)
            db.session.commit()
            file_name = 'invoice_%s_%s_%s.xml' %(regional_center_id, xml_invoice.id, billing_month)
            file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs/billing/', file_name)
            invoice.write(file_path, xml_declaration=True, encoding='UTF-8')
            xml_invoice.file_link = file_path
            db.session.add(xml_invoice)
            db.session.commit()

        invoices.append({'invoice': invoice, 'notes': notes})

    return invoices


def build_billing_obj(appts):

    appts_by_client = {}

    for appt in appts:
        appt_rc_id = appt.client.regional_center_id
        if appt_rc_id == 1:
            continue
        appt_yr_mn = appt.start_datetime.replace(day=1).strftime('%Y-%m-%d')
        appt_c_id = appt.client.id
        appt_at_id = appt.appt_type.id

        appts_by_client[appt_rc_id] = appts_by_client.get(appt_rc_id, {})
        appts_by_client[appt_rc_id][appt_yr_mn] = appts_by_client[appt_rc_id].get(appt_yr_mn, {})
        appts_by_client[appt_rc_id][appt_yr_mn][appt_c_id] = appts_by_client[appt_rc_id][appt_yr_mn].get(appt_c_id, {})
        appts_by_client[appt_rc_id][appt_yr_mn][appt_c_id][appt_at_id] = appts_by_client[appt_rc_id][appt_yr_mn][appt_c_id].get(appt_at_id, [])
        appts_by_client[appt_rc_id][appt_yr_mn][appt_c_id][appt_at_id].append(appt)

    return appts_by_client
