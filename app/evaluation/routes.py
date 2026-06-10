import json
from re import findall
from flask import request, render_template, flash, redirect, url_for, jsonify, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import select, func

from sbt_notes.app.evaluation import bp as eval_bp, models as eval_models
from sbt_notes.app import db, models

from .eval_funcs import write_assessment_sections, get_client_report_info, create_eval_report

from sbt_notes.jobs.user_activity_logs import write_activity_log

###############################
# Start Eval Process data
###############################


@eval_bp.route('/', methods = ['GET', 'POST'])
@login_required
def index():
    client_id = request.args.get('client_id')
    
    client = models.Client.query.get(client_id)    
    
    if request.method == 'POST':
        appt_id = request.form.get('eval_appt')
        
        appt = models.ClientAppt.query.get(appt_id)

        new_eval = eval_models.ClientEvaluation(client_appt_id = appt_id,
                                                therapist_id = appt.therapist_id)
        if client.weeks_premature == None:
            client.weeks_premature = request.form.get('weeks_premature',0)
            
        client.evaluations.append(new_eval)
        
        db.session.commit()
        
    
    eval_appts = client.evaluations.order_by(eval_models.ClientEvaluation.created_date.desc()).all()
    
    
    appts = client.appts.filter(models.ClientAppt.cancelled == 0)\
            .order_by(models.ClientAppt.start_datetime.desc()).limit(5).all()
    
    return render_template('evaluation/index.html',
                           client = client,
                           eval_appts = eval_appts,
                           appts = appts)
    

##################################################
#  Eval Templates to handle report writing
##################################################

@eval_bp.route('/types', methods = ['GET'])
@login_required
def eval_types():
    
    evals = eval_models.EvaluationType.query.all()
    
    return render_template('evaluation/eval_types.html',
                           evals = evals)
    
@eval_bp.route('/type', methods = ['GET','POST'])
@login_required
def eval_type():
    
    type_id = request.args.get('eval_type_id')
    
    eval_type = eval_models.EvaluationType.query.get(type_id)
    
    if request.method == 'POST':
        eval_type.name = request.form.get('eval_type_name')
        eval_type.test_formal_name = request.form.get('test_formal_name')
        eval_type.description = request.form.get('description')
        db.session.add(eval_type)
        db.session.commit()
        
        flash('Updated {}.'.format(eval_type.name))
    
    return render_template('evaluation/eval_type.html',
                           eval_type = eval_type)
    
@eval_bp.route('/type/report', methods = ['GET','POST'])
@login_required
def eval_report_text():
    eval_type_id = request.args.get('eval_type_id')
    
    eval_type = eval_models.EvaluationType.query.get(eval_type_id)
    
    if request.method == 'POST':
        eval_type.report_text = request.form.get('report_text')
        db.session.add(eval_type)
        db.session.commit()
        return redirect(url_for('.eval_types'))
    
    return render_template('evaluation/eval_report_text.html',
                           eval_type = eval_type)
    
@eval_bp.route('/subtest', methods = ['GET','POST'])
@login_required
def subtest():
    
    subtest_id = request.args.get('subtest_id')
    
    subtest = eval_models.EvaluationSubtest.query.get(subtest_id)
    
    if request.method == 'POST':
        subtest.name = request.form.get('subtest_name')
        subtest.description = request.form.get('description')
        db.session.add(subtest)
        db.session.commit()
        
        flash('Updated {}'.format(subtest.name))

    return render_template('evaluation/subtest.html',
                           subtest=subtest)


@eval_bp.route('/question', methods = ['GET','POST'])
@login_required
def question():
    
    question_id = request.args.get('question_id')
    
    question = eval_models.EvaluationQuestion.query.get(question_id)
    
    if request.method == 'POST':
        question.question_num = request.form.get('question_num')
        question.question = request.form.get('question')
        question.report_text = request.form.get('report_text')
        question.question_cat = request.form.get('question_cat')
        question.caregiver_response = 0 if request.form.get('caregiver_response', None) == None else 1
        
        db.session.add(question)
        
        responses = question.responses.all()
        
        for response in responses:
            response.response = request.form.get(str(response.score) + '_response',None)
            response.report_text = request.form.get(str(response.score) + '_report_text',None)
            
            db.session.add(response)
        
        db.session.commit()
        
        flash('Updated {} - {} question number: {}'.format(question.subtest.eval.name,question.subtest.name, question.question_num))
    
    return render_template('evaluation/question.html',
                           question=question)


