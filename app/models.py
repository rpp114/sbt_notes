from sbt_notes.app import db#, app
# from flask_security import UserMixin, RoleMixin  # Use for Roles later on.
from flask_login import UserMixin
import datetime
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import MEDIUMTEXT

from sbt_notes.jobs.encryption_handler import decrypt_text, encrypt_text, encrypt_file, decrypt_file


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
    session_token = db.Column(db.VARCHAR(512), unique=True)
    confirmed_at = db.Column(db.DATETIME())
    first_time_login = db.Column(db.SMALLINT(), default=1)
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    therapist = db.relationship('Therapist', backref='user', uselist=False)
    intern = db.relationship('Intern', backref='user', uselist=False)
    role_id = db.Column(db.INTEGER, db.ForeignKey('role.id'), default=3)
    notes = db.relationship('ClientApptNote', backref='user', lazy='dynamic')
    meeting_users = db.relationship('MeetingUserLookup', back_populates='user', cascade='all, delete-orphan')
    meetings = db.relationship('CompanyMeeting', secondary='meeting_user_lookup', viewonly=True)
    expenses = db.relationship('UserExpense', backref='user', lazy='dynamic')
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
    calendar_credentials = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    signature = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    evals = db.relationship('ClientEval', backref='therapist', lazy='dynamic')
    evaluations = db.relationship('ClientEvaluation', backref='therapist', lazy='dynamic')
    clients = db.relationship('Client', backref='therapist', lazy='dynamic')
    appts = db.relationship('ClientAppt', backref='therapist', lazy='dynamic')
    interns = db.relationship('Intern', backref='therapist', lazy='dynamic')
    
    
########################################
#  Models for User Expenses
########################################

