import os, base64, uuid, requests

from sqlalchemy import select, func
from flask_login import current_user
from flask import current_app
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ctypes import memset, addressof, c_char

from sbt_notes.app import db, models
from sbt_notes.secret_info import kms_endpoint

def get_filedir():
    return Path(current_app.root_path).resolve().parent / "docs" / str(current_user.company_id) / 'client_files' # replace '1' for proper classification

def generate_dek():
    return AESGCM.generate_key(bit_length=256)

def generate_nonce():
    return os.urandom(12)

def generate_filename():
    return f"{uuid.uuid4().hex}.enc"

def fetch_kek(key_version: int = 0):
    
    """
    Fetch KEK from KMS based on key version and return as mutable bytearray. defaults to version 0 which will return the most current Kek version.
    """

    response = requests.post(kms_endpoint + '/getkey',
                                json={'key_version': key_version})
    
    key_obj = response.json()
    
    return bytearray(base64.b64decode(key_obj['key'])), key_obj['key_version']

def destroy_kek(kek):

    """
    Overwrite KEK bytes and remove reference
    """
    
    memset(addressof(c_char.from_buffer(kek)), 0, len(kek))
    del kek
    
    return True

def encrypt_dek(dek: bytes, kek: bytes):
    
    dek_nonce = generate_nonce()
    
    aesgcm = AESGCM(kek)
    
    encrypted_dek = aesgcm.encrypt(dek_nonce, dek, None)
    
    return encrypted_dek, dek_nonce

def decrypt_dek(encrypted_dek: bytes, dek_nonce: bytes, kek: bytes):
    
    aesgcm = AESGCM(kek)
    
    decrypted_dek = aesgcm.decrypt(dek_nonce, encrypted_dek, None)
    
    return decrypted_dek


def encrypt_text(plaintext: str):
    '''
    takes plaintext:str
    returns {encrypted_text:bytes, text_nonce:bytes, encrypted_dek:bytes, dek_nonce:bytes, key_version:int}
    '''
    
    dek = generate_dek()
    text_nonce = generate_nonce()
    
    aesgcm = AESGCM(dek)
    
    text_bytes = plaintext.encode('utf-8')
    
    encrypted_text = aesgcm.encrypt(text_nonce, text_bytes, None)
    
    kek, key_version = fetch_kek()
    
    encrypted_dek, dek_nonce = encrypt_dek(dek, kek)
    
    destroy_kek(kek)
    
    return {'encrypted_text': encrypted_text,
            'encrypted_dek': encrypted_dek,
            'text_nonce': text_nonce,
            'dek_nonce': dek_nonce,
            'key_version': key_version}


def encrypt_text_records(table, column_to_encrypt, batch_size=1000):
    '''
    Takes a table Class from the model and the name of the column where encryption is needed.  Then batches it to encrypt the entire table.
    Params: table: table class from models, column_to_encrypt: str, batch_size: int default 1000
    outputs rows_encrypted: int.  
    Inserts encrypted_XYZ: blob (assumes encrypted column will be "encrypted_" + name of column to encrypt), 
        encrypted_dek: blob, text_nonce: blob, dek_nonce: blob, key_version: int to table for each record.
    '''
    
    encrypted_records = 0
    
    kek, key_version = fetch_kek()
    
    last_id = 0

    while True:
        stmt = (
            select(table)
            .where(table.id > last_id)
            .order_by(table.id)
            .limit(batch_size)
        )

        results = db.session.execute(stmt).scalars().all()
        
        if not results:
            break

        for row in results:
            
            dek = generate_dek()
            text_nonce = generate_nonce()
            
            plaintext = getattr(row, column_to_encrypt)
            
            text_bytes = plaintext.encode('utf-8')
            
            aesgcm = AESGCM(dek)
            
            encrypted_text = aesgcm.encrypt(text_nonce, text_bytes, None)
            
            encrypted_dek, dek_nonce = encrypt_dek(dek, kek)
            
            encrypted_column_name = f'encrypted_{column_to_encrypt}'
            
            setattr(row, encrypted_column_name, encrypted_text)
            setattr(row, 'encrypted_dek', encrypted_dek)
            setattr(row, 'text_nonce', text_nonce)
            setattr(row, 'dek_nonce', dek_nonce)
            setattr(row, 'key_version', key_version)
            
            db.session.add(row)           
            

        db.session.commit()  # commit per batch
        encrypted_records += len(results)
        last_id = results[-1].id
        
    destroy_kek(kek)
    
    return f'Encrypted {encrypted_records} records in {table.__name__}.'


