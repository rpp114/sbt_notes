import secret_info
import os
from datetime import timedelta

WTF_CSRF_ENABLED = True
SECRET_KEY = secret_info.SECRET_KEY
REMEMBER_COOKIE_DURATION = timedelta(days=30)


# Login Settings

OPENID_PROVIDERS = [
    {'name': 'Yahoo', 'url':'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}
]

# DB & model repository Settings

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://%(username)s:%(password)s@%(server)s:%(port)s/%(database)s' %secret_info.DB_CONFIG

base_dir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_MIGRATE_REPO = os.path.join(base_dir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# OAuth Config Settings
OAUTH_CREDENTIALS = {
    'google': secret_info.GOOGLE_JSON_CREDENTIALS
    }
