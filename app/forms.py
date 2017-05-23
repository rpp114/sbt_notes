from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SelectField
from wtforms.validators import DataRequired, InputRequired
from wtforms.fields.html5 import DateField
# from models import

class LoginForm(FlaskForm):
  openid = StringField('openid', validators=[DataRequired()])
  remember_me = BooleanField('remember_me', default=False)

class ClientInfoForm(FlaskForm):
  first_name = StringField('first_name', validators=[DataRequired()])
  last_name = StringField('last_name', validators=[DataRequired()])
  birthdate = DateField('birthdate', validators=[DataRequired()])
  uci_id = StringField('uci_id', validators=[DataRequired()])
  address = StringField('address', validators=[DataRequired()])
  city = StringField('city', validators=[DataRequired()])
  state = StringField('state', validators=[DataRequired()], default='CA')
  zipcode = StringField('zipcode', validators=[DataRequired()])
  phone = StringField('phone', validators=[DataRequired()])
  regional_center_id = SelectField('regional_center_id', coerce=int, validators=[DataRequired()])
  therapist_id = SelectField('therapist_id', coerce=int, validators=[DataRequired()])
