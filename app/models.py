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
    nickname = db.Column(db.VARCHAR(256), index=True, unique=True)
    email = db.Column(db.VARCHAR(256), index=True, unique=True)
    password = db.Column(db.VARCHAR(55))
    active = db.Column(db.SMALLINT())
    confirmed_at = db.Column(db.DATETIME())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % (self.nickname)

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

class EvalQuestions(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    eval_type_id = db.Column(db.INTEGER, db.ForeignKey('evaluations.id'))
    evaluation = db.Column(db.VARCHAR(256))
    subtest = db.Column(db.VARCHAR(256))
    question_cat = db.Column(db.VARCHAR(256))
    question_num = db.Column(db.INTEGER)
    question = db.Column(db.VARCHAR(256))
    report_text = db.Column(db.VARCHAR(256))

    def __repr__(self):
        return '<quest %r>' % (self.question)

class ClientEvalAnswers(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_eval_id = db.Column(db.INTEGER, db.ForeignKey('client_evals.id'))
    eval_questions_id = db.Column(db.INTEGER, db.ForeignKey('eval_questions.id'))
    answer = db.Column(db.SMALLINT())
    question = db.relationship('EvalQuestions')

class ClientEvals(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    eval_type_id = db.Column(db.INTEGER, db.ForeignKey('evaluations.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    created_date = db.Column(db.DATETIME)
    answers = db.relationship('ClientEvalAnswers', backref='eval', lazy='dynamic')

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
    first_name = db.Column(db.VARCHAR(55))
    last_name = db.Column(db.VARCHAR(55))
    company_id = db.Column(db.INTEGER) # ForgeignKey to company_id
    evals = db.relationship('ClientEvals', backref='therapist', lazy='dynamic')
    clients = db.relationship('Client', backref='therapist', lazy='dynamic')


class ClientAuths(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    auth_start = db.Column(db.DATETIME)
    auth_end = db.Column(db.DATETIME)
    auth_id = db.Column(db.INTEGER)
    monthly_visits = db.Column(db.INTEGER)
    # created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)

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
    regional_center_id = db.Column(db.INTEGER, db.ForeignKey('regional_center.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    status = db.Column(db.VARCHAR(15), default='active')
    # created_date = db.Column(db.DATETIME, default=func.now())
    auths = db.relationship('ClientAuths', backref='client', lazy='dynamic')
    evals = db.relationship('ClientEvals', backref='client', lazy='dynamic')

    def __repr__(self):
        return '<client: %r %r>' %(self.first_name, self.last_name)

class Evaluations(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    test_seq = db.Column(db.VARCHAR(255))
    client_evals = db.relationship('ClientEvals', backref='eval', lazy='dynamic')
    questions = db.relationship('EvalQuestions', backref='eval', lazy='dynamic')

    def __repr__(self):
        return '<Eval: %r Seq: %r>' %(self.name, self.test_seq)
