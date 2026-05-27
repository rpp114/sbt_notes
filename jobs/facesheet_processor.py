import sys, os, datetime as dt
import pdfplumber, re
from sqlalchemy import func, desc, or_, select
from flask_login import current_user


from PyPDF2 import PdfReader


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


def extract_fs_info(pdf_file, file_password):
    '''
        Extracts Text from Facesheet PDF and returns proper Information for processing.
    '''

    client_info = {}
    
    upload_file = PdfReader(pdf_file.stream)
    
  
    try:
        pdf_file.seek(0)

        with pdfplumber.open(pdf_file) as fs_file:
            page = fs_file.pages[0] 

    except Exception:
        pdf_file.seek(0)

        with pdfplumber.open(pdf_file, password=file_password) as fs_file:
            page = fs_file.pages[0] 
        
        # with pdfplumber.open(pdf_file, password=file_password) as fs_file:
        #     page = fs_file.pages[0] 
        
        
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
        return 'No RC', None
    
    client_info['regional_center_id'] = regional_center.id
    
    client_query = (select(models.Client).where(models.Client.uci_id == client_info['uci_id'],
                                              models.Client.regional_center_id == regional_center.id))
                                              
    client_result = db.session.execute(client_query).scalars().all()
    
    if client_result:
        return 'existing_client', client_result[0]
    
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
    
    cw_result = db.session.execute(cw_query).scalars().all()

    if len(cw_result) == 1:
        new_client.case_worker = cw_result[0]
    
    db.session.add(new_client)
    db.session.commit()
    
    return 'new_client', new_client

