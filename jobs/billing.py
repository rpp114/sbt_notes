import sys, os, datetime, calendar

from sqlalchemy import and_, func, between
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models


def build_appt_xml(appts, maxed_appts=[], write=False):

    '''Takes an array of Appt Objects From Same Regional Center and will write XML file to static docs directory.'''

    maxed_length = len(maxed_appts)

    appts = maxed_appts + appts

    appts_by_client = build_billing_obj(appts, maxed_length=maxed_length)

    invoices = []

    xml_invoice_id = None

    for regional_center_id in appts_by_client:
        regional_center = models.RegionalCenter.query.get(regional_center_id)
        for billing_month in appts_by_client[regional_center_id]:
            total_appts = []
            notes = []
            tai = Element('TAI')
            invoice = ElementTree(element=tai)
            current_month = datetime.datetime.strptime(billing_month,'%Y-%m-%d')

            appts_by_rc_by_month = appts_by_client[regional_center_id][billing_month]

            for client_id in appts_by_rc_by_month:
                client = models.Client.query.get(client_id)

                for appt_type_id in appts_by_rc_by_month[client_id]:
                    list_of_appts = appts_by_rc_by_month[client_id][appt_type_id]
                    appt_type = models.ApptType.query.get(appt_type_id)

                    if appt_type.name.lower() == 'evaluation':
                        client_auths = client.auths.filter_by(is_eval_only = 1).order_by(models.ClientAuth.id).all()
                    else:
                        client_auths = client.auths.filter_by(is_eval_only = 0).order_by(models.ClientAuth.id).all()

                    current_auth = None

                    # need to be able to handle auths starting midway through the month
                    # Billing error occurred
                    for auth in client_auths:
                        if current_month >= auth.auth_start_date.replace(day=1) and current_month <= auth.auth_end_date:
                            current_auth = auth

                    if not current_auth: # add logic to check if billing month is >6 and auth[:2] == billing year [3:]
                        for appt in list_of_appts:
                            note = models.BillingNote()
                            note.note = 'No valid auth for {} as of {}'.format((client.first_name + ' ' + client.last_name), datetime.datetime.now().strftime('%b %d, %Y'))
                            note.client_appt_id = appt.id
                            notes.append(note)
                        continue

                    invoice_data = SubElement(tai, 'invoicedata')

                    RecType = SubElement(invoice_data, 'RecType')
                    RecType.text = 'D'
                    RCID = SubElement(invoice_data, 'RCID')
                    RCID.text = str(regional_center.rc_id)
                    ATTN = SubElement(invoice_data, 'AttnOnlyFlag')
                    SPNID = SubElement(invoice_data, 'SPNID')
                    SPNID.text = str(client.regional_center.company.vendor_id)
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

                    if len(list_of_appts) > current_auth.monthly_visits:
                        unbilled_appts = list_of_appts[current_auth.monthly_visits:]
                        list_of_appts = list_of_appts[:current_auth.monthly_visits]

                        for unbilled_appt in unbilled_appts:
                            note = models.BillingNote()
                            note.note = 'Max Number of Appts Reached: ' + str(current_auth.monthly_visits) + ' Not Billing for: ' + ' '.join([unbilled_appt.client.first_name, unbilled_appt.client.last_name]) + ' on ' + unbilled_appt.start_datetime.strftime('%b %d, %y')
                            note.client_appt_id = unbilled_appt.id
                            notes.append(note)


                    # Looks to find Duplicate days and moves the second appt to the next open day, starting over if at end of month
                    appt_days = [d.start_datetime.day for d in list_of_appts]

                    new_days = []

                    for i, day in enumerate(appt_days):
                        moved_day = False

                        if current_month.month != list_of_appts[i].start_datetime.month:
                            day = 1
                            moved_day = True
                        # Date should have moved on Eval to start of authorization... why didn't it for Audrielle??
                        if list_of_appts[i].start_datetime < current_auth.auth_start_date:
                            day = current_auth.auth_start_date.day
                            moved_day = True

                        if list_of_appts[i].start_datetime > current_auth.auth_end_date.replace(hour=23, minute=59):
                            day = current_auth.auth_end_date.day
                            moved_day = True

                        eom = calendar.monthrange(current_month.year, current_month.month)[1]
                        if day in new_days:
                            while day in appt_days[i:] or day in new_days:
                                day = (day+1) % eom
                                if day == 0:
                                    day = eom
                            moved_day = True

                        if moved_day:
                            moved_to_date = list_of_appts[i].start_datetime.replace(day=day)

                            if list_of_appts[i].start_datetime.month != current_month.month:
                                moved_to_date = moved_to_date.replace(month=current_month.month)

                            while moved_to_date.weekday() > 4:
                                day = (day+1) % eom
                                if day == 0:
                                    day = eom
                                moved_to_date = moved_to_date.replace(day=day)

                            moved_to_date_string = moved_to_date.strftime('%b %d, %Y')

                            note = models.BillingNote()
                            note.note = 'Appt moved from ' + list_of_appts[i].start_datetime.strftime('%b %d, %Y') + ' to ' + moved_to_date_string
                            note.client_appt_id = list_of_appts[i].id
                            notes.append(note)

                        new_days.append(day)

                    total_appts += list_of_appts

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


            if write and total_appts:
                xml_invoice = models.BillingXml(
                            regional_center_id=regional_center_id,
                            billing_month=current_month
                            )
                xml_invoice.appts = total_appts
                xml_invoice.notes = notes
                db.session.add(xml_invoice)
                db.session.commit()
                file_name = 'invoice_%s_%s_%s.xml' %(regional_center_id, xml_invoice.id, billing_month)

                file_directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs',str(xml_invoice.regional_center.company_id),'billing/')

                if not os.path.exists(file_directory_path):
                    os.makedirs(file_directory_path)

                file_path = os.path.join(file_directory_path, file_name)
                invoice.write(file_path, xml_declaration=True, encoding='UTF-8')
                xml_invoice.file_name = file_name
                db.session.add(xml_invoice)
                xml_invoice_id = xml_invoice.id
                db.session.commit()

            if write:
                if xml_invoice_id:
                    invoices.append({'invoice': invoice, 'notes': notes, 'xml_invoice_id': xml_invoice_id})
            else:
                invoices.append({'invoice': invoice, 'notes': notes, 'xml_invoice_id': xml_invoice_id})

    return invoices