def decrypt_text(row, column_to_decrypt):
    '''
    takes encrypted_text:bytes, encrypted_dek:bytes, text_nonce:bytes, dek_nonce:bytes and key_version:int.
    returns plaintext:str
    '''
    
    kek = fetch_kek(row.key_version)[0]
    
    dek = decrypt_dek(row.encrypted_dek, row.dek_nonce, kek)
    
    destroy_kek(kek)
    
    aesgcm = AESGCM(dek)
    
    encrypted_text = getattr(row, column_to_decrypt)
            
    
    plaintext = aesgcm.decrypt(row.text_nonce, encrypted_text, None)
    
    return plaintext.decode('utf-8')


def decrypt_text_records(records, column_to_decrypt):
    '''
    Takes a list of records from a model and the name of the column to decrypt.
    Params: records: list of records from model (output from a query), column_to_decrypt: str
    outputs list of objects {'record': record, 'decrypted_text': decrypted_text}
    '''
    
    initial_key_version = records[0].key_version
    
    kek, key_version = fetch_kek(initial_key_version)
    
    decrypted_records = []
    
    for row in records:
        try: 
            if row.key_version != key_version: 
                kek, key_version = fetch_kek(row.key_version)
                
            dek = decrypt_dek(getattr(row, 'encrypted_dek'), getattr(row, 'dek_nonce'), kek)
            
            aesgcm = AESGCM(dek)
            
            plaintext = aesgcm.decrypt(getattr(row, 'text_nonce'), getattr(row, column_to_decrypt), None)
            
            decrypted_records.append({'record': row,
                                'decrypted_text': plaintext.decode('utf-8')})
           
        except: 
            decrypted_text = decrypted_records.append({'record': row,
                                      'decrypted_text': f'Could not Decrypt Text for {type(row).__name__} record_id: {row.id}'})
            continue
        
    destroy_kek(kek)
    
    return decrypted_records


def rotate_all_kek(ModelTable = None, batch_size: int = 1000):
    '''
    Given a table model, with encrypted_dek column, will take the Encrypted Dek's and rotate the encryption to the next version of the Kek.
    takes Db model **must have encrypted_dek, dek_nonce, key_version columns** Defaults to None which will find every table with "encrypted_dek" and rotate the kek. 
            and batch_size to process (default 1000)
    returns rows updated and current key_version.
    '''
    
    tables = []
    
    if ModelTable == None: 
        models = [mapper.class_ for mapper in db.Model.registry.mappers]

        for model in models:
            if hasattr(model, "encrypted_dek"):
                tables.append(model)
    else: 
        tables.append(ModelTable)
        
    initial_key_version = db.session.get(tables[0], 1).key_version

    old_kek, old_key_version = fetch_kek(initial_key_version)

    new_kek, new_key_version = fetch_kek(initial_key_version + 1)
    
    records_processed = 0
        
    for table in tables:
        
        last_id = 0
        
        while True:
            stmt = (
                select(table)
                .where(table.id > last_id)
                .order_by(table.id)
                .limit(batch_size)
            )

            results = db.session.execute(stmt).scalars().all()

            if not results:
                break

            for row in results:
                if row.key_version != old_key_version: 
                    old_kek, old_key_version = fetch_kek(row.key_version)
                    new_kek, new_key_version = fetch_kek(row.key_version+1)
                
                decrypted_dek = decrypt_dek(row.encrypted_dek, row.dek_nonce, old_kek)
                
                encrypted_dek, dek_nonce = encrypt_dek(decrypted_dek, new_kek)
                
                setattr(row, 'encrypted_dek', encrypted_dek)
                setattr(row, 'dek_nonce', dek_nonce)
                setattr(row, 'key_version', new_key_version)
                
                db.session.add(row)
                records_processed += 1
                
            db.session.commit()  # commit per batch
            last_id = results[-1].id
                
    destroy_kek(old_kek)
    destroy_kek(new_kek)
    
    return records_processed


