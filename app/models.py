from app import db#, app
# from flask_security import UserMixin, RoleMixin  # Use for Roles later on.
from flask_login import UserMixin
import datetime
from sqlalchemy.sql import func
# For future Encryption of Data
# from sqlalchemy_utils import EncryptedType, force_auto_coercion
# from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
#
# force_auto_coercion()

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
    session_token = db.Column(db.VARCHAR(256), unique=True)
    confirmed_at = db.Column(db.DATETIME())
    first_time_login = db.Column(db.SMALLINT(), default=1)
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    therapist = db.relationship('Therapist', backref='user', uselist=False)
    intern = db.relationship('Intern', backref='user', uselist=False)
    role_id = db.Column(db.INTEGER, db.ForeignKey('role.id'), default=3)
    notes = db.relationship('ClientApptNote', backref='user', lazy='dynamic')
    meetings = db.relationship('CompanyMeeting', secondary='meeting_user_lookup')
    # roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User %r>' % (self.email)

    def get_id(self):
        return str(self.session_token)


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

class Intern(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    notes = db.relationship('ClientApptNote', backref='intern', lazy='dynamic')

class Therapist(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    status = db.Column(db.VARCHAR(15), default='active')
    calendar_credentials = db.Column(db.Text)
    signature = db.Column(db.Text)
    evals = db.relationship('ClientEval', backref='therapist', lazy='dynamic')
    clients = db.relationship('Client', backref='therapist', lazy='dynamic')
    appts = db.relationship('ClientAppt', backref='therapist', lazy='dynamic')
    interns = db.relationship('Intern', backref='therapist', lazy='dynamic')

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
    case_workers = db.relationship('CaseWorker', backref='regional_center', lazy='dynamic')
    teams = db.relationship('RegionalCenterTeam', backref='regional_center', lazy='dynamic')

class Company(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    address = db.Column(db.VARCHAR(255))
    city = db.Column(db.VARCHAR(55))
    state = db.Column(db.VARCHAR(10), default='CA')
    zipcode = db.Column(db.VARCHAR(15))
    vendor_id = db.Column(db.VARCHAR(55))
    doc_password = db.Column(db.VARCHAR(55))
    therapists = db.relationship('Therapist', backref='company', lazy='dynamic')
    meetings = db.relationship('CompanyMeeting', backref='company', lazy='dynamic')
    regional_centers = db.relationship('RegionalCenter', backref='company', lazy='dynamic')
    users = db.relationship('User', backref='company', lazy='dynamic')

class CaseWorker(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    regional_center_team_id = db.Column(db.INTEGER, db.ForeignKey('regional_center_team.id'))
    first_name = db.Column(db.VARCHAR(55))
    last_name = db.Column(db.VARCHAR(55))
    email = db.Column(db.VARCHAR(255), default='No Email')
    phone = db.Column(db.VARCHAR(15), default='No Phone Number')
    status = db.Column(db.VARCHAR(15), default='active')
    clients = db.relationship('Client', backref='case_worker', lazy='dynamic')

    def __repr__(self):
        return '<case_worker: %r %r>' %(self.first_name, self.last_name)

class RegionalCenterTeam(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    team_name = db.Column(db.VARCHAR(55))
    first_name = db.Column(db.VARCHAR(55))
    last_name = db.Column(db.VARCHAR(55))
    email = db.Column(db.VARCHAR(255), default='No Email')
    phone = db.Column(db.VARCHAR(15), default='No Phone Number')
    status = db.Column(db.VARCHAR(15), default='active')
    case_workers = db.relationship('CaseWorker', backref='team', lazy='dynamic')

    def __repr__(self):
        return '<case_worker_team: %r>' %(self.team_name)

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
    needs_appt_scheduled =  db.Column(db.SMALLINT(), default=1)
    additional_info = db.Column(db.Text)
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    case_worker_id = db.Column(db.INTEGER, db.ForeignKey('case_worker.id'))
    status = db.Column(db.VARCHAR(15), default='active')
    weeks_premature = db.Column(db.Numeric(precision=10, scale=2))
    auths = db.relationship('ClientAuth', backref='client', lazy='dynamic')
    evals = db.relationship('ClientEval', backref='client', lazy='dynamic')
    appts = db.relationship('ClientAppt', backref='client', lazy='dynamic')
    goals = db.relationship('ClientGoal', backref='client', lazy='dynamic')
    background = db.relationship('ClientBackground', backref='client', uselist=False)

    def __repr__(self):
        return '<client: %r %r>' %(self.first_name, self.last_name)

class ClientBackground(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    additional_hearing_test = db.Column(db.TEXT)
    additional_hearing_test_detail = db.Column(db.TEXT)
    allergies = db.Column(db.TEXT)
    allergies_detail = db.Column(db.TEXT)
    bed_time = db.Column(db.TEXT)
    birth_length = db.Column(db.TEXT)
    birth_weight = db.Column(db.TEXT)
    born_city = db.Column(db.TEXT)
    born_hospital = db.Column(db.TEXT)
    born_state = db.Column(db.TEXT)
    combine_speak = db.Column(db.TEXT)
    concerns = db.Column(db.TEXT)
    crawl = db.Column(db.TEXT)
    current_food = db.Column(db.TEXT)
    current_length = db.Column(db.TEXT)
    current_weight = db.Column(db.TEXT)
    daycare = db.Column(db.TEXT)
    delivery = db.Column(db.TEXT)
    delivery_complications = db.Column(db.TEXT)
    delivery_complications_detail = db.Column(db.TEXT)
    dreams = db.Column(db.TEXT)
    drug_exposure = db.Column(db.TEXT)
    ear_infections = db.Column(db.TEXT)
    family = db.Column(db.TEXT)
    family_schedule = db.Column(db.TEXT)
    feeding_concerns = db.Column(db.TEXT)
    feeding_concerns_detail = db.Column(db.TEXT)
    feeding_skills = db.Column(db.TEXT)
    first_speak = db.Column(db.TEXT)
    follow_up_appt = db.Column(db.TEXT)
    gestation = db.Column(db.TEXT)
    goals = db.Column(db.TEXT)
    history_of_delays = db.Column(db.TEXT)
    history_of_delays_detail = db.Column(db.TEXT)
    hospitalizations = db.Column(db.TEXT)
    hospitalizations_detail = db.Column(db.TEXT)
    how_interact_adults = db.Column(db.TEXT)
    how_interact_children = db.Column(db.TEXT)
    illnesses = db.Column(db.TEXT)
    illnesses_detail = db.Column(db.TEXT)
    immunizations = db.Column(db.TEXT)
    immunizations_detail = db.Column(db.TEXT)
    interaction_ops = db.Column(db.TEXT)
    languages = db.Column(db.TEXT)
    last_seen_appt = db.Column(db.TEXT)
    medical_concerns = db.Column(db.TEXT)
    medical_concerns_detail = db.Column(db.TEXT)
    medications = db.Column(db.TEXT)
    medications_detail = db.Column(db.TEXT)
    milk = db.Column(db.TEXT)
    milk_amount = db.Column(db.TEXT)
    nap_time = db.Column(db.TEXT)
    negative_behavior = db.Column(db.TEXT)
    newborn_hearing_test = db.Column(db.TEXT)
    newborn_hearing_test_detail = db.Column(db.TEXT)
    pediatrician = db.Column(db.TEXT)
    picky_eater = db.Column(db.TEXT)
    pregnancy_complications = db.Column(db.TEXT)
    pregnancy_complications_detail = db.Column(db.TEXT)
    roll = db.Column(db.TEXT)
    sit = db.Column(db.TEXT)
    sleep_thru_night = db.Column(db.TEXT)
    sleep_thru_night_detail = db.Column(db.TEXT)
    specialist = db.Column(db.TEXT)
    specialist_detail = db.Column(db.TEXT)
    strengths = db.Column(db.TEXT)
    surgeries = db.Column(db.TEXT)
    surgeries_detail = db.Column(db.TEXT)
    vision_test = db.Column(db.TEXT)
    vision_test_detail = db.Column(db.TEXT)
    wake_time = db.Column(db.TEXT)
    walk = db.Column(db.TEXT)
    # encrypt_test = db.Column(EncryptedType(db.VARCHAR(255), app.config['SECRET_KEY'],AesEngine))


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
    answers = db.relationship('ClientEvalAnswer', backref='question', lazy='dynamic')

    def __repr__(self):
        return '<quest %r>' % (self.question)

class ClientEvalAnswer(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_eval_id = db.Column(db.INTEGER, db.ForeignKey('client_eval.id'))
    eval_question_id = db.Column(db.INTEGER, db.ForeignKey('eval_question.id'))
    answer = db.Column(db.SMALLINT())

class ClientEvalSubtestLookup(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_eval_id = db.Column(db.INTEGER, db.ForeignKey('client_eval.id'))
    subtest_id = db.Column(db.INTEGER, db.ForeignKey('eval_subtest.id'))
    evals = db.relationship('ClientEval', backref=db.backref('eval_subtests', cascade='all, delete-orphan'))
    subtests = db.relationship('EvalSubtest', backref=db.backref('eval_subtests', cascade='all, delete-orphan'), innerjoin=True, order_by='EvalSubtest.eval_id, EvalSubtest.eval_subtest_id')
    raw_score = db.Column(db.INTEGER)
    scaled_score = db.Column(db.INTEGER)
    age_equivalent = db.Column(db.INTEGER)

class ClientEval(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    client_appt_id = db.Column(db.INTEGER, db.ForeignKey('client_appt.id'))
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    answers = db.relationship('ClientEvalAnswer', backref='eval', lazy='dynamic')
    subtests = db.relationship('EvalSubtest', secondary='client_eval_subtest_lookup', order_by='EvalSubtest.eval_id, EvalSubtest.eval_subtest_id')
    report = db.relationship('EvalReport', backref='eval', uselist=False)

class EvalSubtest(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    eval_id = db.Column(db.INTEGER, db.ForeignKey('evaluation.id'))
    eval_subtest_id = db.Column(db.INTEGER)
    name = db.Column(db.VARCHAR(50))
    description = db.Column(db.TEXT)
    evals = db.relationship('ClientEval', secondary='client_eval_subtest_lookup')
    questions = db.relationship('EvalQuestion', backref='subtest', lazy='dynamic')
    report_sections = db.relationship('ReportSection', backref='subtest', lazy='dynamic')

class Evaluation(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    test_formal_name = db.Column(db.VARCHAR(255))
    description = db.Column(db.TEXT)
    subtests = db.relationship('EvalSubtest', backref='eval', lazy='dynamic')

    def __repr__(self):
        return '<Eval: %r >' %(self.name)

class EvalSubtestStart(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    age = db.Column(db.INTEGER)
    subtest_id = db.Column(db.INTEGER)
    start_point = db.Column(db.INTEGER)

class EvalSubtestScaledScore(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    from_age = db.Column(db.INTEGER)
    to_age = db.Column(db.INTEGER)
    subtest_id = db.Column(db.INTEGER)
    raw_score = db.Column(db.INTEGER)
    scaled_score = db.Column(db.INTEGER)

class EvalSubtestAgeEquivalent(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    subtest_id = db.Column(db.INTEGER)
    raw_score = db.Column(db.INTEGER)
    age_equivalent = db.Column(db.INTEGER)

##################################
#  Models for Evaluation Reports
##################################

class EvalReport(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_eval_id = db.Column(db.INTEGER, db.ForeignKey('client_eval.id'))
    file_name = db.Column(db.VARCHAR(255))
    sections = db.relationship('ReportSection', backref='report', lazy='dynamic')

class ReportSection(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    eval_report_id = db.Column(db.INTEGER, db.ForeignKey('eval_report.id'))
    eval_subtest_id = db.Column(db.INTEGER, db.ForeignKey('eval_subtest.id'), nullable=True)
    section_order_id = db.Column(db.INTEGER)
    name = db.Column(db.VARCHAR(50))
    section_title = db.Column(db.VARCHAR(50))
    text = db.Column(db.TEXT)

    def __repr__(self):
        return '<section %r>' % (self.name)

##################################
#  Models for Client Goals
##################################

class ClientGoal(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    goal = db.Column(db.VARCHAR(255))
    goal_status = db.Column(db.VARCHAR(55))
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)


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
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)

########################################
# Models for Company Meetings
########################################

class CompanyMeeting(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    start_datetime = db.Column(db.DATETIME)
    end_datetime = db.Column(db.DATETIME)
    description = db.Column(db.TEXT)
    users = db.relationship('User', secondary='meeting_user_lookup')

class MeetingUserLookup(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    meeting_id = db.Column(db.INTEGER, db.ForeignKey('company_meeting.id'))
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    users = db.relationship('CompanyMeeting', backref=db.backref('meeting_users', cascade='all, delete-orphan'))
    meetings = db.relationship('User', backref=db.backref('meeting_users', cascade='all, delete-orphan'))
    attended = db.Column(db.SMALLINT(), default=1)

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
    location = db.Column(db.VARCHAR(255))
    mileage = db.Column(db.INTEGER, default=0)
    billing_xml_id = db.Column(db.INTEGER, db.ForeignKey('billing_xml.id'))
    billing_notes = db.relationship('BillingNote', backref='appt', lazy='dynamic')
    eval = db.relationship('ClientEval', backref='appt', uselist=False)
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
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    approved = db.Column(db.SMALLINT(), default=0)
    note = db.Column(db.Text)
    intern_id = db.Column(db.INTEGER, db.ForeignKey('intern.id'))
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)

####################################
# Models for Billing
####################################

class BillingXml(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    billing_month = db.Column(db.DATETIME)
    file_name = db.Column(db.VARCHAR(255))
    appts = db.relationship('ClientAppt', backref='billing_invoice', lazy='dynamic')
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    notes = db.relationship('BillingNote', backref='billing_invoice', lazy='dynamic')

class BillingNote(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    billing_xml_id = db.Column(db.INTEGER, db.ForeignKey('billing_xml.id'))
    client_appt_id= db.Column(db.INTEGER, db.ForeignKey('client_appt.id'))
    note = db.Column(db.Text)
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    
class FileUploadDir(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    file_dir = db.Column(db.VARCHAR(25))
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
