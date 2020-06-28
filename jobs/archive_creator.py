
import datetime as dt, sys, os

from shutil import copy, make_archive, rmtree

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import app, db, models


def write_appt_notes(appts, archive_dir):
    
    appt_summary = {}
    
    for appt in appts:
        
        client_name = ' '.join((appt.client.first_name, appt.client.last_name))
        client_folder = '_'.join([str(appt.client.uci_id),client_name.lower().replace(' ','_')])
        client_path = os.path.join(archive_dir,appt.appt_type.name,client_folder)
        
        os.makedirs(client_path, exist_ok=True)
        
        appt_summary[appt.appt_type.name] = appt_summary.get(appt.appt_type.name,{})
        appt_summary[appt.appt_type.name]['count'] = appt_summary[appt.appt_type.name].get('count',0) + 1
        
        new_appt = ' - '.join([appt.start_datetime.strftime('%b %d, %Y %H:%M'),client_name])
        appt_summary[appt.appt_type.name]['appts'] =  appt_summary[appt.appt_type.name].get('appts',[])
        appt_summary[appt.appt_type.name]['appts'].append(new_appt)
        
        appt_file_name = '_'.join([client_name.lower().replace(' ','_'), appt.appt_type.name, appt.start_datetime.strftime('%Y_%m_%d'), str(appt.id)])
        
        
        with open(os.path.join(client_path, appt_file_name + '.txt'), 'w') as note_file:
            
            note_file.write('Client:\t{}\n'.format(client_name))
            note_file.write('Appt Type:\t{}\n'.format(appt.appt_type.name))
            note_file.write('Appt Date:\t{}\n'.format(appt.start_datetime.strftime('%b %d, %Y %H:%M')))
                            
            therapist_name = ' '.join([appt.therapist.user.first_name, appt.therapist.user.last_name])
            note_file.write('Therapist:\t{}\n\n'.format(therapist_name))
            
            note_file.write('Appt Note:\n\n')
            if appt.note:
                note_file.write(appt.note.note)
            else:
                note_file.write('NO NOTE')

    return appt_summary



def create_financial_archive(start_date, end_date, regional_center_id):
    
    rc = models.RegionalCenter.query.get(regional_center_id)
    
    directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs',str(rc.company_id))
    # directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs','1')
    
    archive_name = 'financial_archive_{}_{}'.format(start_date.strftime('%Y_%m_%d'), end_date.strftime('%Y_%m_%d'))
    
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
            
            appt_summary = write_appt_notes(f.appts.order_by(models.ClientAppt.start_datetime).all(), bill_archive)
            
            with open(os.path.join(bill_archive, f.file_name.split('.')[0]  + '_summary.txt'), 'w') as summary_file:
                
                summary_file.write('Billing Invoice: {}\n'.format(f.file_name))
                summary_file.write('Billing Month: {}\n'.format(f.billing_month.strftime('%Y_%m_%d')))
                summary_file.write('Submitted Date: {}\n\n'.format(f.created_date.strftime('%Y_%m_%d')))
                
                for type in appt_summary:
                    summary_file.write(type.capitalize() + '\n')
                    summary_file.write('Total Appts: {}\n'.format(appt_summary[type]['count']))
                    summary_file.write('Appts:\n\n')
                    summary_file.write('\n'.join(appt_summary[type]['appts'])+'\n\n')
                        
            included_invoices.append(f.file_name)
    
    make_archive(os.path.join(directory_path,'tmp',archive_name),'zip', archive_path)
    
    rmtree(archive_path, ignore_errors=True)
        
    return (os.path.join(directory_path, 'tmp'), archive_name + '.zip')
    
    


# start_date = dt.date(2019,12,1)
# end_date = dt.date(2020,2,1)

# create_financial_archive(start_date, end_date, 3)