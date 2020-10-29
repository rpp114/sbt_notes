
from re import findall
from flask import request, render_template, flash, redirect, url_for
from flask_login import login_required

from app.evaluation import bp as eval_bp, models as eval_models
from app import db, models


@eval_bp.route('/', methods = ['GET'])
@login_required
def index():
    client_id = request.args.get('client_id')
    
    client = models.Client.query.get(client_id)
    
    print(client)
        
    report  = {'section_one':{'text':'''Hi, I'm <span id="name"></span> and my job is <span id="job"></span>.'''}}
    
    for section in report:
        report[section]['vars']= findall(r'<span id="(.*?)"></span>',report[section]['text'])
    
    return render_template('evaluation/index.html',
                           report = report)

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
    
    sections = eval_models.EvaluationReportTemplateSection.query.order_by(eval_models.EvaluationReportTemplateSection.section_rank).all()
    
    # upload image for report letterhead
    # upload report template .docx file
    
    return render_template('evaluation/report_template.html',
                           sections=sections)
                           
@eval_bp.route('/report/template/section', methods=['GET','POST'])
@login_required
def report_template_section():
    
    section_id = request.args.get('section_id')
    
    section = eval_models.EvaluationReportTemplateSection() if section_id == None else eval_models.EvaluationReportTemplateSection.query.get(section_id)
    
    section_vars = findall(r'//(.*?)//',section.text)
    
    print(section_vars)
    
    if request.method == 'POST':
        
        section.section_rank = request.form.get('section_rank')
        section.title = request.form.get('title')
        section.text = request.form.get('text')
        
        db.session.add(section)
        db.session.commit()
        
        flash('Updated Report Section: {}.'.format(section.title))
        
        return redirect(url_for('.report_template'))
        
    return render_template('evaluation/report_template_section.html',
                           section=section)
                           
############################################################
# Eval Score Input Views
############################################################

@eval_bp.route('/scoresheet', methods=['GET'])
@login_required
def scoresheet():
    
    subtests = eval_models.EvaluationSubtest.query.all()
    
    return render_template('evaluation/eval_scoresheet.html',
                           subtests=subtests)
    
@eval_bp.route('/scoresheet/submit', methods=['POST'])
@login_required
def scoresheet_submit():
    
    if request.method == 'POST':
        print(request.form)
    
    return redirect(url_for('.scoresheet'))

############################################################
# Eval Report Views
############################################################

@eval_bp.route('/report/submit', methods= ['POST'])
@login_required
def report_submit():
    
    print(request.json)
    
    return redirect(url_for('.index'))