def encrypt_file(file = None):
    '''
    takes file obj
    returns {encrypted file: bytes, encrypted_filename:str, encrypted_dek: bytes, file_nonce: bytes, dek_nonce: bytes, key_version:int}
    '''
    directory_path = get_filedir()
    
    os.makedirs(directory_path, exist_ok=True)
    
    dek = generate_dek()
    file_nonce = generate_nonce()
    
    aesgcm = AESGCM(dek)
    
    file_data = file.read()
    
    encrypted_file = aesgcm.encrypt(file_nonce, file_data, None)
    
    kek, key_version = fetch_kek()
    
    encrypted_dek, dek_nonce = encrypt_dek(dek, kek)
    
    destroy_kek(kek)
    
    encrypted_filename = generate_filename()
    
    with open(directory_path / encrypted_filename, "wb") as f:
        f.write(encrypted_file)
    
    return {'encrypted_filename': encrypted_filename,
            'encrypted_dek': encrypted_dek,
            'file_nonce': file_nonce,
            'dek_nonce': dek_nonce,
            'key_version': key_version}


def encrypt_all_files():
    '''
    takes file obj
    returns {encrypted file: bytes, encrypted_filename:str, encrypted_dek: bytes, file_nonce: bytes, dek_nonce: bytes, key_version:int}
    '''
    directory_path = get_filedir()
    
    file_directory = directory_path.parent.parent
    
    files_encrypted = 0
    
    kek, key_version = fetch_kek()
    
    status = []
    status.append(f'Scanning: {file_directory}')
    
    for path in Path(file_directory).rglob("*"):    
        path_parts = path.parts
        
        if path.is_file() and 'clients' in path_parts:
            qry = select(models.FileUploadDir).where(func.lower(models.FileUploadDir.file_dir)==path_parts[-2])
            
            with open(path, 'rb') as file:
                file_data = file.read()
                
            dek = generate_dek()
            file_nonce = generate_nonce()
            
            aesgcm = AESGCM(dek)
            
            encrypted_file = aesgcm.encrypt(file_nonce, file_data, None)
            
            encrypted_dek, dek_nonce = encrypt_dek(dek, kek)
            
            encrypted_filename = generate_filename()
            
            write_path = Path('/'+path_parts[0].join(path_parts[1:8])+'/client_files')
            
            os.makedirs(write_path, exist_ok=True)
            
            with open(write_path / encrypted_filename, "wb") as f:
                f.write(encrypted_file)
            
            encrypted_file_info = {'encrypted_filename': encrypted_filename,
                                'encrypted_dek': encrypted_dek,
                                'file_nonce': file_nonce,
                                'dek_nonce': dek_nonce,
                                'key_version': key_version,
                                'readable_filename': path_parts[-1],
                                'folder': db.session.execute(qry).scalar_one_or_none(),
                                'client_id': int(path_parts[-3])
                                }
            
            status.append(f'Added file: {path}')
            db.session.add(models.ClientFile(**encrypted_file_info))
            files_encrypted += 1
    
    destroy_kek(kek)
    db.session.commit()
        
    status.append( f'Total files encrypted: {files_encrypted}.')
            
    return status


def decrypt_file(file_record):
    '''
    takes file record from client_files table
    returns file obj
    '''
    directory_path = get_filedir()
    
    with open(directory_path / file_record.encrypted_filename, "rb") as encrypted_file:
        encrypted_file_data = encrypted_file.read()
        
    kek = fetch_kek(file_record.key_version)[0]

    dek = decrypt_dek(file_record.encrypted_dek, file_record.dek_nonce, kek)
    
    destroy_kek(kek)
    
    aesgcm = AESGCM(dek)
    
    output_file_data = aesgcm.decrypt(file_record.file_nonce, encrypted_file_data, None)
    
    return output_file_data
    
        
    


