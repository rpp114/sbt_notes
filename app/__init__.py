from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_oauthlib.client import OAuth
from flask_security import Security, SQLAlchemyUserDatastore
from flask_login import LoginManager
from flask_admin import Admin

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
admin = Admin(app)
oauth_credentials = app.config['OAUTH_CREDENTIALS']

from app import views, models, admin, oauth



user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)