@eval_bp.route('/report/template', methods=['GET'])
@login_required
def report_template():
    
    # upload image for report letterhead
    # upload report template .docx file
    
    # current_user.company_id = 3
    template = eval_models.EvaluationReportTemplate.get_latest_version(current_user.company_id)

    if not template:
        init_template = eval_models.EvaluationReportTemplate.get_latest_version(1)
        template = init_template.clone()
            
    sects = template.get_background_sections()
    
    sections = {'before': [],
                'after': []}
    
    for sect in sects:
        if sect.before_assessment:
            sections['before'].append(sect)
        else:
            sections['after'].append(sect)
    
    return render_template('evaluation/report_template.html',
                           sections=sections)
                           
@eval_bp.route('/report/template/section', methods=['GET','POST'])
@login_required
def report_template_section():
    
    section_id = request.args.get('section_id', None)
    
    section = eval_models.EvaluationReportTemplateSection() if section_id == None else eval_models.EvaluationReportTemplateSection.query.get(section_id)
    
    if request.method == 'POST':
        
        changed = (section.title != request.form.get('title')
            or section.text != request.form.get('text')
            or section.section_rank != int(request.form.get('section_rank'))
            or section.before_assessment != 1 if request.form.get('before_assessment',0) == 'on' else 0
            or section_id == None)
        
        if not changed:
            
            flash('No changes made to Report Section: {}.'.format(section.title), 'error')
            return redirect(url_for('.report_template'))
        
        if section_id:
            
            new_section = eval_models.EvaluationReportTemplateSection(
                company_id = current_user.company_id,
                version = section.version+1,
                section_rank = request.form.get('section_rank'),
                title = request.form.get('title'),
                text = request.form.get('text'),
                before_assessment = 1 if request.form.get('before_assessment',0) == 'on' else 0
            )
            section_id = int(section_id)
            new_section.old_item_id = section_id
        else: 
            new_section = eval_models.EvaluationReportTemplateSection(
                company_id = current_user.company_id,
                version = 1,
                section_rank = request.form.get('section_rank'),
                title = request.form.get('title'),
                text = request.form.get('text'),
                before_assessment = 1 if request.form.get('before_assessment',0) == 'on' else 0
            )
            new_section.old_item_id = None
        new_section.item_type = 'background'
        
        current_template = eval_models.EvaluationReportTemplate.get_latest_version(current_user.company_id)
        current_template.clone(new_section)
        # update_report_template(new_section, 'background', section_id)
        
        flash('Updated Report Section: {}. Created new report template.'.format(section.title))
        
        return redirect(url_for('.report_template'))
        
    return render_template('evaluation/report_template_section.html',
                           section=section)
                           
############################################################
# Eval Score Input Views
############################################################

@eval_bp.route('/scoresheet', methods=['GET','POST'])
@login_required
def scoresheet():
    
    eval_id = request.args.get('eval_id')
    
    eval = eval_models.ClientEvaluation.query.get(eval_id)
    
    if request.method == 'POST':

        for q_id in request.form:
            if 'caregiver' not in q_id:
                q = eval_models.ClientEvaluationAnswer(question_id = q_id,
                                                    score = request.form.get(q_id),
                                                    caregiver_response = request.form.get('_'.join((q_id,'caregiver')),0))
                eval.answers.append(q)
                
        db.session.commit()
        
        flash('Submitted evaluation responses for {} {} on {}'.format(eval.client.first_name,eval.client.last_name, eval.appt.start_datetime.strftime('%b %d, %Y')))

        return redirect(url_for('.index', client_id = eval.client.id))        
    
    subtests = eval_models.EvaluationSubtest.query.all()

    eval_answers = {}

    for answer in eval.answers:
        eval_answers[answer.question.id] = {'caregiver_repsonse': answer.caregiver_response,
                                            'score': answer.score}

    return render_template('evaluation/eval_scoresheet.html',
                           subtests=subtests,
                           eval_answers=eval_answers)

