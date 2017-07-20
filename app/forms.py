from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SelectField, RadioField, SelectMultipleField, widgets, PasswordField, SubmitField
from wtforms.validators import DataRequired, InputRequired, EqualTo, Email
from wtforms.fields.html5 import DateField
# from models import

class LoginForm(FlaskForm):
  email = StringField('email', validators=[DataRequired(), Email()])
  password = PasswordField('password', validators=[DataRequired()])
  remember_me = BooleanField('remember_me', default=False)
  submit = SubmitField('Sign In')

class PasswordChangeForm(FlaskForm):
  old_password = PasswordField('old_password', validators=[DataRequired()])
  new_password = PasswordField('new_password', validators=[DataRequired(), EqualTo('confirm', message='Come On Man!  Make them Match!')])
  confirm = PasswordField('confirm')

class UserInfoForm(FlaskForm):
  first_name = StringField('first_name', validators=[DataRequired()], default='First Name')
  last_name = StringField('last_name', validators=[DataRequired()], default='Last Name')
  email = StringField('email', validators=[DataRequired()])
  calendar_access = BooleanField('cal_access', default=False)

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
  gender = SelectField('gender', choices=[('M', 'Male'), ('F','Female')], validators=[DataRequired()])

class MultiCheckboxField(SelectMultipleField):
  widget = widgets.ListWidget(prefix_label=False)
  option_widget = widgets.CheckboxInput()

class NewEvalForm(FlaskForm):
  # eval_type_id = RadioField('eval_type_id', coerce=int)
  subtest_id = MultiCheckboxField('subtest_id', coerce=int)

class ClientNoteForm(FlaskForm):
  notes = StringField('notes', widget=widgets.TextArea()) #, height_="48")

class ClientAuthForm(FlaskForm):
  auth_id = StringField('auth_id', validators=[DataRequired()])
  auth_start_date = DateField('auth_start_date', validators=[DataRequired()])
  auth_end_date = DateField('auth_end_date', validators=[DataRequired()])
  monthly_visits = StringField('monthly_visits', validators=[DataRequired()], default='1')
