from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_oauthlib.client import OAuth
from flask_security import Security, SQLAlchemyUserDatastore
from flask_admin import Admin

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
oauth = OAuth(app)
admin = Admin(app)
oauth_credentials = app.config['OAUTH_CREDENTIALS']


from app import views, models, admin, oauth


# print(oauth)
# print(admin)

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)
#
# # @app.before_first_request
# def before_frist_request():
#
#     user_datastore.find_or_create_role(name='admin', description='Administrator')
#     user_datastore.find_or_create_role(name='end-user', description='End User')
#
#     # make sure to encrypt passwords later
#     # encrypted_password = utils.encrypt_password('password')
#     if not user_datastore.get_user('someone@test.com'):
#         user_datastore.create_user(email='someone@test.com', password='password')
#     if not user_datastore.get_user('admin@test.com'):
#         user_datastore.create_user(email='admin@test.com', password='password')
#
#     db.session.commit()
#
#     user_datastore.add_role_to_user('someone@test.com', 'end-user')
#     user_datastore.add_role_to_user('admin@test.com', 'admin')
#     db.session.commit()
