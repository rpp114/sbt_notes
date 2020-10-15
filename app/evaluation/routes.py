
from flask import request, render_template, flash
from flask_login import login_required

from app.evaluation import bp as eval_bp, models as eval_models
from app import db, models


@eval_bp.route('/', methods = ['GET'])
@login_required
def index():
    print('in the blueprint index')
    user = models.User.query.get(1)
    print(user)
    return render_template('evaluation/index.html')



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
        print(request.form)
        flash('Updated {} - {} question number: {}'.format(question.subtest.eval.name,question.subtest.name, question.question_num))
    
    return render_template('evaluation/question.html',
                           question=question)