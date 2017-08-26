from app import db, app
# from flask_security import UserMixin, RoleMixin  # Use for Roles later on.
from flask_login import UserMixin
import datetime
from sqlalchemy.sql import func
from itsdangerous import URLSafeTimedSerializer

login_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])



##################################
# Models for User Definition
##################################

roles_users = db.Table('roles_users',
db.Column('user_id', db.INTEGER, db.ForeignKey('user.id')),
db.Column('role_id', db.INTEGER, db.ForeignKey('role.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.INTEGER, primary_key=True)
    first_name = db.Column(db.VARCHAR(256))
    last_name = db.Column(db.VARCHAR(256))
    email = db.Column(db.VARCHAR(256), index=True, unique=True)
    password = db.Column(db.VARCHAR(256))
    status = db.Column(db.VARCHAR(15), default='active')
    calendar_access = db.Column(db.SMALLINT(), default=0)
    confirmed_at = db.Column(db.DATETIME())
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    therapist = db.relationship('Therapist', backref='user', uselist=False)
    role_id = db.Column(db.INTEGER, db.ForeignKey('role.id'), default=3)
    # roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User %r>' % (self.email)

    def get_auth_token(self):
        cookie_data = [str(self.id), self.password]
        print('created cookie', cookie_data)
        return login_serializer.dumps(cookie_data)


class Role(db.Model): #, RoleMixin):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55), unique=True)
    description = db.Column(db.VARCHAR(256))
    users = db.relationship('User', backref='role', uselist=False)

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '<role %r>' % (self.name)

class Therapist(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    status = db.Column(db.VARCHAR(15), default='active')
    calendar_credentials = db.Column(db.Text)
    evals = db.relationship('ClientEval', backref='therapist', lazy='dynamic')
    clients = db.relationship('Client', backref='therapist', lazy='dynamic')
    appts = db.relationship('ClientAppt', backref='therapist', lazy='dynamic')

########################################
#  Models for Company and RC Definitions
########################################

class RegionalCenter(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    rc_id = db.Column(db.INTEGER)
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    name = db.Column(db.VARCHAR(55))
    appt_reference_name = db.Column(db.VARCHAR(55))
    address = db.Column(db.VARCHAR(255))
    city = db.Column(db.VARCHAR(55))
    state = db.Column(db.VARCHAR(10), default='CA')
    zipcode = db.Column(db.VARCHAR(15))
    primary_contact_name = db.Column(db.VARCHAR(55))
    primary_contact_phone = db.Column(db.VARCHAR(55))
    primary_contact_email = db.Column(db.VARCHAR(55))
    clients = db.relationship('Client', backref='regional_center', lazy='dynamic')
    billing_files = db.relationship('BillingXml', backref='regional_center', lazy='dynamic')
    appt_types = db.relationship('ApptType', backref='regional_center', lazy='dynamic')

class Company(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    address = db.Column(db.VARCHAR(255))
    city = db.Column(db.VARCHAR(55))
    state = db.Column(db.VARCHAR(10), default='CA')
    zipcode = db.Column(db.VARCHAR(15))
    vendor_id = db.Column(db.VARCHAR(55))
    therapists = db.relationship('Therapist', backref='company', lazy='dynamic')
    regional_centers = db.relationship('RegionalCenter', backref='company', lazy='dynamic')
    users = db.relationship('User', backref='company', lazy='dynamic')

#########################################
# Models for Client Definition
#########################################

class Client(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    first_name = db.Column(db.VARCHAR(255))
    last_name = db.Column(db.VARCHAR(255))
    birthdate = db.Column(db.DATETIME)
    uci_id = db.Column(db.INTEGER)
    address = db.Column(db.VARCHAR(255))
    city = db.Column(db.VARCHAR(55))
    state = db.Column(db.VARCHAR(10))
    zipcode = db.Column(db.VARCHAR(15))
    phone = db.Column(db.VARCHAR(15))
    gender = db.Column(db.VARCHAR(10))
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    status = db.Column(db.VARCHAR(15), default='active')
    # created_date = db.Column(db.DATETIME, default=func.now())
    auths = db.relationship('ClientAuth', backref='client', lazy='dynamic')
    evals = db.relationship('ClientEval', backref='client', lazy='dynamic')
    appts = db.relationship('ClientAppt', backref='client', lazy='dynamic')

    def __repr__(self):
        return '<client: %r %r>' %(self.first_name, self.last_name)


###########################################
#  Models for evals
###########################################

class EvalQuestion(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    subtest_id = db.Column(db.INTEGER, db.ForeignKey('eval_subtest.id'))
    question_cat = db.Column(db.VARCHAR(256))
    question_num = db.Column(db.INTEGER)
    question = db.Column(db.VARCHAR(256))
    report_text = db.Column(db.VARCHAR(256))

    def __repr__(self):
        return '<quest %r>' % (self.question)

class ClientEvalAnswer(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_eval_id = db.Column(db.INTEGER, db.ForeignKey('client_eval.id'))
    eval_question_id = db.Column(db.INTEGER, db.ForeignKey('eval_question.id'))
    answer = db.Column(db.SMALLINT())
    question = db.relationship('EvalQuestion', uselist=False)

eval_subtest_lookup = db.Table('eval_subtest_lookup',
                        db.Column('client_eval_id', db.INTEGER, db.ForeignKey('client_eval.id')),
                        db.Column('subtest_id', db.INTEGER, db.ForeignKey('eval_subtest.id')),
                        db.PrimaryKeyConstraint('client_eval_id', 'subtest_id'))

class ClientEval(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))   #Add if other therapists do Evals
    created_date = db.Column(db.DATETIME)
    answers = db.relationship('ClientEvalAnswer', backref='eval', lazy='dynamic')
    subtests = db.relationship('EvalSubtest', secondary=eval_subtest_lookup)

class EvalSubtest(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    eval_id = db.Column(db.INTEGER, db.ForeignKey('evaluation.id'))
    eval_subtest_id = db.Column(db.INTEGER)
    name = db.Column(db.VARCHAR(50))
    questions = db.relationship('EvalQuestion', backref='subtest', lazy='dynamic')

class ReportSectionTemplate(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    subtest_id = db.Column(db.INTEGER, db.ForeignKey('eval_subtest.id'))
    section_summary = db.Column(db.TEXT)
    section_detail = db.Column(db.TEXT)
    subtest = db.relationship('EvalSubtest', backref='report_section', uselist=False)

class Evaluation(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    test_seq = db.Column(db.VARCHAR(255))
    subtests = db.relationship('EvalSubtest', backref='eval', lazy='dynamic')

    def __repr__(self):
        return '<Eval: %r Seq: %r>' %(self.name, self.test_seq)

##################################
#  Models for Authorizations
##################################

class ClientAuth(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    auth_start_date = db.Column(db.DATETIME)
    auth_end_date = db.Column(db.DATETIME)
    auth_id = db.Column(db.INTEGER)
    is_eval_only = db.Column(db.SMALLINT(), default=0)
    monthly_visits = db.Column(db.INTEGER)
    status = db.Column(db.VARCHAR(10), default='active')
    created_date = db.Column(db.DATETIME)

#####################################
# Models with Client Appts
#####################################

class ClientAppt(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    start_datetime = db.Column(db.DATETIME)
    end_datetime = db.Column(db.DATETIME)
    appointment_type = db.Column(db.VARCHAR(15)) # Need to remove and add id in Calendar grab
    appt_type_id = db.Column(db.INTEGER, db.ForeignKey('appt_type.id'))
    note = db.relationship('ClientApptNote', backref='appt', uselist=False)
    cancelled = db.Column(db.SMALLINT(), default=0)
    mileage = db.Column(db.INTEGER, default=0)
    billing_xml_id = db.Column(db.INTEGER, db.ForeignKey('billing_xml.id'))
    billing_notes = db.relationship('BillingNote', backref='appt', lazy='dynamic')
    __table_args__ = (db.UniqueConstraint('therapist_id', 'client_id', 'start_datetime', name='_therapist_client_appt_unique'),)

    def __repr__(self):
        return 'Appt for: %r at %r' %(self.client_id, self.start_datetime)

class ApptType(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(20))
    service_code = db.Column(db.INTEGER)
    service_type_code = db.Column(db.VARCHAR(15))
    rate = db.Column(db.Numeric(precision=10, scale=2))
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    appts = db.relationship('ClientAppt', backref='appt_type', lazy='dynamic')

class ClientApptNote(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_appt_id= db.Column(db.INTEGER, db.ForeignKey('client_appt.id'))
    note = db.Column(db.Text)
    created_date = db.Column(db.DATETIME)

####################################
# Models for Billing
####################################

class BillingXml(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    billing_month = db.Column(db.DATETIME)
    file_link = db.Column(db.VARCHAR(255))
    appts = db.relationship('ClientAppt', backref='billing_invoice', lazy='dynamic')
    created_date = db.Column(db.DATETIME)
    notes = db.relationship('BillingNote', backref='billing_invoice', lazy='dynamic')

class BillingNote(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    billing_xml_id = db.Column(db.INTEGER, db.ForeignKey('billing_xml.id'))
    client_appt_id= db.Column(db.INTEGER, db.ForeignKey('client_appt.id'))
    note = db.Column(db.Text)
    created_date = db.Column(db.DATETIME)
