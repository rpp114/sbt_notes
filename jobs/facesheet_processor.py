import sys, os, datetime as dt
import pdfplumber, re
from sqlalchemy import func, desc, or_, select
from flask_login import current_user

from sbt_notes.app import db, models

def find_info_line_numbers(text):

    line_nums = {}

    for j,l in enumerate(text): # capped line limit for "ADDRESS" further down in comments.
        line = l.lstrip()
        # print(f"line number {j}. TEXT:",line)
        if line.startswith('Name:'):
            line_nums['regional_center'] = j-3
            line_nums['uci'] = j
        if line.startswith('Legal Name:'):
            line_nums['client_name'] = j
            line_nums['gender'] = j
        if line.startswith('Date of Birth/Loc:'):
            line_nums['birthdate'] = j
        if line.startswith('PrimaryPhone:'):
            line_nums['phone'] = j
        if line.startswith('C/O Name:'):
            line_nums['caregiver'] = j
        if line.startswith('Street:'):
            line_nums['street_address'] = j
            line_nums['apartment_no'] = j + 1
            line_nums['city_state'] = j + 2
            line_nums['zipcode'] = j + 4
        if line.startswith('Print Date:'):
            line_nums['service_coordinator'] = j
        
    return line_nums


def extract_fs_info(pdf_file):
    '''
        Extracts Text from Facesheet PDF and returns proper Information for processing.
    '''

    client_info = {}
    
    with pdfplumber.open(pdf_file, password='sbthrc') as fs_file:
        page = fs_file.pages[0] 
        
    text = page.extract_text(layout=True).split('\n')
    
    line_nums = find_info_line_numbers(text)
        
    client_info['first_name'] = text[line_nums['client_name']].split()[2].title()
    client_info['middle_name'] = text[line_nums['client_name']].split()[3].title()
    client_info['last_name'] = text[line_nums['client_name']].split()[4].title()
    
    client_info['gender'] = text[line_nums['client_name']].split()[-1][0]
    
    client_info['birthdate'] = dt.datetime.strptime(text[line_nums['birthdate']].split()[3], '%m/%d/%Y')
    client_info['uci_id'] = text[line_nums['uci']].split()[-1]
    
    client_info['address'] = ' '.join(text[line_nums['street_address']].split()[1:]).title()
    
    apartment_no = ''.join(text[line_nums['apartment_no']].split()[4:])
    
    if apartment_no:
        client_info['address'] += ', ' + ''.join(text[line_nums['apartment_no']].split()[4:])
        
    client_info['city'] = ' '.join(text[line_nums['city_state']].split()[2:-1])
    client_info['state'] = text[line_nums['city_state']].split()[-1]
    
    client_info['phone'] = text[line_nums['phone']].split()[1]
    
    client_info['zipcode'] = text[line_nums['zipcode']].split()[-1]
    
    regional_center_name = text[line_nums['regional_center']].split()[0]
    
    rc_result = db.session.execute(select(models.RegionalCenter)
                                         .where(models.RegionalCenter.company_id == current_user.company_id,
                                                models.RegionalCenter.name == regional_center_name)).one_or_none()
    regional_center = None
    
    if rc_result:
        regional_center = rc_result[0]
        
    if not regional_center:
        return ('No RC', None)
    
    client_info['regional_center_id'] = regional_center.id
    
    client_query = (select(models.Client).where(models.Client.uci_id == client_info['uci_id'],
                                              models.Client.regional_center_id == regional_center.id))
                                              
    client_result = db.session.execute(client_query).all()
    
    if client_result:
        return ('existing_client', client_result[0])
    
    new_client = models.Client(**client_info)
    
    caseworker_first_name = text[line_nums['service_coordinator']].split()[-3]
    caseworker_last_name = text[line_nums['service_coordinator']].split()[-2]
    
    cw_query = (select(models.CaseWorker)
                .where(func.lower(models.CaseWorker.first_name) == caseworker_first_name.lower(),
                        func.lower(models.CaseWorker.last_name) == caseworker_last_name.lower(),
                        models.CaseWorker.status == 'active',
                        models.CaseWorker.regional_center.has(company_id = current_user.company_id)
                        )
                )
    
    cw_result = db.session.execute(cw_query).all()
    
    if len(cw_result) == 1:
        new_client.case_worker = cw_result[0]
    
    return ('new_client', new_client)


