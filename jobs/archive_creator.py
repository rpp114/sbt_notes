
import datetime as dt, sys, os

from shutil import copy, make_archive, rmtree

from fpdf import FPDF

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import app, db, models


def create_pdf_note_summaries(paths):
    
    for path in paths:
        
        pdf_file_name = path.split('/')[-1] + '_notes_summary.pdf'
        notes_summary_pdf = FPDF()
        
        notes_summary_pdf.set_font('Arial', size = 12)
        
        files = os.listdir(path)
        files.sort()
        
        for f in files:
            if 'txt' == f.split('.')[1]:
                with open(os.path.join(path, f), 'r') as txt_file:
                    text = txt_file.read()
                    
                    text_no_latin = text.encode('latin-1', 'replace').decode('latin-1')
                    
                    notes_summary_pdf.add_page()
                    notes_summary_pdf.multi_cell(190, 10, txt = text_no_latin)
        
        notes_summary_pdf.output(os.path.join(path, pdf_file_name))
    
    return True




def write_appt_notes(appts, archive_dir, pdfs=False):
    
    appt_summary = {}
    
    client_paths = set()
    
    for appt in appts:
        
        client_name = ' '.join((appt.client.first_name, appt.client.last_name))
        client_folder = '_'.join([str(appt.client.uci_id),client_name.lower().replace(' ','_')])
        client_path = os.path.join(archive_dir,appt.appt_type.name,client_folder)
        
        if appt.appt_type.name.lower() == 'treatment':
            client_paths.add(client_path)
        
        os.makedirs(client_path, exist_ok=True)
        
        appt_summary[appt.appt_type.name] = appt_summary.get(appt.appt_type.name,{})
        appt_summary[appt.appt_type.name]['count'] = appt_summary[appt.appt_type.name].get('count',0) + 1
        
        new_appt = ' - '.join([appt.start_datetime.strftime('%b %d, %Y %H:%M'),client_name])
        appt_summary[appt.appt_type.name]['appts'] =  appt_summary[appt.appt_type.name].get('appts',[])
        appt_summary[appt.appt_type.name]['appts'].append(new_appt)
        
        appt_file_name = '_'.join([client_name.lower().replace(' ','_'), appt.appt_type.name, appt.start_datetime.strftime('%Y_%m_%d'), str(appt.id)])
        
        
        with open(os.path.join(client_path, appt_file_name + '.txt'), 'w') as note_file:
            
            note_file.write('Client:      {}\n'.format(client_name))
            note_file.write('Appt Type:   {}\n'.format(appt.appt_type.name))
            note_file.write('Appt Date:   {}\n'.format(appt.start_datetime.strftime('%b %d, %Y %H:%M')))
                            
            therapist_name = ' '.join([appt.therapist.user.first_name, appt.therapist.user.last_name])
            note_file.write('Therapist:   {}\n\n'.format(therapist_name))
            
            note_file.write('Appt Note:\n\n')
            if appt.note:
                note_file.write(appt.note.note)
            else:
                note_file.write('NO NOTE')
        
        if appt.appt_type.name == 'evaluation':
            try:
                client_dir = os.path.join(archive_dir, '..', '..','..','clients', str(appt.client.id), 'evaluations')

                eval_file =  [f for f in os.listdir(client_dir) if str(appt.id) in f][0]
                
                copy(os.path.join(client_dir, eval_file), client_path)
                
            except:
                # print(appt.id,appt.client.first_name, appt.client.last_name)
                continue
    
    if pdfs:
        create_pdf_note_summaries(client_paths)
    
    return appt_summary



def create_financial_archive(start_date, end_date, regional_center_id):
    
    rc = models.RegionalCenter.query.get(regional_center_id)
    
    directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs',str(rc.company_id))
    # directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs','1')
    
    archive_name = '{}_financial_archive_from_{}_to_{}'.format(rc.name.lower(), start_date.strftime('%b_%Y'), end_date.strftime('%b_%Y')).lower()
    
    archive_path = os.path.join(directory_path, 'tmp', archive_name)
    
    os.makedirs(archive_path, exist_ok = True)
        
    included_invoices = []
    
    with app.app_context():
        
        billing_files = models.BillingXml.query.filter(models.BillingXml.billing_month.between(start_date, end_date),
                                                       models.BillingXml.regional_center_id == regional_center_id).all()
        
        for f in billing_files:
            
            bill_archive = os.path.join(archive_path,'bill_month_{}_submitted_{}'.format(f.billing_month.strftime('%Y_%m_%d'),f.created_date.strftime('%Y_%m_%d')))
            
            os.makedirs(bill_archive, exist_ok=True)
            
            copy(os.path.join(directory_path, 'billing',f.file_name), bill_archive)  
            
            appt_summary = write_appt_notes(f.appts.order_by(models.ClientAppt.start_datetime).all(), bill_archive, True)
            
            with open(os.path.join(bill_archive, f.file_name.split('.')[0]  + '_summary.txt'), 'w') as summary_file:
                
                summary_file.write('Billing Invoice: {}\n'.format(f.file_name))
                summary_file.write('Billing Month: {}\n'.format(f.billing_month.strftime('%Y_%m_%d')))
                summary_file.write('Submitted Date: {}\n\n'.format(f.created_date.strftime('%Y_%m_%d')))
                
                for type in sorted(appt_summary.keys()):
                    summary_file.write(type.capitalize() + '\n')
                    summary_file.write('Total Appts: {}\n'.format(appt_summary[type]['count']))
                    summary_file.write('Appts:\n\n')
                    summary_file.write('\n'.join(appt_summary[type]['appts'])+'\n\n')
                        
            included_invoices.append(f.file_name)
    
    make_archive(os.path.join(directory_path,'tmp',archive_name),'zip', archive_path)
    
    rmtree(archive_path, ignore_errors=True)
        
    return (os.path.join(directory_path, 'tmp'), archive_name + '.zip')
    
    