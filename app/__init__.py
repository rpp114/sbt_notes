from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_oauthlib.client import OAuth
from flask_security import Security, SQLAlchemyUserDatastore
from flask_login import LoginManager, current_user
from flask_admin import Admin
from flask_permissions.core import Permissions

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
admin = Admin(app)
oauth_credentials = app.config['OAUTH_CREDENTIALS']
perms = Permissions(app, db, current_user)

from app import views, models, admin, perms


user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)