def insert_auth(new_auth, client_id):
    '''
        Handles processed Auth information as an dict.
        Inserts and updates appropriate information as needed.
        Returns tuple of Client and Comment on actions taken.
    '''

    comments = ['Found authorization for {} {} - Auth No: {}'.format(new_auth['client']['first_name'], new_auth['client']['last_name'], new_auth['auth']['auth_id'])]
    company_id = current_user.company_id

    if client_id == None:

        clients = models.Client.query.filter(models.Client.uci_id==new_auth['client']['uci_id'],\
                                            models.Client.regional_center.has(company_id=company_id)).all()

        if len(clients) == 0:
            clients = models.Client.query.filter(or_(func.lower(models.Client.first_name).like(new_auth['client']['first_name'][:5].lower() + "%"),
                                                 func.lower(models.Client.last_name).like(new_auth['client']['last_name'][:5].lower() + "%")),
                                                 models.Client.regional_center.has(company_id = company_id),
                                                 models.Client.uci_id == 0).all()

        if len(clients) == 0:
            return [None, ['No client found for Authorization Number: {}'.format(new_auth['auth']['auth_id'])]]
        elif len(clients) > 1:
            return [None, ['Multiple clients found for Authorization Number: {}. Which one is it?.'.format(new_auth['auth']['auth_id'])]]
        else:
            client = clients[0]

    else:
        if client_id == 0:
            regional_center = models.RegionalCenter.query.filter(func.lower(models.RegionalCenter.name) == new_auth['regional_center'].lower(),
                                                                 models.RegionalCenter.company_id == company_id).first()
            
            client = models.Client.query.filter(func.lower(models.Client.first_name) == 'new').first()
            
            if client == None:
            
                client = models.Client(first_name = new_auth['client']['first_name'],
                                   last_name = new_auth['client']['last_name'],
                                   regional_center = regional_center,
                                   therapist = current_user.therapist)
            else:
                client.first_name = new_auth['client']['first_name']
                client.last_name = new_auth['client']['last_name']
                client.regional_center = regional_center
                client.therapist = current_user.therapist
                client.status = 'active'
            
            db.session.add(client)
            comments.append('Created New Client: {} {}.'.format(new_auth['client']['first_name'], new_auth['client']['last_name']))
        else:
            client = models.Client.query.get(client_id)

    case_worker = models.CaseWorker.query.filter(func.lower(models.CaseWorker.first_name).like(new_auth['case_worker']['first_name'][:3].lower() + '%'),\
                                                    func.lower(models.CaseWorker.last_name).like(new_auth['case_worker']['last_name'][:5].lower() + '%'),\
                                                    models.CaseWorker.status == 'active',
                                                    models.CaseWorker.regional_center.has(company_id = company_id)).first()

    if case_worker == None:
        case_worker = models.CaseWorker(**new_auth['case_worker'])
        case_worker.regional_center = client.regional_center
        comments.append('Added New Case Worker: {} {} for {}.'.format(case_worker.first_name, case_worker.last_name, case_worker.regional_center.name))
        db.session.add(case_worker)

    existing_auth = client.auths.filter_by(auth_id = new_auth['auth']['auth_id']).order_by(desc(models.ClientAuth.created_date)).first()
    if existing_auth != None:
        existing_end_date = existing_auth.auth_end_date.strftime('%b %Y')

    for obj, update_values in new_auth.items():
        if obj == 'client':
            update_obj = client
        elif obj == 'auth':
            if existing_auth == None:
                continue
            update_obj = existing_auth
        else:
            continue

        for key, value in update_values.items():
            attr = getattr(update_obj, key, 'SKIP')

            if attr == 'SKIP' or attr == value:
                continue
            else:
                if key in ['created_date']:
                    continue
                key_name = ' '.join([k.capitalize() for k in key.split('_')])
                name = client.first_name + ' ' + client.last_name if obj == 'client' else existing_auth.auth_id
                comments.append('Updated {} from {} to {} for {}: {}'.format(key_name, attr, value, obj, name))
                setattr(update_obj, key, value)

    if client.case_worker != case_worker:
        client.case_worker = case_worker
        comments.append('Updated Case Worker for {} to {}'.format(client.first_name + ' ' + client.last_name,
                                                                          case_worker.first_name + ' ' + case_worker.last_name))

    if existing_auth == None:
        existing_auth = models.ClientAuth(**new_auth['auth'])
        comments.append('Created New Auth for {}.'.format(client.first_name + ' ' + client.last_name))
        db.session.add(existing_auth)

        if not new_auth['auth']['is_eval_only']:

            for auth in client.auths:
                auth.status = 'inactive'
        else:
            existing_auth.status = 'inactive'
        
        client.auths.append(existing_auth)
        insert_auth_reminder(existing_auth)
        flash('Auth Reminder for %s inserted into Google Calendar' % (client.first_name + ' ' + client.last_name))

    else:
        existing_auth.status = 'active'

        new_auth_end_date = existing_auth.auth_end_date.strftime('%b %Y')

        if not existing_auth.is_eval_only and existing_end_date != new_auth_end_date:
            move_auth_reminder(existing_auth)
            flash('Auth Reminder moved for %s from %s to %s.' % (client.first_name + ' ' + client.last_name, existing_end_date, new_auth_end_date))

    db.session.commit()
    return [client, comments]
