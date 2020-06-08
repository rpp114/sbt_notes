from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_oauthlib.client import OAuth
# from flask_security import Security, SQLAlchemyUserDatastore
from flask_login import LoginManager, current_user
from flask_admin import Admin
import os, sys
# from flask_permissions.core import Permissions


# app = Flask(__name__)
# app.config.from_object('config')
# db = SQLAlchemy(app)
# login_manager = LoginManager()
# login_manager.init_app(app)
# admin = Admin(app)
# oauth_credentials = app.config['OAUTH_CREDENTIALS']


# from app.evaluation import bp as eval_bp

# app.register_blueprint(eval_bp, url_prefix='/evaluation')

# from app import views, models, admin#, perms

db = SQLAlchemy()
login_manager = LoginManager()
admin = Admin()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    
    register_extensions(app)
    register_blueprints(app)
    
    return app

def register_extensions(app):
    
    db.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)
    
    
def register_blueprints(app):
    
    from app.evaluation import bp as eval_bp
        
    app.register_blueprint(eval_bp, url_prefix='/evaluation')
    
    
    
app = create_app()

from app import views, models, admin#, perms


# perms = Permissions(app, db, current_user)
# user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
# security = Security(app, user_datastore)
