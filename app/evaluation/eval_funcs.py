import sys,os, datetime

from re import findall
from docxtpl import DocxTemplate, Listing

from app.evaluation import bp as eval_bp, models as eval_models
from app import db

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..','..','jobs'))

from evals import get_client_age





def create_eval_report(eval):
    
    report_info = create_report_info(eval)
    
    template_dir = os.path.dirname(os.path.realpath(__file__))
    
    template_dir = os.path.join(template_dir,'..','..','docs',str(eval.therapist.company_id),'reports')
    
    report = DocxTemplate(os.path.join(template_dir, 'report_template_bayley_4.docx'))
    
    report.render(report_info)
    
    new_report_filepath = os.path.join(template_dir, 'download_report.docx'.format(eval.id, eval.created_date.strftime('%Y_%m_%d')))
    
    report.save(new_report_filepath)
                
    return template_dir



def create_report_info(eval):
    
    report_info = {'client': get_client_report_info(eval),
                   'pre_assessment':[],
                   'assessments':{},
                   'post_assessment':[],
                   'eval':eval,
                   }
    
    sections = eval.report.sections.order_by(eval_models.ClientEvalReportSection.section_template_id,
                                             eval_models.ClientEvalReportSection.eval_subtest_id).all()
    
    for section in sections:
        if section.section_template_id > 0:
            if section.template.before_assessment:
                report_info['pre_assessment'].append(section)
            else:
                report_info['post_assessment'].append(section)
                
        else:
            eval_name = section.subtest.eval.name
            report_info['assessments'][eval_name] = report_info['assessments'].get(eval_name, {'eval': section.subtest.eval,
                                                                                               'subtests':[]})
            report_info['assessments'][eval_name]['subtests'].append(section)
            
    return report_info



def write_assessment_sections(eval):
    
    client_report_info = get_client_report_info(eval)
    
    subtests = get_subtest_info(eval)
    
    report = eval_models.ClientEvaluationReport(evaluation_id = eval.id) if eval.report == None else eval.report
    
    for k,answers in subtests.items():
        
        subtest = eval_models.EvaluationSubtest.query.get(k)
        
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
                                                   section_template_id = 0,
                                                   section_title = subtest.name,
                                                   text = report_text.format(**client_report_info))
        sect.capitalize_text()
        report.sections.append(sect)
    
    db.session.add(report)
    db.session.commit()
    
    return True

def make_answer_list(answers):
    
    if len(answers) == 1:
        return answers[0]
    elif len(answers) == 0:
        return ''
    else:
        return ', and '.join((', '.join(answers[:-1]),answers[-1]))
    
    
def get_subtest_info(eval):
    subtests = {}
    
    for answer in eval.answers.all():
        
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
        
    
    return report_info

