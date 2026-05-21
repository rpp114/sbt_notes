from sbt_notes.app import db

import datetime
from sqlalchemy.sql import func, select
from flask_login import current_user

from sqlalchemy.dialects.mysql import MEDIUMTEXT, LONGTEXT, JSON

from sbt_notes.jobs.encryption_handler import decrypt_text, encrypt_text

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
    
class EvaluationReportTemplate(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    company_id = db.Column(db.INTEGER)
    version = db.Column(db.INTEGER)
    reports = db.relationship('ClientEvaluationReport', backref='template', lazy='dynamic')
    items = db.relationship('EvaluationReportTemplateItem', backref='template')
    
    def clone(self, new_section=None):
        
        if new_section:
            db.session.add(new_section)
            db.session.flush()
            
            latest_template = self.get_latest_version(current_user.company_id)

            new_template = EvaluationReportTemplate(
                company_id=latest_template.company_id,
                version=latest_template.version + 1
            )

            db.session.add(new_template)
            db.session.flush()
            
            old_items = latest_template.items
            
            old_item_id = new_section.old_item_id
                
            for item in old_items:

                new_item_id = item.item_id

                if (
                    item.item_type == new_section.item_type
                    and item.item_id == old_item_id
                ):
                    new_item_id = new_section.id

                copied_item = EvaluationReportTemplateItem(
                    evaluation_report_template_id=new_template.id,
                    item_type=item.item_type,
                    item_id=new_item_id
                )

                db.session.add(copied_item)
            
            if not old_item_id:
                new_item = EvaluationReportTemplateItem(
                    evaluation_report_template_id=new_template.id,
                    item_type=new_section.item_type,
                    item_id=new_section.id
                )
                
                db.session.add(new_item)
            
            
        else:
            new_template = EvaluationReportTemplate(
                company_id=current_user.company_id,
                version=1
            )

            db.session.add(new_template)
            db.session.flush()

            for item in self.items:

                copied_item = EvaluationReportTemplateItem(
                    evaluation_report_template_id=new_template.id,
                    item_type=item.item_type,
                    item_id=item.item_id
                )

                db.session.add(copied_item)

        db.session.commit()
        return new_template
    
    @classmethod
    def get_latest_version(cls, company_id=1):
        version = db.session.scalar(
                select(func.max(cls.version))
                .where(cls.company_id == company_id)
            )
        
        return db.session.scalars(
                select(EvaluationReportTemplate)
                .where(EvaluationReportTemplate.company_id == company_id,
                       EvaluationReportTemplate.version == version)
                ).one_or_none()
        
    @classmethod
    def get_background_sections(cls, version=None):
        
        if not version: 
            version = db.session.scalar(
                select(func.max(cls.version))
                .where(cls.company_id == current_user.company_id)
            )

        items = db.session.scalars(
            select(EvaluationReportTemplateItem)
                .join(
                    EvaluationReportTemplate,
                    EvaluationReportTemplate.id ==
                    EvaluationReportTemplateItem.evaluation_report_template_id
                )
                .join(
                    EvaluationReportTemplateSection,
                    EvaluationReportTemplateSection.id ==
                    EvaluationReportTemplateItem.item_id
                )
                .where(
                    EvaluationReportTemplate.company_id == current_user.company_id,
                    EvaluationReportTemplate.version == version,
                    EvaluationReportTemplateItem.item_type == "background",
                    EvaluationReportTemplateSection.id > 0
                )
                .order_by(
                    EvaluationReportTemplateSection.before_assessment.desc(),
                    EvaluationReportTemplateSection.section_rank
                )
        ).all()

        return [item.section for item in items]
    
    @classmethod
    def get_eval_types_sections(cls, version=None):
        
        if not version: 
            version = db.session.scalar(
                select(func.max(cls.version))
                .where(cls.company_id == current_user.company_id)
            )

        items = db.session.scalars(
            select(EvaluationReportTemplateItem)
                .join(
                    EvaluationReportTemplate,
                    EvaluationReportTemplate.id ==
                    EvaluationReportTemplateItem.evaluation_report_template_id
                )
                .join(
                    EvaluationType,
                    EvaluationType.id ==
                    EvaluationReportTemplateItem.item_id
                )
                .where(
                    EvaluationReportTemplate.company_id == current_user.company_id,
                    EvaluationReportTemplate.version == version,
                    EvaluationReportTemplateItem.item_type == "eval_type"
                )
                .order_by(
                    EvaluationType.id
                )
        ).all()

        return [item.section for item in items]
    
    
class EvaluationReportTemplateItem(db.Model):
    id = id = db.Column(db.INTEGER, primary_key=True)
    evaluation_report_template_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_report_template.id'))
    item_type = db.Column(db.String(50))
    item_id = db.Column(db.INTEGER)
    
    @property
    def section(self):
        SECTION_MODELS = {'eval_type': EvaluationType,
                          'background': EvaluationReportTemplateSection}
        
        model = SECTION_MODELS.get(self.item_type)
        
        if not model:
            return None
        
        return db.session.get(
            model,
            self.item_id
        ) 
        
class EvaluationType(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    company_id = db.Column(db.INTEGER)
    version = db.Column(db.INTEGER)
    name = db.Column(db.VARCHAR(55))
    test_formal_name = db.Column(db.VARCHAR(255))
    description = db.Column(db.TEXT)
    report_text = db.Column(db.TEXT)
    subtests = db.relationship('EvaluationSubtest', backref='eval', lazy='dynamic')

    def __repr__(self):
        return '<Eval: {}>'.format(self.name)
    
    @property
    def text(self):
        return self.report_text
    
class EvaluationReportTemplateSection(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    company_id = db.Column(db.INTEGER)
    version = db.Column(db.INTEGER)
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
    answers = db.relationship('ClientEvaluationAnswer', backref='eval')
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
    encrypted_report_json = db.Column(db.LargeBinary)
    text_nonce = db.Column(db.LargeBinary)
    encrypted_dek = db.Column(db.LargeBinary)
    dek_nonce = db.Column(db.LargeBinary)
    key_version = db.Column(db.INTEGER)
    evaluation_report_template_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_report_template.id'))
    
    @property
    def decrypted_text(self):
        return decrypt_text(self, 'encrypted_report_json')
    
    def encrypt_text(self, plaintext):
        encrypted_text_data = encrypt_text(plaintext)
        self.encrypted_report_json = encrypted_text_data['encrypted_text']
        self.text_nonce = encrypted_text_data['text_nonce']
        self.encrypted_dek = encrypted_text_data['encrypted_dek']
        self.dek_nonce = encrypted_text_data['dek_nonce']
        self.key_version = encrypted_text_data['key_version']
    
class ClientEvalReportSection(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    report_id = db.Column(db.INTEGER, db.ForeignKey('client_evaluation_report.id'))
    eval_subtest_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_subtest.id'), nullable=True)
    section_template_id = db.Column(db.INTEGER, db.ForeignKey('evaluation_report_template_section.id'))
    section_title = db.Column(db.VARCHAR(50))
    text = db.Column(db.TEXT)
    encrypted_text = db.Column(db.LargeBinary)
    text_nonce = db.Column(db.LargeBinary)
    encrypted_dek = db.Column(db.LargeBinary)
    dek_nonce = db.Column(db.LargeBinary)
    key_version = db.Column(db.INTEGER)
    
    @property
    def decrypted_text(self):
        return decrypt_text(self, 'encrypted_text')
    
    def encrypt_text(self, plaintext):
        encrypted_text_data = encrypt_text(plaintext)
        self.encrypted_text = encrypted_text_data['encrypted_text']
        self.text_nonce = encrypted_text_data['text_nonce']
        self.encrypted_dek = encrypted_text_data['encrypted_dek']
        self.dek_nonce = encrypted_text_data['dek_nonce']
        self.key_version = encrypted_text_data['key_version']
    
    def capitalize_text(self):
        
        report_text = []
        
        for s in self.text.split('. '):
            if s != '': 
                sentence = ''
                for i,l in enumerate(s):
                    if l in ('\n','\r','',' '):
                        sentence += l
                    else:
                        sentence += l.capitalize() + s[i+1:]
                        break
                report_text.append(sentence.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))

        self.text = '. '.join(report_text)
        self.text = self.text.replace('. .', '.')
        
        
        
