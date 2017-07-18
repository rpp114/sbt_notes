from app import db
from flask_security import UserMixin, RoleMixin
import datetime
from sqlalchemy.sql import func

roles_users = db.Table('roles_users',
db.Column('user_id', db.INTEGER, db.ForeignKey('user.id')),
db.Column('role_id', db.INTEGER, db.ForeignKey('role.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.INTEGER, primary_key=True)
    first_name = db.Column(db.VARCHAR(256))
    last_name = db.Column(db.VARCHAR(256))
    email = db.Column(db.VARCHAR(256), index=True, unique=True)
    password = db.Column(db.VARCHAR(55))
    status = db.Column(db.VARCHAR(15), default='active')
    calendar_access = db.Column(db.SMALLINT(), default=0)
    confirmed_at = db.Column(db.DATETIME())
    calendar_credentials = db.Column(db.Text)
    therapist = db.relationship('Therapist', backref='user', lazy='dynamic')
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % (self.email)

class Post(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    body = db.Column(db.VARCHAR(256))
    timestamp = db.Column(db.DATETIME)
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<post %r>' % (self.body)

class Role(db.Model, RoleMixin):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55), unique=True)
    description = db.Column(db.VARCHAR(256))

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '<role %r>' % (self.name)

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
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    created_date = db.Column(db.DATETIME)
    answers = db.relationship('ClientEvalAnswer', backref='eval', lazy='dynamic')
    subtests = db.relationship('EvalSubtest', secondary=eval_subtest_lookup)

class RegionalCenter(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    address = db.Column(db.VARCHAR(255))
    city = db.Column(db.VARCHAR(55))
    state = db.Column(db.VARCHAR(10), default='CA')
    zipcode = db.Column(db.VARCHAR(15))
    primary_contact_name = db.Column(db.VARCHAR(55))
    primary_contact_phone = db.Column(db.VARCHAR(55))
    clients = db.relationship('Client', backref='regional_center', lazy='dynamic')


class Therapist(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    user_id = db.Column(db.INTEGER, db.ForeignKey('user.id'))
    company_id = db.Column(db.INTEGER, db.ForeignKey('company.id'))
    status = db.Column(db.VARCHAR(15), default='active')
    evals = db.relationship('ClientEval', backref='therapist', lazy='dynamic')
    clients = db.relationship('Client', backref='therapist', lazy='dynamic')
    appts = db.relationship('ClientAppt', backref='therapist', lazy='dynamic')

class Company(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    city = db.Column(db.VARCHAR(55))
    state = db.Column(db.VARCHAR(10), default='CA')
    zipcode = db.Column(db.VARCHAR(15))
    therapists = db.relationship('Therapist', backref='company', lazy='dynamic')

class ClientAuth(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    auth_start_date = db.Column(db.DATETIME)
    auth_end_date = db.Column(db.DATETIME)
    auth_id = db.Column(db.INTEGER)
    monthly_visits = db.Column(db.INTEGER)
    created_date = db.Column(db.DATETIME)

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

# Need to build a 1:1 relationship with notes:appts


class ClientAppt(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    start_datetime = db.Column(db.DATETIME)
    end_datetime = db.Column(db.DATETIME)
    appointment_type = db.Column(db.VARCHAR(15))
    note = db.relationship('ClientApptNote', backref='appt', uselist=False)
    __table_args__ = (db.UniqueConstraint('therapist_id', 'start_datetime', name='_therapist_appt_unique'),)

    def __repr__(self):
        return 'Appt for: %r at %r' %(self.client_id, self.start_datetime)

# client_appt_note = db.Table('client_appt_note',
#                         db.Column('client_appt_id', db.INTEGER, db.ForeignKey('client_appt.id')),
#                         db.Column('note', db.Text),
#                         db.Column('created_date', db.DATETIME))


class ClientApptNote(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_appt_id= db.Column(db.INTEGER, db.ForeignKey('client_appt.id'))
    note = db.Column(db.Text)
    created_date = db.Column(db.DATETIME)