def build_billing_obj(appts, maxed_length=0):

    appts_by_client = {}

    for i, appt in enumerate(appts):
        appt_rc_id = appt.appt_type.regional_center_id
        appt_yr_mn = appt.start_datetime.replace(day=1).strftime('%Y-%m-%d')

        if i < maxed_length:
            eom_day = calendar.monthrange(appt.start_datetime.year, appt.start_datetime.month)[1]
            appt_yr_mn = (appt.start_datetime.replace(day=eom_day) + datetime.timedelta(1)).strftime('%Y-%m-%d')

        appt_c_id = appt.client.id
        appt_at_id = appt.appt_type.id

        appts_by_client[appt_rc_id] = appts_by_client.get(appt_rc_id, {})
        appts_by_client[appt_rc_id][appt_yr_mn] = appts_by_client[appt_rc_id].get(appt_yr_mn, {})
        appts_by_client[appt_rc_id][appt_yr_mn][appt_c_id] = appts_by_client[appt_rc_id][appt_yr_mn].get(appt_c_id, {})
        appts_by_client[appt_rc_id][appt_yr_mn][appt_c_id][appt_at_id] = appts_by_client[appt_rc_id][appt_yr_mn][appt_c_id].get(appt_at_id, [])
        appts_by_client[appt_rc_id][appt_yr_mn][appt_c_id][appt_at_id].append(appt)

    return appts_by_client


def get_appts_for_grid(etree, notes=[]):

    '''Takes a ElementTree from xml file or output and a list of notes.  Returns an object to build the Appt
            Grid for viewing invoice.'''

    root_element = etree.getroot()

    appts_for_grid = []

    appt_count = 0
    appt_amount = 0

    grid_obj = {'evaluation': {'appts_for_grid': [],
                               'appt_count': 0,
                               'appt_amount': 0,
                               'daily_totals': [0] * 31},
                'treatment': {'appts_for_grid': [],
                               'appt_count': 0,
                               'appt_amount': 0,
                               'daily_totals': [0] * 31},
                }

    for child in root_element:
        appt = {}
        vendor_id = child.find('SPNID').text
        company = models.Company.query.filter_by(vendor_id = vendor_id).first()

        regional_center_rc_id = child.find('RCID').text
        regional_center = models.RegionalCenter.query.filter(models.RegionalCenter.rc_id == regional_center_rc_id, models.RegionalCenter.company_id == company.id).first()

        if child.find('UCI').text == '0':
            client = models.Client.query.filter(models.Client.first_name == child.find('firstname').text, models.Client.last_name == child.find('lastname').text, models.Client.regional_center_id == regional_center.id).first()
        else:
            client = models.Client.query.filter(models.Client.uci_id == child.find('UCI').text, models.Client.regional_center_id == regional_center.id).first()

        appt['client_id'] = client.id
        appt['firstname'] = client.first_name
        appt['lastname'] = client.last_name

        svcs_code = child.find('SVCSCode').text

        appt_type_name = db.session.query(models.ApptType.name).filter(models.ApptType.service_type_code == svcs_code, models.ApptType.regional_center_id == regional_center.id).first()
        appt['appt_type'] = appt_type_name[0]
        appt['total_appts'] = child.find('EnteredUnits').text
        grid_obj[appt['appt_type']]['appt_count'] += int(appt['total_appts'])
        appt['total_amount'] = child.find('EnteredAmount').text
        grid_obj[appt['appt_type']]['appt_amount'] += float(appt['total_amount'])
        appt_month = datetime.datetime.strptime(child.find('SVCMnYr').text, '%Y-%m-%d')
        appt['start_date'] = appt_month
        last_day = appt_month.replace(day=calendar.monthrange(appt_month.year, appt_month.month)[1])
        appt['end_date'] = last_day
        appt['appts'] = [''] * last_day.day
        for day in range(1,last_day.day+1):
            if child.find('Day' + str(day)).text:
                appt['appts'][day-1] = child.find('Day' + str(day)).text
                grid_obj[appt['appt_type']]['daily_totals'][day-1] += 1

        grid_obj[appt['appt_type']]['daily_totals'] = grid_obj[appt['appt_type']]['daily_totals'][:last_day.day]

        grid_obj[appt['appt_type']]['appts_for_grid'].append(appt)

    grid_obj['treatment']['appts_for_grid'].sort(key=lambda x: x['lastname'])
    grid_obj['evaluation']['appts_for_grid'].sort(key=lambda x: x['lastname'])

    grid_obj['notes'] = {}

    notes_for_grid = grid_obj['notes']

    for note in notes:
        
        appt = models.ClientAppt.query.get(note.client_appt_id)
        notes_for_grid[appt.client.id] = notes_for_grid.get(appt.client.id, {'name': appt.client.first_name + ' ' + appt.client.last_name, 'notes': []})
        if note.note in notes_for_grid[appt.client.id]['notes']:
            continue
        notes_for_grid[appt.client.id]['notes'].append(note.note)

    grid_obj['days'] = last_day.day

    return grid_obj
