import sys,os, datetime, json

from re import findall
from docxtpl import DocxTemplate, Listing
from sqlalchemy import select
from flask_login import current_user
from flask import current_app
from pathlib import Path

from . import bp as eval_bp 
from . import models as eval_models
from sbt_notes.app import db

#sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..','..','jobs'))

from sbt_notes.jobs.evals import get_client_age


def create_eval_report(eval):
    
    template_dir = Path(current_app.root_path).resolve().parent / "docs" / 'report_template'
    
    report_info = create_report_info(eval)
    
    
    # template_dir = os.path.dirname(os.path.realpath(__file__))
    
    # template_dir = os.path.join(template_dir,'..','..','docs',str(eval.therapist.company_id),'reports')
     
    report = DocxTemplate(os.path.join(template_dir, 'report_template_bayley_4.docx'))
    
    report.render(report_info)
    
    new_report_filepath = os.path.join(template_dir, f'download_report.docx'.format(eval.id, eval.created_date.strftime('%Y_%m_%d')))
    
    report.save(new_report_filepath)
                
    return template_dir


def capitalize_text(text):
    
    report_text = []
    
    for s in text.split('. '):
        if s != '': 
            sentence = ''
            for i,l in enumerate(s):
                if l in ('\n','\r','',' '):
                    sentence += l
                else:
                    sentence += l.capitalize() + s[i+1:]
                    break
            report_text.append(sentence.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))

    output_text = '. '.join(report_text)
    output_text = output_text.replace('. .', '.')
    
    return output_text


def create_report_info(eval):

    eval_data = {'start_date': eval.appt.start_datetime,
                 'therapist': {'name': eval.therapist.name,
                               'signature': eval.therapist.signature},
                 'regional_center_name': eval.client.regional_center.name,
                 }
    
    report_info = {'client': get_client_report_info(eval),
                   'pre_assessment':[],
                   'assessments':{},
                   'post_assessment':[],
                   'eval':eval_data,
                   }
    
    found_report_sections = False
    
    encrypted_report_sections = eval.report.sections.order_by(eval_models.ClientEvalReportSection.id,
                                             eval_models.ClientEvalReportSection.eval_subtest_id).all()
    
    for ers in encrypted_report_sections:
        found_report_sections = True
        
        sect = {'section_title': ers.section_title,
                'text': ers.decrypted_text,
                }

        if ers.template.id > 0:
            if ers.template.before_assessment:
                report_info['pre_assessment'].append(sect)
            else:
                report_info['post_assessment'].append(sect)
                
        else:
            eval_name = ers.subtest.eval.name
            report_info['assessments'][eval_name] = report_info['assessments'].get(eval_name, {'eval': {'test_formal_name': ers.subtest.eval.test_formal_name,
                                                                                                        'description': ers.subtest.eval.description,
                                                                                                        'name': ers.subtest.name,
                                                                                                        },
                                                                                               'subtests':[]})
            report_info['assessments'][eval_name]['subtests'].append({'name': ers.subtest.name,
                                                                      'description': ers.subtest.description,
                                                                      'text': ers.text,
                                                                      })
    
    if not found_report_sections:    
        
        report_vars = json.loads(eval.report.decrypted_text)
        
                
        for item in eval.report.template.get_background_sections(eval.report.template.version):
        
                 # create report info from background Inputs if no pre-written_sections
            if item.id == -1: 
                continue
            
            sect_id = str(item.id)
            
            section_text = item.text
            
            for var in report_vars.get(sect_id,[]):
                section_text = section_text.replace(var[0],var[1])
            
            sect = {'section_title': item.title,
                    'text': capitalize_text(section_text.format(**report_info['client']))}
            
            if int(item.id) > 0:
                if item.before_assessment:
                    report_info['pre_assessment'].append(sect)
                else:
                    report_info['post_assessment'].append(sect)
                
            # create subtests if no pre-written sections
        subtests = get_subtest_info(eval)
            
        for k,answers in subtests.items():

            subtest = db.session.get(eval_models.EvaluationSubtest, k)
            
            report_text = subtest.eval.report_text        
            
            vars = findall(r'//(.*?)//',report_text)
            
            for var in vars:
                score = int(var.split('_')[-1])
                caregiver = 1 if var.split('_')[0] == 'caregiver' else 0
                
                answer_list = make_answer_list(answers.get(score,{}).get(caregiver,[]))
                
                if caregiver == 1 and len(answer_list) > 0:
                    answer_list = 'Caregiver reported that {first_name} ' + answer_list + '.'

                report_text = report_text.replace('//{}//'.format(var), answer_list)
                        
            eval_name = subtest.eval.name
            
            report_info['assessments'][eval_name] = report_info['assessments'].get(eval_name, {'eval': {'test_formal_name': subtest.eval.test_formal_name,
                                                                                                        'description': subtest.eval.description,
                                                                                                        'name': subtest.name,
                                                                                                        },
                                                                                            'subtests':[]})
            report_info['assessments'][eval_name]['subtests'].append({'name': subtest.name,
                                                                      'description': subtest.description,
                                                                      'text': capitalize_text(report_text.format(**report_info['client'])),
                                                                      })
    for k,i in report_info['client'].items():
        print(f'{k}: {i}')
    return report_info

    

