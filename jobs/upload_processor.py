import PyPDF2, os, sys
from PyPDF2._page import PageObject
from io import BytesIO
from .auth_processor import extract_info, insert_auth
from .facesheet_processor import extract_fs_info
from pathlib import Path
from flask_login import current_user

def auth_pdf_processor(pdf_file, client_id=None):
    '''
        Handles Uploaded Authorization PDF.
        Splits file into single auths.
        Inserts and Updates Information based on New Auths.
        Returns list of comments about actions taken.
    '''
    pdf_obj = PyPDF2.PdfReader(pdf_file)

    if pdf_obj.is_encrypted:
        pdf_obj.decrypt(current_user.company.doc_password)
        
    count = len(pdf_obj.pages)
    updated_auths = []
    for i in range(count):
        page = pdf_obj.pages[i]
        auth = extract_info(i, pdf_file)
        updated_auth = insert_auth(auth, client_id)

        file_name = '_'.join([str(auth['auth']['auth_id']), auth['auth_date'].strftime('%Y_%m_%d')]) + '.pdf'

        if updated_auth[0] == None:
            client_name = '_'.join([auth['client']['first_name'].replace(' ', '_'), auth['client']['last_name'].replace(' ','_')])
            file_name = '_'.join([client_name, file_name])

        updated_auth.append(file_name)
        updated_auths.append(updated_auth)

        write_file(page, file_name, 'authorizations', None, updated_auth[0])

    return updated_auths


def report_upload_processor(file, client=None):
    '''
        Uploads client reports into appropriate directories.

    '''
    pass

def facesheet_upload_processor(file, file_password):
    '''
        Uploads client facesheet creates client and puts it into appropriate directory.
        takes file.
        returns client

    '''
    code, client = extract_fs_info(file, file_password)
    
    if client:
        needs_password = write_file(file, file.filename, 'face sheets', file_password, client)
        if needs_password:
            return 'needs_password', None

    return code, client


def normalize_pdf(file):
    # Page → wrap into PDF
    if isinstance(file, PageObject):
        writer = PyPDF2.PdfWriter()
        writer.add_page(file)

        buffer = BytesIO()
        writer.write(buffer)
        buffer.seek(0)

        return PyPDF2.PdfReader(buffer)

    # file-like (Flask upload, BytesIO, etc.)
    if hasattr(file, "read") and hasattr(file, "seek"):
        return PyPDF2.PdfReader(file)

    # already reader
    if isinstance(file, PdfReader):
        return file

    raise TypeError(f"Unsupported type: {type(file)}")



def write_file(file, file_name, file_type, file_password=None, client=None):
    '''
        Writes uploaded files into appropriate folder
        and files allowing for organization
        Dumps files with no client desgination into tmp folder for later organization.
    '''
    pdf = normalize_pdf(file)
    
    if pdf.is_encrypted and file_password:
        if pdf.decrypt(file_password) == 0:
            return True

    base_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..',
        'docs',
        str(current_user.company_id)
    )

    folder = 'tmp' if client is None else os.path.join('clients', str(client.id))

    file_path = os.path.join(base_path, folder, file_type)
    
    os.makedirs(file_path, exist_ok=True)

    writer = PyPDF2.PdfWriter()

    for page in pdf.pages:
        writer.add_page(page)

    writer.encrypt(current_user.company.doc_password)
    with open(os.path.join(file_path, file_name), "wb") as f:
        writer.write(f)

    return False

            
        # flash('got to writer')
    # buffer = BytesIO()
        # writer.write(buffer) # write to bytes to memory
    # buffer.seek(0)
    
    # qry = select(models.FileUploadDir).where(models.FileUploadDir.file_dir==file_dir)
    # folder = db.session.execute(qry).scalar_one_or_none()
    # new_file = models.ClientFile(readable_filename=filename, folder=folder, client=client)
    # new_file.encrypt_file(buffer)
    # db.session.add(new_file)
    # db.session.commit()
    # flash('removing_temp_file')
