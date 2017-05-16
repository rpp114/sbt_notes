from flask import render_template, flash, redirect, jsonify, request, g
from app import app, models
from .forms import LoginForm
from flask_security import login_required
# import .models

@app.route('/')
@app.route('/index')
# @login_required
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

@app.route('/clients')
def clients_page():
	clients = models.Client.query.filter_by(status='active').order_by(models.Client.last_name)

	return render_template('clients.html',
							clients=clients)


@app.route('/client/profile/<client_id>', methods=['GET','POST'])
def client_profile(client_id):

	client = models.Client.query.get(client_id)

	if request.method == 'POST':
		print('form results posted: ', request.form)

	return render_template('client_profile.html',
							client = client
							)




@app.route('/new_eval/<client_id>', methods=['GET', 'POST'])
def new_eval(client_id):
	evals = [{'name': 'Bayley', 'id': 1},
			 {'name': 'DAYC-2', 'id': 2}]

	client = models.Client.query.get(client_id)

	print(client_id)

	if request.method == 'POST':
		print('POST', request.form)
		return redirect('/eval/' + request.form['eval_id'])

	return render_template('new_eval.html',
							evals=evals,
							client=client)




@app.route('/evaluation/<eval_type>/<subtest>/<eval_id>', methods=['GET', 'POST'])
@app.route('/eval/<eval_id>', methods=['GET', 'POST'])
def evaluation(eval_id): # eval_type, subtest, eval_id, methods=['GET', 'POST']):
	questions = models.EvalQuestions.query.all()#filter(and_(Eval_Questions.evaluation == eval_type, Eval_Questions.subtest == subtest)).order_by(Eval_Questions.question_num)

	print(request.form) # form responses coming back... need to drop them into a response table and then redirect to the next page in the eval



	return render_template('eval.html',
							title='Eval',
							#eval=eval_type,
							questions = questions)