def write_assessment_sections(eval, client_report_info):
       
    subtests = get_subtest_info(eval)
    
    version = eval.report.report_template_version if eval.report else None
    
    assessment_sections = []
    
    if version is None:
        
        latest_version = db.session.scalar(
            select(
                func.max(eval_models.evaluation_type.version)
            )
            .where(eval_models.evaluation_type.company_id == eval.client.therapist.user.company_id)
        )
        
        version_to_use = latest_version
        
    else:
        
        version_to_use = version
    
    # report = eval_models.ClientEvaluationReport(evaluation_id = eval.id, report_template_version = version_to_use) if eval.report == None else eval.report

    
    for k,answers in subtests.items():
        
        subtest = db.session.get(eval_models.EvaluationSubtest, k)
        
        report_text = subtest.eval.report_text        
        
        vars = findall(r'//(.*?)//',report_text)
        
        for var in vars:
           score = int(var.split('_')[-1])
           caregiver = 1 if var.split('_')[0] == 'caregiver' else 0
           
           answer_list = make_answer_list(answers.get(score,{}).get(caregiver,[]))
           
           if caregiver == 1 and len(answer_list) > 0:
               answer_list = 'Caregiver reported that {first_name} ' + answer_list + '.'

           report_text = report_text.replace('//{}//'.format(var), answer_list)
           
        
        sect = eval_models.ClientEvalReportSection(eval_subtest_id = subtest.id,
                                                   section_template_id = -1,
                                                   section_title = subtest.name,
                                                   text = report_text.format(**client_report_info))
        sect.capitalize_text()
        assessment_sections.append(sect)
    
    return assessment_sections


def make_answer_list(answers):
    
    if len(answers) == 1:
        return answers[0]
    elif len(answers) == 0:
        return ''
    else:
        return ', and '.join((', '.join(answers[:-1]),answers[-1]))
    
    
def get_subtest_info(eval):
    subtests = {}
    
    for answer in eval.answers:
        
        subtests[answer.question.subtest_id] = subtests.get(answer.question.subtest_id,{})
        
        subtest = subtests[answer.question.subtest_id]
            
        subtest[answer.score] = subtest.get(answer.score, {})
        
        subtest[answer.score][answer.caregiver_response] = subtest[answer.score].get(answer.caregiver_response,[])
        
        if answer.question.subtest.eval_type_id == 1:
            question_response = answer.question.responses.filter_by(score = 1).first()
        else:
            question_response = answer.question.responses.filter_by(score = answer.score).first()
        
        subtest[answer.score][answer.caregiver_response].append(question_response.report_text)
    
    return subtests



def get_client_report_info(eval):
    
    client = eval.client
    
    appt = eval.appt
    
    report_info = client.__dict__
    
    
    report_info['full_name'] = client.full_name
    report_info['pronoun'] = 'he' if client.gender == 'M' else 'she'
    report_info['possessive_pronoun'] = 'his' if client.gender == 'M' else 'her'
    report_info['child'] = 'boy' if client.gender == 'M' else 'girl' 
    
    age_tuple = get_client_age(client.birthdate, appt.start_datetime)
    report_info['age_tuple'] = age_tuple
    report_info['age'] = '{} months and {} days'.format(*age_tuple)
    
    adjusted_age_tuple = age_tuple
    
    if age_tuple[0] < 24 and client.weeks_premature >= 4:
        adjusted_age = eval.client.birthdate + datetime.timedelta(int(eval.client.weeks_premature * 7 // 1))
        adjusted_age_tuple = get_client_age(adjusted_age, appt.start_datetime)
    report_info['adjusted_age_tuple'] = adjusted_age_tuple
    report_info['adjusted_age'] = '{} months and {} days'.format(*adjusted_age_tuple)
    
    report_info['case_worker'] = client.case_worker.name
    
    return report_info

