from flask import render_template, flash, redirect, jsonify, request, g, session
from app import app, models, db
from .forms import LoginForm, ClientInfoForm, NewEvalForm
from flask_security import login_required
from sqlalchemy import and_
import json
import datetime

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


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		flash('Login requested for OpenId="%s", remember_me=%s' % (form.openid.data, str(form.remember_me.data)))
		return redirect('/index')
	return render_template('login.html',
							title='Sign In',
							form=form,
							providers=app.config['OPENID_PROVIDERS'])


@app.route('/clients')
def clients_page():
	clients = models.Client.query.filter_by(status='active').order_by(models.Client.last_name)

	return render_template('clients.html',
							clients=clients)

@app.route('/eval_directory/<client_id>')
def eval_directory(client_id):
	client = models.Client.query.get(client_id)

	return render_template('eval_directory.html',
							client=client,
							evals=client.evals)

@app.route('/client/delete', methods=['POST'])
def delete_client():
	# print('delete post: ', request.args.get('client_id'))
	client = models.Client.query.get(request.args.get('client_id'))
	client.status='inactive'
	db.session.commit()
	return redirect('/clients')


@app.route('/client/profile', methods=['GET','POST'])
def client_profile():

	if request.args.get('client_id') == None:
		new_client = models.Client(first_name='New Client')
		db.session.add(new_client)
		db.session.commit()
		client = models.Client.query.get(new_client.id)
	else:
		client_id = request.args.get('client_id')
		client = models.Client.query.get(client_id)

	form = ClientInfoForm(obj=client)

	reg_center_result = models.RegionalCenter.query.all()
	centers = []
	for center in reg_center_result:
		centers.append((center.id, center.name))
	form.regional_center_id.choices = centers

	therapist_result = models.Therapist.query.all()
	therapists = []
	for therapist in therapist_result:
		therapists.append((therapist.id, therapist.first_name))
	form.therapist_id.choices = therapists

	if form.validate_on_submit():
		client.first_name = form.first_name.data
		client.last_name = form.last_name.data
		client.birthdate = form.birthdate.data
		client.uci_id = form.uci_id.data
		client.address = form.address.data
		client.city = form.city.data
		client.state = form.state.data
		client.zipcode = form.zipcode.data
		client.phone = form.phone.data
		client.regional_center_id = form.regional_center_id.data
		client.therapist_id = form.therapist_id.data
		db.session.commit()
		return redirect('/clients')

	return render_template('client_profile.html',
							client=client,
							form=form)


@app.route('/new_eval/<client_id>', methods=['GET', 'POST'])
def new_eval(client_id):
	eval_data = models.Evaluations.query.all()
	eval_choices= []

	for e in eval_data:
		eval_choices.append((e.id, e.name))

	form = NewEvalForm()
	form.eval_type_id.choices = eval_choices
	client = models.Client.query.get(client_id)

	if form.validate_on_submit():
		new_eval = models.ClientEvals(client_id=client_id, eval_type_id=form.eval_type_id.data,
		therapist_id=1)
		db.session.add(new_eval)
		db.session.commit()
		return redirect('/eval/' + str(new_eval.id) + '/1')

	return render_template('new_eval.html',
							form=form,
							# evals=evals,
							client=client)



# @app.route('/evaluation/<eval_type>/<subtest>/<eval_id>', methods=['GET', 'POST'])
@app.route('/eval/<eval_id>/<page_no>', methods=['GET', 'POST'])
def evaluation(eval_id, page_no): # eval_type, subtest, eval_id, methods=['GET', 'POST']):
	eval_data = models.ClientEvals.query.filter_by(id=eval_id).one()

	test_seq = json.loads(eval_data.eval.test_seq)

	page = int(page_no)

	if request.method == 'POST':
		for q in request.form:
			answer = models.ClientEvalAnswers(client_eval_id= eval_id,
											eval_questions_id=q,
											answer=request.form[q])
			db.session.add(answer)
		db.session.commit()

	if page == len(test_seq):
		return redirect('/clients')

	questions = models.EvalQuestions.query.filter(and_(models.EvalQuestions.evaluation == eval_data.eval.name, models.EvalQuestions.subtest == test_seq[page-1])).order_by(models.EvalQuestions.question_num)

	eval = {'name': eval_data.eval.name,
			'subtest': test_seq[page],
			'link':'/eval/' + eval_id + '/' + str(page + 1)}

	return render_template('eval.html',
							eval=eval,
							questions = questions)
