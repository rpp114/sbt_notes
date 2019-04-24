import PyPDF2, os, sys
from auth_processor import extract_info, insert_auth
from flask_login import current_user

def auth_pdf_processor(pdf_file, client_id=None):
    '''
        Handles Uploaded Authorization PDF.
        Splits file into single auths.
        Inserts and Updates Information based on New Auths.
        Returns list of comments about actions taken.
    '''
    pdfReader = PyPDF2.PdfFileReader(pdf_file)

    count = pdfReader.numPages
    updated_auths = []
    for i in range(count):
        page = pdfReader.getPage(i)
        auth = extract_info(page)

        updated_auth = insert_auth(auth, client_id)

        file_name = '_'.join([str(auth['auth']['auth_id']), auth['auth_date'].strftime('%Y_%m_%d')]) + '.pdf'
        if updated_auth[0] == None:
            client_name = '_'.join([auth['client']['first_name'].replace(' ', '_'), auth['client']['last_name'].replace(' ','_')])
            file_name = '_'.join([client_name, file_name])

        updated_auth.append(file_name)
        updated_auths.append(updated_auth)
        
        write_file(page, file_name, 'auth', updated_auth[0])

    return updated_auths


def write_file(file, file_name, file_type, client=None):
    '''
        Writes uploaded files into appropriate folder
        and files allowing for organization
        Dumps files with no client desgination into tmp folder for later organization.
    '''

    directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs',str(current_user.company_id))

    if client == None:
        folder_name = 'tmp'
    else:
        folder_name = os.path.join('clients',str(client.id))

    file_path = os.path.join(directory_path, folder_name, file_type)

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    if file_name.endswith('.pdf'):
        writer = PyPDF2.PdfFileWriter()
        writer.addPage(file)
        with open(os.path.join(file_path, file_name), 'wb') as pdf_write:
            writer.write(pdf_write)
    else:
        pass
