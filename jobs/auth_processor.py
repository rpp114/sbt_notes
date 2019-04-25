import sys, os, datetime as dt
from sqlalchemy import and_, func, desc
from flask_login import current_user
from flask import flash

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models
from appts import insert_auth_reminder, move_auth_reminder

def find_info_line_numbers(text):

    line_nums = {}

    for j,l in enumerate(text):
        if 'Page' in l:
            line_nums['address'] = j + 1
        if l.strip() == 'VENDOR NO':
            line_nums['client_name'] = j -1
        if l.strip() == 'A Project of':
            line_nums['regional_center'] = j + 2
        if l.strip() == 'BIRTH DATE':
            line_nums['uci'] = j + 1
            line_nums['client_birth_date'] = j + 2
            line_nums['case_worker'] = j + 4
            line_nums['client_phone'] = j + 5
        if l.strip() == 'AUTHORIZATION NO:':
            line_nums['auth_date'] = j - 1
            line_nums['auth_number'] = j + 1
            line_nums['auth_type'] = j + 2
            line_nums['auth_valid_dates'] = j + 3
            line_nums['auth_visits'] = j + 4

    return line_nums


def extract_info(page):
    '''
        Extracts Text from Auth PDF and returns proper Information for processing.
    '''

    auth_info = {'client':{},
                 'case_worker':{},
                 'auth':{}}

    text = page.extractText().split('\n')
    line_nums = find_info_line_numbers(text)

    space_count = 0
    for i,l in enumerate(text[line_nums['client_name']]):
        if l == ' ':
            space_count += 1
        elif space_count == 1 and l != ' ':
            space_count = 0
        elif space_count > 1:
            auth_info['client']['last_name'] = ' '.join([n.capitalize() for n in text[line_nums['client_name']][:i].split()])
            auth_info['client']['first_name'] = ' '.join([n.capitalize() for n in text[line_nums['client_name']][i:].split()])
            break

    address_list = []
    for i in range(line_nums['address'],line_nums['client_name']-1):
        address_list += [n.capitalize() for n in text[i].split()]
    auth_info['client']['address'] = ' '.join(address_list)

    city_info = text[line_nums['client_name']-1].split()

    auth_info['client']['zipcode'] = city_info[-1]
    auth_info['client']['state'] = city_info[-2]
    auth_info['client']['city'] = ' '.join([c.capitalize() for c in city_info[:-2]])

    auth_info['client']['birthdate'] = dt.datetime.strptime(text[line_nums['client_birth_date']], '%m/%d/%Y')

    auth_info['client']['uci_id'] = int(text[line_nums['uci']].strip())

    auth_info['client']['phone'] = text[line_nums['client_phone']].strip()

    auth_info['case_worker']['first_name'] = ' '.join([n.capitalize() for n in text[line_nums['case_worker']].split(',')[1].split()])
    auth_info['case_worker']['last_name'] = ' '.join([n.capitalize() for n in text[line_nums['case_worker']].split(',')[0].split()])

    auth_info['auth_date'] = dt.datetime.strptime(text[line_nums['auth_date']], '%m/%d/%y')
    auth_info['regional_center'] = text[line_nums['regional_center']]
    auth_info['auth']['created_date'] = dt.datetime.now()
    auth_info['auth']['auth_id'] = int(text[line_nums['auth_number']].strip())

    auth_info['auth']['is_eval_only'] = 1 if text[line_nums['auth_type']].split()[1] == 'EVLOT' else 0

    auth_info['auth']['auth_start_date'] = dt.datetime.strptime(text[line_nums['auth_valid_dates']].split()[-2], '%m/%d/%y')
    auth_info['auth']['auth_end_date'] = dt.datetime.strptime(text[line_nums['auth_valid_dates']].split()[-1], '%m/%d/%y')

    auth_info['auth']['monthly_visits'] = int(round(float(text[line_nums['auth_visits']].split()[-3])))

    return auth_info


def insert_auth(new_auth, client_id):
    '''
        Handles processed Auth information.
        Inserts and updates appropriate information as needed.
        Returns tuple of Client and Comment on actions taken.
    '''

    comments = ['Found authorization for {} {} - Auth No: {}'.format(new_auth['client']['first_name'], new_auth['client']['last_name'], new_auth['auth']['auth_id'])]
    company_id = current_user.company_id

    if client_id == None:

        clients = models.Client.query.filter(models.Client.uci_id==new_auth['client']['uci_id'],\
                                            models.Client.regional_center.has(company_id=company_id)).all()

        if len(clients) == 0:
            clients = models.Client.query.filter(func.lower(models.Client.first_name).like(new_auth['client']['first_name'][:5].lower() + "%"),\
                                                 func.lower(models.Client.last_name).like(new_auth['client']['last_name'][:5].lower() + "%"),\
                                                 models.Client.regional_center.has(company_id = company_id)).all()


        if len(clients) == 0:
            return [None, ['Client does not exist for Authorization Number: {}'.format(new_auth['auth']['auth_id'])]]
        elif len(clients) > 1:
            return [None, ['Multiple clients found for Authorization Number: {}. Please input by hand.'.format(new_auth['auth']['auth_id'])]]
        else:
            client = clients[0]

    else:
        if client_id == 0:
            regional_center = models.RegionalCenter.query.filter(func.lower(models.RegionalCenter.name) == new_auth['regional_center'].lower(),
                                                                 models.RegionalCenter.company_id == company_id).first()
            client = models.Client(first_name = new_auth['client']['first_name'],
                                   last_name = new_auth['client']['last_name'],
                                   regional_center = regional_center,
                                   therapist = current_user.therapist)
            db.session.add(client)
            comments.append('Created New Client: {} {}.'.format(new_auth['client']['first_name'], new_auth['client']['last_name']))
        else:
            client = models.Client.query.get(client_id)

    case_worker = models.CaseWorker.query.filter(func.lower(models.CaseWorker.first_name).like(new_auth['case_worker']['first_name'][:3].lower() + '%'),\
                                                    func.lower(models.CaseWorker.last_name).like(new_auth['case_worker']['last_name'][:5].lower() + '%'),\
                                                    models.CaseWorker.regional_center.has(company_id = company_id)).first()

    if case_worker == None:
        case_worker = models.CaseWorker(**new_auth['case_worker'])
        case_worker.regional_center = client.regional_center
        comments.append('Added New Case Worker: {} {} for {}.'.format(case_worker.first_name, case_worker.last_name, case_worker.regional_center.name))
        db.session.add(case_worker)

    existing_auth = client.auths.filter_by(auth_id = new_auth['auth']['auth_id']).order_by(desc(models.ClientAuth.created_date)).first()
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
        client.auths.append(existing_auth)
        if not new_auth['auth']['is_eval_only']:
            insert_auth_reminder(existing_auth)
            flash('Auth Reminder for %s inserted into Google Calendar' % (client.first_name + ' ' + client.last_name))
    else:
        new_auth_end_date = existing_auth.auth_end_date.strftime('%b %Y')
        if not existing_auth.is_eval_only and existing_end_date != new_auth_end_date:
            move_auth_reminder(existing_auth)
            flash('Auth Reminder moved for %s from %s to %s.' % (client.first_name + ' ' + client.last_name, existing_end_date, new_auth_end_date))

    db.session.commit()
    return [client, comments]
