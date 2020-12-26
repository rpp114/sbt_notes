from app import db

import datetime
from sqlalchemy.sql import func

class EvaluationQuestion(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    subtest_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_subtest.id'))
    question_cat = db.Column(db.VARCHAR(256))
    question_num = db.Column(db.INTEGER)
    question = db.Column(db.VARCHAR(256))
    report_text = db.Column(db.VARCHAR(256))
    caregiver_response = db.Column(db.SMALLINT(), default=0)
    responses = db.relationship('EvaluationQuestionResponse', backref='question', lazy='dynamic')
    answers = db.relationship('ClientEvaluationAnswer', backref='question', lazy='dynamic')
    
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
    report_sections = db.relationship('ClientEvalReportSection', backref='subtest', lazy='dynamic')

    def __repr__(self):
        return '<subtest {}>'.format(self.name)
    
class EvaluationType(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.VARCHAR(55))
    test_formal_name = db.Column(db.VARCHAR(255))
    description = db.Column(db.TEXT)
    report_text = db.Column(db.TEXT)
    subtests = db.relationship('EvaluationSubtest', backref='eval', lazy='dynamic')

    def __repr__(self):
        return '<Eval: {}>'.format(self.name)
    
class EvaluationReportTemplateSection(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    section_rank = db.Column(db.INTEGER)
    before_assessment = db.Column(db.SMALLINT(), default=0)
    title = db.Column(db.VARCHAR(255))
    text = db.Column(db.TEXT)
    report_sections = db.relationship('ClientEvalReportSection', backref='template', lazy='dynamic')
    
class ClientEvaluation(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    client_id = db.Column(db.INTEGER, db.ForeignKey('client.id'))
    therapist_id = db.Column(db.INTEGER, db.ForeignKey('therapist.id'))
    client_appt_id = db.Column(db.INTEGER, db.ForeignKey('client_appt.id'))
    created_date = db.Column(db.DATETIME, default=datetime.datetime.utcnow)
    answers = db.relationship('ClientEvaluationAnswer', backref='eval', lazy='dynamic')
    report = db.relationship('ClientEvaluationReport', backref='eval', uselist=False)
    
    def __repr__(self):
        return '<Client Eval: {} {}>'.format(self.client.first_name, self.id)

class ClientEvaluationAnswer(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    question_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_question.id'))
    evaluation_id = db.Column(db.INTEGER, db.ForeignKey('client_evaluation.id'))
    caregiver_response = db.Column(db.SMALLINT(), default=0)
    score = db.Column(db.INTEGER)
    
class ClientEvaluationReport(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    evaluation_id = db.Column(db.INTEGER, db.ForeignKey('client_evaluation.id'))
    filename = db.Column(db.VARCHAR(255))
    sections = db.relationship('ClientEvalReportSection', backref='report', lazy='dynamic')
    
class ClientEvalReportSection(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    report_id = db.Column(db.INTEGER, db.ForeignKey('client_evaluation_report.id'))
    eval_subtest_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_subtest.id'), nullable=True)
    section_template_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_report_template_section.id'))
    section_title = db.Column(db.VARCHAR(50))
    text = db.Column(db.TEXT)
    
    def capitalize_text(self):
        
        report_text = []
        
        for s in self.text.split('. '):
            
            sentence = ''
            for i,l in enumerate(s):
                if l in ('\n','\r','',' '):
                    sentence += l
                else:
                    sentence += l.capitalize() + s[i+1:]
                    break
            report_text.append(sentence)

        self.text = '. '.join(report_text)
        
        
        
