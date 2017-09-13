from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SelectField, RadioField, SelectMultipleField, widgets, PasswordField, SubmitField
from wtforms.validators import DataRequired, InputRequired, EqualTo, Email
from wtforms.fields.html5 import DateField
# from wtforms_components import TimeField
# from models import

class LoginForm(FlaskForm):
  email = StringField('email', validators=[DataRequired(), Email()])
  password = PasswordField('password', validators=[DataRequired()])
  remember_me = BooleanField('remember_me', default=False)
  submit = SubmitField('Sign In')

class PasswordChangeForm(FlaskForm):
  password = PasswordField('password', validators=[DataRequired(), EqualTo('confirm', message='Come On Man!  Make them Match!')])
  confirm = PasswordField('confirm')

class UserInfoForm(FlaskForm):
  first_name = StringField('first_name',  default='First Name')
  last_name = StringField('last_name',  default='Last Name')
  email = StringField('email')
  role_id = SelectField('role_id', coerce=int)
  calendar_access = BooleanField('cal_access', default=False)
  therapist_id = SelectField('therapist_id', coerce=int)

class NewUserInfoForm(FlaskForm):
  first_name = StringField('first_name', validators=[DataRequired()])
  last_name = StringField('last_name', validators=[DataRequired()])
  email = StringField('email', validators=[DataRequired()])
  role_id = SelectField('role_id', coerce=int)
  calendar_access = BooleanField('cal_access', default=False)
  password = PasswordField('password', validators=[DataRequired(), EqualTo('confirm', message='Come On Man!  Make them Match!')])
  confirm = PasswordField('confirm')


class ClientInfoForm(FlaskForm):
  first_name = StringField('first_name', validators=[DataRequired()])
  last_name = StringField('last_name', validators=[DataRequired()])
  birthdate = StringField('birthdate', validators=[DataRequired()])
  uci_id = StringField('uci_id', validators=[DataRequired()])
  address = StringField('address', validators=[DataRequired()])
  city = StringField('city', validators=[DataRequired()])
  state = StringField('state', validators=[DataRequired()], default='CA')
  zipcode = StringField('zipcode', validators=[DataRequired()])
  phone = StringField('phone', validators=[DataRequired()])
  regional_center_id = SelectField('regional_center_id', coerce=int, validators=[DataRequired()])
  therapist_id = SelectField('therapist_id', coerce=int, validators=[DataRequired()])
  gender = SelectField('gender', choices=[('M', 'Male'), ('F','Female')], validators=[DataRequired()])

# Removed to reformat form.  Doesn't use form class anymore.
# class MultiCheckboxField(SelectMultipleField):
#   widget = widgets.ListWidget(prefix_label=False)
#   option_widget = widgets.CheckboxInput()
#
# class NewEvalForm(FlaskForm):
#   # eval_type_id = RadioField('eval_type_id', coerce=int)
#   subtest_id = MultiCheckboxField('subtest_id', coerce=int)

class ClientNoteForm(FlaskForm):
  notes = StringField('notes', widget=widgets.TextArea()) #, height_="48")
  cancelled = BooleanField('cancelled', default=False)
  approved = BooleanField('approved', default=True)
  appt_date = StringField('appt_date')
  appt_time = StringField('appt_time')
  intern_id = SelectField('intern_id', coerce=int)

class ClientAuthForm(FlaskForm):
  auth_id = StringField('auth_id', validators=[DataRequired()])
  auth_start_date = StringField('auth_start_date', validators=[DataRequired()])
  auth_end_date = StringField('auth_end_date', validators=[DataRequired()])
  is_eval_only = BooleanField('is_eval_only')
  monthly_visits = StringField('monthly_visits', validators=[DataRequired()], default='1')

class RegionalCenterForm(FlaskForm):
  name = StringField('name')
  appt_reference_name = StringField('appt_reference_name')
  address = StringField('address')
  city = StringField('city')
  state = StringField('state', default='CA')
  zipcode = StringField('zipcode')
  rc_id = StringField('rc_id')
  primary_contact_name = StringField('primary_contact_name')
  primary_contact_phone = StringField('primary_contact_phone')
  primary_contact_email = StringField('primary_contact_email')

class CompanyForm(FlaskForm):
  name = StringField('name', validators=[DataRequired()])
  address = StringField('address')
  city = StringField('city')
  state = StringField('state', default='CA')
  zipcode = StringField('zipcode')
  vendor_id = StringField('vendor_id', validators=[DataRequired()])

class ApptTypeForm(FlaskForm):
  name = StringField('name')
  service_code = StringField('service_code')
  service_type_code = StringField('service_type_code')
  rate = StringField('rate')

class DateSelectorForm(FlaskForm):
  start_date = StringField('start_date')
  end_date = StringField('end_date')
