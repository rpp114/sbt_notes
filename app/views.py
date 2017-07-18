from flask import render_template, flash, redirect, jsonify, request, g, session, url_for
from app import app, models, db, oauth_credentials
from .forms import LoginForm, ClientInfoForm, NewEvalForm, ClientNoteForm, ClientAuthForm, UserInfoForm
from flask_security import login_required
from sqlalchemy import and_
import json, datetime, httplib2, json
from apiclient import discovery
from oauth2client import client


@app.route('/')
@app.route('/index')
# @login_required
def index():
	user = {'nickname': 'Ray'}

	posts = [{'author':{'nickname': 'John'},
			 'body': 'Nice day today'},
			 {'author':{'nickname': 'Susan'},
			 'body':'Yes it is'}]

	session['start_time'] = datetime.datetime.now()
	session['user_name'] = 'Ray'

	return render_template('index.html',
							title='Home',
							user=user,
							posts = posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		print(form.data)
		flash('Login requested for OpenId="%s", remember_me=%s' % (form.openid.data, str(form.remember_me.data)))
		return redirect('/index')
	return render_template('login.html',
							title='Sign In',
							form=form,
							providers=app.config['OPENID_PROVIDERS'])


@app.route('/users')
def users_page():
	users = models.User.query.filter_by(status='active').order_by(models.User.last_name)
	return render_template('users.html',
							users=users)

@app.route('/user/delete')
def delete_user():
	user = models.User.query.get(request.args.get('user_id'))
	user.status='inactive'
	db.session.commit()
	return redirect('/users')


@app.route('/user/profile', methods=['GET','POST'])
def user_profile():
	user_id = request.args.get('user_id')

	if user_id == None:
		user = {'first_name':'New',
		'last_name':'User'}
	else:
		user = models.User.query.get(user_id)

	form = UserInfoForm(obj=user)

	if form.validate_on_submit():

		user = models.User() if user_id == '' else models.User.query.get(user_id)

		user.first_name = form.first_name.data
		user.last_name = form.last_name.data
		user.email = form.email.data
		user.password = form.password.data
		user.calendar_access = form.cal_access.data
		db.session.add(user)
		db.session.commit()
		if user.calendar_access:
			if models.Therapist.query.filter_by(user_id=user.id).first() != None:
				therapist = models.Therapist.query.filter_by(user_id=user.id).first()
				therapist.status = 'active'
			else:
				therapist = models.Therapist()
				therapist.user_id = user.id
				db.session.add(therapist)
			db.session.commit()
		else:
			therapist = models.Therapist.query.filter_by(user_id=user.id).first()
			therapist.status = 'inactive'
			db.session.commit()

		if user.calendar_access and user.calendar_credentials == None:
			session['oauth_user_id'] = user.id
			return redirect('/oauth2callback')

		return redirect(url_for('users_page'))

	return render_template('user_profile.html',
	user=user,
	form=form)

@app.route('/oauth2callback')
def oauth2callback():
	google_oauth_secrets = oauth_credentials['google']['web']

	flow = client.OAuth2WebServerFlow(client_id=google_oauth_secrets['client_id'],
			client_secret=google_oauth_secrets['client_secret'],
			scope='https://www.googleapis.com/auth/calendar',
			redirect_uri=url_for('oauth2callback', _external=True))

	flow.params['access_type']='offline'
	flow.params['prompt']='consent'

	if 'code' not in request.args:
		auth_uri = flow.step1_get_authorize_url()
		return redirect(auth_uri)
	else:
		auth_code = request.args.get('code')
		credentials = flow.step2_exchange(auth_code)
		user = models.User.query.get(session['oauth_user_id'])
		user.calendar_credentials = json.dumps(credentials.to_json())
		db.session.add(user)
		db.session.commit()
		session.pop('oauth_user_id', None)
		# session['credentials'] = credentials.to_json()
		return redirect(url_for('users_page'))


@app.route('/clients')
def clients_page():
	clients = models.Client.query.filter_by(status='active').order_by(models.Client.last_name)
	# for stuff in session:
	# 	print(stuff, ': ', session[stuff])

	return render_template('clients.html',
							clients=clients,
							)

@app.route('/clients/archive')
def clients_archive_page():
	clients = models.Client.query.filter_by(status='inactive').order_by(models.Client.last_name)
	# for stuff in session:
	# 	print(stuff, ': ', session[stuff])

	return render_template('clients.html',
							clients=clients,
							)

@app.route('/eval_directory/<client_id>')
def eval_directory(client_id):
	client = models.Client.query.get(client_id)

	return render_template('eval_directory.html',
							client=client,
							evals=client.evals)

@app.route('/client/delete')
def delete_client():
	client = models.Client.query.get(request.args.get('client_id'))
	client.status='inactive'
	db.session.commit()
	return redirect('/clients')


@app.route('/client/profile', methods=['GET','POST'])
def client_profile():
	client_id = request.args.get('client_id')

	if client_id == None:
		client = {'first_name':'New',
				  'last_name':'Client'}
	else:
		client = models.Client.query.get(client_id)

	form = ClientInfoForm(obj=client)

	form.regional_center_id.choices = [(c.id, c.name) for c in models.RegionalCenter.query.all()]

	form.therapist_id.choices = [(t.id, t.user.first_name) for t in models.Therapist.query.filter(and_(models.Therapist.user.has(status = 'active'),models.Therapist.status == 'active'))]

	if form.validate_on_submit():

		client = models.Client() if client_id == '' else models.Client.query.get(client_id)

		client.first_name = form.first_name.data
		client.last_name = form.last_name.data
		client.birthdate = form.birthdate.data
		client.uci_id = form.uci_id.data
		client.address = form.address.data
		client.city = form.city.data
		client.state = form.state.data
		client.zipcode = form.zipcode.data
		client.phone = form.phone.data
		client.gender = form.gender.data
		client.regional_center_id = form.regional_center_id.data
		client.therapist_id = form.therapist_id.data
		db.session.add(client)
		db.session.commit()
		return redirect('/clients')

	return render_template('client_profile.html',
							client=client,
							form=form)


@app.route('/new_eval/<client_id>', methods=['GET', 'POST'])
def new_eval(client_id):
	form = NewEvalForm()

	if request.method == 'POST' and form.is_submitted():
		new_eval = models.ClientEval(client_id=client_id, therapist_id=1)
		new_eval.subtests = models.EvalSubtest.query.filter(models.EvalSubtest.id.in_(form.subtest_id.data)).all()
		db.session.add(new_eval)
		db.session.commit()
		return redirect('/eval/' + str(new_eval.id) + '/' + str(form.subtest_id.data[0]))

	form.subtest_id.choices = [(s.id, s.name) for s in models.EvalSubtest.query.order_by(models.EvalSubtest.eval_id, models.EvalSubtest.eval_subtest_id).all()]

	form.subtest_id.default = [s[0] for s in form.subtest_id.choices]

	form.process()

	client = models.Client.query.get(client_id)

	return render_template('new_eval.html',
							form=form,
							client=client)



@app.route('/eval/<eval_id>/<subtest_id>', methods=['GET', 'POST'])
def evaluation(eval_id, subtest_id):
	if request.method == 'POST':
		for q in request.form:
			answer = models.ClientEvalAnswer(client_eval_id= eval_id,
			eval_question_id=q,
			answer=request.form[q])
			db.session.add(answer)
		db.session.commit()

	if subtest_id == 'end':
		return redirect('/clients')

	subtest = models.EvalSubtest.query.get(subtest_id)
	subtest_sequence = models.ClientEval.query.get(eval_id).subtests

	subtest_ids = [s.id for s in sorted(subtest_sequence, key=lambda test: str(test.eval_id) + str(test.eval_subtest_id))]

	subtest_ids.append('end')

	subtest_index = subtest_ids.index(int(subtest_id))

	questions = subtest.questions.all()

	eval = {'name': subtest.eval.name,
			'subtest': subtest.name,
			'link':'/eval/' + eval_id + '/' + str(subtest_ids[subtest_index + 1])}

	return render_template('eval.html',
							eval=eval,
							questions=questions)

@app.route('/eval/<eval_id>/responses')
def eval_responses(eval_id):
	client_eval = models.ClientEval.query.get(eval_id)

	responses = {}

	for answer in client_eval.answers:
		eval_name = answer.question.subtest.eval.name
		sub_name = answer.question.subtest.name
		responses[eval_name] = responses.get(eval_name, {})
		responses[eval_name][sub_name] = responses[eval_name].get(sub_name, [])
		responses[eval_name][sub_name].append((answer.question.question_num,
						  answer.question.question,
						  answer.answer))
	for eval in responses:
		for t in responses[eval]:
			responses[eval][t] = sorted(responses[eval][t], key=lambda tup: tup[0])

	return render_template('eval_responses.html',
							responses=responses,
							eval=client_eval)

@app.route('/client/note', methods=['GET', 'POST'])
def client_notes():
	appt_id = request.args.get('appt_id')

	appt = models.ClientAppt.query.get(appt_id)

	appt.date_string = datetime.datetime.strftime(appt.start_datetime, '%b %-d, %Y at %-I:%M %p')

	form = ClientNoteForm() if appt.note == None else ClientNoteForm(notes=appt.note.note)

	if form.validate_on_submit():
		print('form answers', form.data)
		appt_note = models.ClientApptNote(note=form.notes.data, appt=appt)
		db.session.add(appt_note)
		db.session.commit()
		return redirect(url_for('clients_page'))

	return render_template('client_note.html',
							form=form,
							appt=appt)
