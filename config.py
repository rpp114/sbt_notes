from db_info import DB_CONFIG as db_config
import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'password'

OPENID_PROVIDERS = [
    {'name': 'Yahoo', 'url':'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}
]

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://' + db_config['username'] + ':' + db_config['password'] + '@' + db_config['server'] + ':' + db_config['port'] + '/' + db_config['database']

base_dir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_MIGRATE_REPO = os.path.join(base_dir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