############################################################
# Eval Report Views
############################################################

@eval_bp.route('/report', methods = ['GET','POST'])
@login_required
def create_report():
    
    eval_id = request.args.get('eval_id')
    
    eval = eval_models.ClientEvaluation.query.get(eval_id)
    
    if eval.client.uci_id == 0:
        flash(f'Client UCI number needed for {eval.client.first_name} {eval.client.last_name}.', 'error')
        return redirect(url_for('main.client_profile', client_id = eval.client.id))
    
    if eval.client.case_worker == None:
        flash(f'{eval.client.first_name} {eval.client.last_name} needs a case worker.', 'error')
        return redirect(url_for('main.client_profile', client_id = eval.client.id))
    
    client_report_info = get_client_report_info(eval)
    
    version = eval.report.template.version if eval.report else None
    
    if version is None:
        
        latest_version = eval_models.EvaluationReportTemplate.get_latest_version(eval.client.therapist.user.company_id)
        
        version_to_use = latest_version.version
        
    else:
        
        version_to_use = version
    
    if request.method == 'POST':
        template = db.session.scalar(
            select(eval_models.EvaluationReportTemplate)
            .where(
                eval_models.EvaluationReportTemplate.version == version_to_use,
                eval_models.EvaluationReportTemplate.company_id == current_user.company_id
                )
            )
        
        report = eval_models.ClientEvaluationReport(evaluation_id = eval_id, template=template) if eval.report == None else eval.report
        
        report_vars = {}
        for report_var in request.form:
            if report_var == 'manual_save':
                continue
            section_id = report_var.split('-')[0]
            report_vars[section_id] = report_vars.get(section_id,[])
            report_vars[section_id].append(('//' + report_var.split('-')[1] + '//',request.form.get(report_var)))
            
        report.encrypt_text(json.dumps(report_vars))
        
        
        db.session.add(report)
        
        db.session.commit()
        
        if request.form.get('manual_save', 0):
            flash('Submitted evaluation background for {} {} on {}'.format(eval.client.first_name,eval.client.last_name, eval.appt.start_datetime.strftime('%b %d, %Y')))
            return redirect(url_for('.index', client_id=eval.client.id))
    

    sects = eval_models.EvaluationReportTemplate.get_background_sections(version_to_use)
    
    sections = []
    report = eval.report
    report_input_vars = {} if not report else json.loads(report.decrypted_text)
    
    for sect in sects:
        new_sect = {'id': sect.id,
                    'title': sect.title,
                    'vars':  [],
                    'text': sect.text.format(**client_report_info)}
        
        intext_vars = findall(r'//(.*?)//',sect.text)
        
        report_input = dict(report_input_vars.get(str(sect.id), []))

        for var in intext_vars:
            replace_var = f'//{var}//'
            new_sect['vars'].append((var, report_input.get(replace_var, '')))
            new_sect['text'] = new_sect['text'].replace(replace_var,f'<b><span id="{str(new_sect['id'])+'-'+var}">{report_input.get(replace_var, '') if report_input.get(replace_var, '') else var}</span></b>')
            
        sections.append(new_sect)
    return render_template('evaluation/report.html',
                           sections=sections,
                           client=client_report_info, 
                           eval_id = eval.id)
    


@eval_bp.route('/report/download', methods = ['GET'])
@login_required
def report_download():
    eval_id = request.args.get('eval_id', 0)
    
    eval = eval_models.ClientEvaluation.query.get(eval_id)
    
    file_path = create_eval_report(eval)
    
    download_filename = ' '.join((eval.client.first_name, eval.client.last_name, eval.appt.start_datetime.strftime('%Y_%m_%d'))).lower()
    
    download_name = download_filename.replace(' ','_')
    
    write_activity_log('download_report', 'eval', download_name, request)
    
    return send_from_directory(file_path, 'download_report.docx', as_attachment=True, download_name=download_name + '.docx')
