from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, DateField, IntegerField
from wtforms.validators import DataRequired
# from models

class LoginForm(FlaskForm):
  openid = StringField('openid', validators=[DataRequired()])
  remember_me = BooleanField('remember_me', default=False)
