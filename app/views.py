from flask import render_template, flash, redirect
from app import app
from .forms import LoginForm
from flask_security import login_required

@app.route('/')
@app.route('/index')
@login_required
def index():
	user = {'nickname': 'Ray'}

	posts = [{'author':{'nickname': 'John'},
			 'body': 'Nice day today'},
			 {'author':{'nickname': 'Susan'},
			 'body':'Yes it is'}]

	return render_template('index.html',
							title='Home',
							user=user,
							posts = posts)


"""@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		flash('Login requested for OpenId="%s", remember_me=%s' % (form.openid.data, str(form.remember_me.data)))
		return redirect('/index')
	return render_template('login.html',
							title='Sign In',
							form=form,
							providers=app.config['OPENID_PROVIDERS'])
"""


# @app.route('/evaluation/<eval_type>/<subtest>/<eval_id>', methods=['GET', 'POST'])
# def evaluation(eval_type, subtest, eval_id):
# 	questions = Eval_Questions.query.filter(and_(Eval_Questions.evaluation == eval_type, Eval_Questions.subtest == subtest)).order_by(Eval_Questions.question_num)