class UserExpense(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    date = db.Column(db.DATETIME)
    description = db.Column(db.VARCHAR(255))
    amount = db.Column(db.Numeric(precision=10, scale=2))
    filename =  db.Column(db.VARCHAR(255))
    

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
    middle_name = db.Column(db.VARCHAR(255))
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
    additional_info = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    case_worker_id = db.Column(db.INTEGER, db.ForeignKey('case_worker.id'))
    status = db.Column(db.VARCHAR(15), default='active')
    weeks_premature = db.Column(db.Numeric(precision=10, scale=2))
    auths = db.relationship('ClientAuth', backref='client', lazy='dynamic')
    evals = db.relationship('ClientEval', backref='client', lazy='dynamic')
    evaluations = db.relationship('ClientEvaluation', backref='client', lazy='dynamic')
    appts = db.relationship('ClientAppt', backref='client', lazy='dynamic')
    goals = db.relationship('ClientGoal', backref='client', lazy='dynamic')
    background = db.relationship('ClientBackground', backref='client', uselist=False)
    care_giver = db.Column(db.VARCHAR(255))
    files = db.relationship('ClientFile', backref='client', lazy='dynamic')

    def __repr__(self):
        return '<client: %r %r>' %(self.first_name, self.last_name)
        
    @property
    def full_name(self):
        return ' '.join([self.first_name, self.middle_name, self.last_name])

class ClientBackground(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    additional_hearing_test = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    additional_hearing_test_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    allergies = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    allergies_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    bed_time = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    birth_length = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    birth_weight = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    born_city = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    born_hospital = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    born_state = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    combine_speak = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    concerns = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    crawl = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    current_food = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    current_length = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    current_weight = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    daycare = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    delivery = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    delivery_complications = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    delivery_complications_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    dreams = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    drug_exposure = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    ear_infections = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    family = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    family_schedule = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    feeding_concerns = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    feeding_concerns_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    feeding_skills = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    first_speak = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    follow_up_appt = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    gestation = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    goals = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    history_of_delays = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    history_of_delays_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    hospitalizations = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    hospitalizations_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    how_interact_adults = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    how_interact_children = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    illnesses = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    illnesses_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    immunizations = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    immunizations_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    interaction_ops = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    languages = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    last_seen_appt = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    medical_concerns = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    medical_concerns_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    medications = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    medications_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    milk = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    milk_amount = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    nap_time = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    negative_behavior = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    newborn_hearing_test = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    newborn_hearing_test_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    pediatrician = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    picky_eater = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    pregnancy_complications = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    pregnancy_complications_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    roll = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    sit = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    sleep_thru_night = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    sleep_thru_night_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    specialist = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    specialist_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    strengths = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    surgeries = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    surgeries_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    vision_test = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    vision_test_detail = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    wake_time = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    walk = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
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
    eval = db.relationship('ClientEval', back_populates='eval_subtests')
    subtest = db.relationship('EvalSubtest', back_populates='eval_subtests', innerjoin=True, order_by='EvalSubtest.eval_id, EvalSubtest.eval_subtest_id')
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
    eval_subtests = db.relationship('ClientEvalSubtestLookup', back_populates='eval', cascade='all, delete-orphan')
    subtests = db.relationship('EvalSubtest', secondary='client_eval_subtest_lookup', viewonly=True, order_by='EvalSubtest.eval_id, EvalSubtest.eval_subtest_id')
    report = db.relationship('EvalReport', backref='eval', uselist=False)

class EvalSubtest(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    eval_id = db.Column(db.INTEGER, db.ForeignKey('evaluation.id'))
    eval_subtest_id = db.Column(db.INTEGER)
    name = db.Column(db.VARCHAR(50))
    description = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    eval_subtests = db.relationship('ClientEvalSubtestLookup', back_populates='subtest', cascade='all, delete-orphan')
    evals = db.relationship('ClientEval', secondary='client_eval_subtest_lookup', viewonly=True)
    questions = db.relationship('EvalQuestion', backref='subtest', lazy='dynamic')
    report_sections = db.relationship('ReportSection', backref='subtest', lazy='dynamic')

class Evaluation(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    test_formal_name = db.Column(db.VARCHAR(255))
    description = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
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
    text = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    encrypted_text = db.Column(db.LargeBinary)
    nonce = db.Column(db.LargeBinary, nullable=False)
    encrypted_dek = db.Column(db.LargeBinary, nullable=False)
    key_version = db.Column(db.String(255))

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
    billing_code = db.Column(db.VARCHAR(10))


########################################
# Models for Company Meetings
########################################

class CompanyMeeting(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    start_datetime = db.Column(db.DATETIME)
    end_datetime = db.Column(db.DATETIME)
    description = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    meeting_users = db.relationship('MeetingUserLookup',back_populates='meeting', cascade='all, delete-orphan')
    users = db.relationship('User', secondary='meeting_user_lookup', viewonly=True)

class MeetingUserLookup(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    meeting_id = db.Column(db.INTEGER, db.ForeignKey('company_meeting.id'))
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='meeting_users')
    meeting = db.relationship('CompanyMeeting', back_populates='meeting_users')
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
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    billing_notes = db.relationship('BillingNote', backref='appt', lazy='dynamic')
    eval = db.relationship('ClientEval', backref='appt', uselist=False)
    evaluation = db.relationship('ClientEvaluation', backref='appt', uselist=False)
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
    note = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    encrypted_note = db.Column(db.LargeBinary)
    intern_id = db.Column(db.INTEGER, db.ForeignKey('intern.id'))
    text_nonce = db.Column(db.LargeBinary, nullable=False)
    encrypted_dek = db.Column(db.LargeBinary, nullable=False)
    dek_nonce = db.Column(db.LargeBinary, nullable=False)
    key_version = db.Column(db.INTEGER)
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    
    @property
    def decrypted_note(self):
        try:
            return decrypt_text(self, 'encrypted_note')
        except:
            return f"Could not decrypt note for appt_note_id: {self.id}."
    
    def encrypt_note(self, plaintext):
        encrypted_note_data = encrypt_text(plaintext)
        self.encrypted_note = encrypted_note_data['encrypted_text']
        self.text_nonce = encrypted_note_data['text_nonce']
        self.encrypted_dek = encrypted_note_data['encrypted_dek']
        self.dek_nonce = encrypted_note_data['dek_nonce']
        self.key_version = encrypted_note_data['key_version']
        

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
    note = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    
    
####################################
# Models for File Handling
####################################

class FileUploadDir(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    file_dir = db.Column(db.VARCHAR(25))
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    
class ClientFile(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    file_upload_dir_id = db.Column(db.INTEGER, db.ForeignKey('file_upload_dir.id'))
    encrypted_filename = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'), nullable=False)
    readable_filename = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'), nullable=False)
    file_nonce = db.Column(db.LargeBinary, nullable=False)
    encrypted_dek = db.Column(db.LargeBinary, nullable=False)
    dek_nonce = db.Column(db.LargeBinary, nullable=False)
    key_version = db.Column(db.INTEGER)
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    folder = db.relationship('FileUploadDir', backref='file')
    status = db.Column(db.VARCHAR(10), default='active')
    
        
    @property
    def decrypted_file(self):
        return decrypt_file(self)
    
    def encrypt_file(self, file):
        encrypted_file_data = encrypt_file(file)
        self.encrypted_filename = encrypted_file_data['encrypted_filename']
        self.file_nonce = encrypted_file_data['file_nonce']
        self.encrypted_dek = encrypted_file_data['encrypted_dek']
        self.dek_nonce = encrypted_file_data['dek_nonce']
        self.key_version = encrypted_file_data['key_version']

####################################
# Models for Audit Logging
####################################
 
class UserActivityLog(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    user_id = db.Column(db.INTEGER)
    action = db.Column(db.VARCHAR(50))
    resource_type = db.Column(db.VARCHAR(50))
    resource_id = db.Column(db.VARCHAR(50))
    ip_address = db.Column(db.VARCHAR(50))
    user_agent = db.Column(MEDIUMTEXT(collation='utf8mb4_unicode_ci'))
    created_at = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    previous_hash = db.Column(db.CHAR(64))
    current_hash = db.Column(db.CHAR(64))
    

