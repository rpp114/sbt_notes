from app import db

import datetime
from sqlalchemy.sql import func


# class Test(db.Model):
#     id = db.Column(db.INTEGER, primary_key=True)
#     stuff = db.Column(db.Text)
#     client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))

class EvaluationQuestion(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    subtest_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_subtest.id'))
    question_cat = db.Column(db.VARCHAR(256))
    question_num = db.Column(db.INTEGER)
    question = db.Column(db.VARCHAR(256))
    report_text = db.Column(db.VARCHAR(256))
    caregiver_response = db.Column(db.SMALLINT(), default=0)
    responses = db.relationship('EvaluationQuestionResponse', backref='question', lazy='dynamic')
    
    def __repr__(self):
        return '<question {}>'.format(self.question)
    
class EvaluationQuestionResponse(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    question_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_question.id'))
    score = db.Column(db.INTEGER)
    response = db.Column(db.VARCHAR(256))
    report_text = db.Column(db.VARCHAR(256))
    
    def __repr__(self):
        return '<response {}>'.format(self.response)

class EvaluationSubtest(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    eval_type_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_type.id'))
    eval_subtest_id = db.Column(db.INTEGER)
    name = db.Column(db.VARCHAR(50))
    description = db.Column(db.TEXT)
    # evals = db.relationship('ClientEval', secondary='client_eval_subtest_lookup')
    questions = db.relationship('EvaluationQuestion', backref='subtest', lazy='dynamic')
    # report_sections = db.relationship('ReportSection', backref='subtest', lazy='dynamic')

    def __repr__(self):
        return '<subtest {}>'.format(self.name)
    
class EvaluationType(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    test_formal_name = db.Column(db.VARCHAR(255))
    description = db.Column(db.TEXT)
    subtests = db.relationship('EvaluationSubtest', backref='eval', lazy='dynamic')

    def __repr__(self):
        return '<Eval: {}>'.format(self.name)