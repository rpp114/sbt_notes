from flask import render_template, flash, redirect, jsonify, request, g, session, url_for
from app import app, models, db, oauth_credentials, login_manager
from .forms import LoginForm, ClientInfoForm, ClientNoteForm, ClientAuthForm, UserInfoForm, LoginForm, PasswordChangeForm, RegionalCenterForm, ApptTypeForm, InvoiceCreateForm
from flask_login import login_required, login_user, logout_user, current_user
from sqlalchemy import and_
import json, datetime, httplib2, json, sys, os
from apiclient import discovery
from oauth2client import client
from werkzeug.security import generate_password_hash, check_password_hash
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../jobs'))
from billing import build_appt_xml



################################################
# Pages pertaining to SignUps and LogIns
################################################

@app.route('/')
@app.route('/index')
def index():
	if current_user.is_authenticated:
		return redirect(url_for('user_tasks'))
	else:
		form = LoginForm()
		return render_template('index.html',
		form=form)


@login_manager.user_loader
def load_user(id):
	return models.User.query.get(id)

@login_manager.token_loader
def load_token(token):

	print('loading cookie')
	max_age = app.config["REMEMBER_COOKIE_DURATION"].total_seconds()
	login_info = models.login_serializer.loads(token, max_age=max_age)
	user = User.get(data[0])

	if user and check_password_hash(user.password, data[1]):
		return user
	return None

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/password')
@login_required
def password_change():
	user_id = request.args.get('user_id')

	user = models.User.query.get(user_id)

	form = PasswordChangeForm()

	if form.validate_on_submit():
		user.password = generate_password_hash(form.password)
		db.session.add(user)
		db.session.commit()
		return redirect(url_for('user_profile', user_id=user.id))

	return render_template('password_reset.html',
							form=form,
							user=user)


@app.route('/secret')
@login_required
def secret():
	return render_template('secret.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	form = LoginForm()

	if request.method == 'GET':
		return render_template('signup.html', form=form)
	elif request.method == 'POST':
		if form.validate_on_submit():
			if models.User.query.filter_by(email=form.email.data).first():
				return "Email already exists"
			else:
				new_user = models.User(email=form.email.data, password=generate_password_hash(form.password.data))
				db.session.add(new_user)
				db.session.commit()

				login_user(new_user, remember=form.remember_me.data)

				# drop User on User page to see if they are a therapist

				return redirect(url_for('user_profile', user_id=new_user.id))
	else:
		return 'Form didn\'t Validate'



@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()

	if request.method == 'GET':
		return render_template('login.html',
								form=form)
	elif request.method == 'POST':
		if form.validate_on_submit():
			user = models.User.query.filter_by(email=form.email.data).first()
			if user:
				if check_password_hash(user.password, form.password.data):
					login_user(user, remember=form.remember_me.data)
					return redirect(url_for('user_tasks'))
				else:
					return redirect(url_for('index'))
			else:
				return redirect(url_for('signup'))
	else:
		return 'Form didn\'t Validate'


################################################
# Pages pertaining to Users
################################################

@app.route('/user/tasklist')
@login_required
def user_tasks():

	return render_template('user_tasklist.html',
							user=current_user)

@app.route('/users')
@login_required
def users_page():
	users = models.User.query.filter_by(status='active').order_by(models.User.last_name)
	return render_template('users.html',
							users=users)

@app.route('/user/delete')
@login_required
def delete_user():
	user = models.User.query.get(request.args.get('user_id'))
	user.status='inactive'
	db.session.commit()
	return redirect('/users')

@app.route('/user/profile', methods=['GET','POST'])
@login_required
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
		user.calendar_access = form.calendar_access.data
		db.session.add(user)
		if user.calendar_access:
			if models.Therapist.query.filter_by(user_id=user.id).first() != None:
				therapist = models.Therapist.query.filter_by(user_id=user.id).first()
				therapist.status = 'active'
			else:
				therapist = models.Therapist()
				therapist.user_id = user.id
				db.session.add(therapist)
		else:
			therapist = models.Therapist.query.filter_by(user_id=user.id).first()
			if therapist:
				therapist.status = 'inactive'
		db.session.commit()

		if user.calendar_access and user.calendar_credentials == None:
			session['oauth_user_id'] = user.id
			return redirect('/oauth2callback')

		return redirect(url_for('user_tasklist'))

	return render_template('user_profile.html',
	user=user,
	form=form)

# Oauth Callback

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
		return redirect(url_for('user_tasklist'))


######################################################
# Client pages including profiles and summaries
######################################################


@app.route('/clients')
@login_required
def clients_page():
	clients = models.Client.query.filter_by(status='active').order_by(models.Client.last_name)

	return render_template('clients.html',
							clients=clients,
							)
@app.route('/clients/archive')
@login_required
def clients_archive_page():
	clients = models.Client.query.filter_by(status='inactive').order_by(models.Client.last_name)
	# for stuff in session:
	# 	print(stuff, ': ', session[stuff])

	return render_template('clients.html',
							clients=clients,
							)

@app.route('/client/delete')
@login_required
def delete_client():
	client = models.Client.query.get(request.args.get('client_id'))
	client.status='inactive'
	db.session.commit()
	return redirect('/clients')


@app.route('/client/profile', methods=['GET','POST'])
@login_required
def client_profile():
	client_id = request.args.get('client_id')

	if client_id == None:
		client = {'first_name':'New',
				  'last_name':'Client',
					'appts': []}
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
		return redirect(url_for('clients_page'))

	return render_template('client_profile.html',
							client=client,
							form=form)


##############################################
# Pages dealing with Evaluations
##############################################


@app.route('/eval_directory/<client_id>')
@login_required
def eval_directory(client_id):
	client = models.Client.query.get(client_id)

	return render_template('eval_directory.html',
	client=client,
	evals=client.evals)

@app.route('/new_eval/<client_id>', methods=['GET', 'POST'])
@login_required
def new_eval(client_id):

	if request.method == 'POST':# and form.is_submitted():
		form_data = sorted([s for s in request.form])
		subtest_ids = [int(request.form[id]) for id in form_data]
		client = models.Client.query.get(client_id)
		new_eval = models.ClientEval(client=client, therapist=client.therapist)
		new_eval.subtests = models.EvalSubtest.query.filter(models.EvalSubtest.id.in_(subtest_ids)).all()
		db.session.add(new_eval)
		db.session.commit()
		return redirect('/eval/' + str(new_eval.id) + '/' + str(subtest_ids[0]))

	evals_form = []
	evals = [(e.id, e.name) for e in models.Evaluation.query.order_by(models.Evaluation.id)]

	for eval_type in evals:
		evals_form.append((eval_type[1], [(s.id, s.name) for s in models.EvalSubtest.query.filter(models.EvalSubtest.eval_id == eval_type[0]).order_by(models.EvalSubtest.eval_subtest_id).all()]))


	client = models.Client.query.get(client_id)

	return render_template('new_eval.html',
							evals_form=evals_form,
							client=client)


@app.route('/eval/<eval_id>/<subtest_id>', methods=['GET', 'POST'])
@login_required
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

@app.route('/eval/responses')
@login_required
def eval_responses():
	eval_id = request.args.get('eval_id')

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

###################################################
# Pages dealing with Client Appts and Notes
###################################################

@app.route('/client/note', methods=['GET', 'POST'])
@login_required
def client_note():
	appt_id = request.args.get('appt_id')

	appt = models.ClientAppt.query.get(appt_id)

	appt.date_string = datetime.datetime.strftime(appt.start_datetime, '%b %-d, %Y at %-I:%M %p')

	form = ClientNoteForm() if appt.note == None else ClientNoteForm(notes=appt.note.note)

	if form.validate_on_submit():
		appt_note = models.ClientApptNote(note=form.notes.data, appt=appt)
		db.session.add(appt_note)
		db.session.commit()
		return redirect(url_for('clients_page'))

	return render_template('client_note.html',
							form=form,
							appt=appt)


###########################################################
# Pages dealing with Client Authorizations
###########################################################


@app.route('/client/authorization', methods=['GET', 'POST'])
@login_required
def client_auth():
	client_auth_id = request.args.get('client_auth_id')
	client_id = request.args.get('client_id')

	client = models.Client.query.get(client_id)

	if client_auth_id != None:
		auth = models.ClientAuth.query.get(client_auth_id)
	elif client_id != None:
		auth = {'client_id': client_id}

	form = ClientAuthForm(obj=auth)

	if form.validate_on_submit():
		auth = models.ClientAuth() if client_auth_id == '' else models.ClientAuth.query.get(client_auth_id)
		auth.client = client
		auth.monthly_visits = form.monthly_visits.data
		auth.auth_start_date = form.auth_start_date.data
		auth.auth_end_date = form.auth_end_date.data
		auth.auth_id = form.auth_id.data
		db.session.add(auth)
		db.session.commit()

		return redirect(url_for('client_profile', client_id=client_id))

	return render_template('client_auth.html',
							client = client,
							form = form,
							auth = auth)


############################
# Billing Views
############################

@app.route('/billing')
@login_required
def billing():
	print(current_user)
	rcs = models.RegionalCenter.query.filter(models.RegionalCenter.id > 1).all()

	u_appts = models.ClientAppt.query.filter(models.ClientAppt.cancelled == 0,
							models.ClientAppt.billing_xml_id == None,
							models.ClientAppt.client.has(models.Client.regional_center_id > 1),
							models.ClientAppt.start_datetime < datetime.datetime.now().replace(day=1)).all()

	unbilled_appts = {}
	for rc in rcs:
		unbilled_appts[rc.id] = {'appts': 0, 'name': rc.name, 'auths': 0}

	for appt in u_appts:
		unbilled_appts[appt.client.regional_center.id]['appts'] += 1

	return render_template('billing.html',
							regional_centers=unbilled_appts)


@app.route('/billing/appt', methods=['POST', 'GET'])
@login_required
def billing_appt():
	center_id = request.args.get('center_id')
	#  Needs to be show all unbilled Appts and invoices

@app.route('/billing/invoice', methods=['POST', 'GET'])
@login_required
def billing_invoice():
	invoice_id = request.args.get('invoice_id')
	start_date = request.args.get('start_date')
	end_date = request.args.get('end_date')
	center_id = request.args.get('center_id')

	if invoice_id != None:
		invoice = models.BillingXml.query.get(invoice_id)
		invoice_xml = ElementTree.parse(invoice.file_link)
		new_invoice = False
		notes = []
		for note in invoice.notes:
			notes.append(note.note)
	else:
		if start_date == None and end_date == None:
			end_date = datetime.datetime.now().replace(day=1) - datetime.timedelta(1)
			start_date = end_date.replace(day=1)
		else:
			start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
			end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

		start_date = start_date.replace(hour=0, minute=0, second=0)
		end_date = end_date.replace(hour=23, minute=59, second=59)

		appts = models.ClientAppt.query.filter(models.ClientAppt.start_datetime >= start_date,
											models.ClientAppt.start_datetime <= end_date,
											models.ClientAppt.client.has(models.Client.regional_center_id == center_id),
											models.ClientAppt.cancelled == 0,
											models.ClientAppt.billing_xml_id == None)

		invoice_obj = build_appt_xml(appts)

		new_invoice = True
		invoice_xml = invoice_obj[0]['invoice']
		notes = invoice_obj[0]['notes']


	root_element = invoice_xml.getroot()

	appts_for_grid = []

	appt_count = 0

	for child in root_element:
		appt = {}
		appt['firstname'] = child.find('firstname').text
		appt['lastname'] = child.find('lastname').text
		appt_type_name = models.ApptType.query.filter(models.ApptType.service_type_code == child.find('SVCSCode').text).first()
		appt['appt_type'] = appt_type_name.name
		appt['total_appts'] = child.find('EnteredUnits').text
		appt_count += int(appt['total_appts'])
		appt['appts'] = []
		appt_month = datetime.datetime.strptime(child.find('SVCMnYr').text, '%Y-%m-%d')
		last_day = appt_month.replace(month=(appt_month.month + 1) %12) - datetime.timedelta(1)
		for day in range(1,last_day.day+1):
			appt['appts'].append('' if child.find('Day' + str(day)).text == None else child.find('Day' + str(day)).text)


		appts_for_grid.append(appt)

	form = InvoiceCreateForm()

	appts_for_grid.sort(key=lambda x: x['firstname'])

	return render_template('invoice_grid.html',
							appt_count=appt_count,
							appts_for_grid=appts_for_grid,
							days=last_day.day,
							form=form,
							notes=notes,
							new_invoice=new_invoice)



	# Shows summary and all appts billed in a grid with invoice notes


##################################
#  Regional Center Views
##################################

@app.route('/regional_center', methods=['POST', 'GET'])
@login_required
def regional_center():
	center_id = request.args.get('center_id')

	if center_id == None:
		regional_center = {}
	else:
		regional_center = models.RegionalCenter.query.get(center_id)

	form = RegionalCenterForm(obj=regional_center)

	if form.validate_on_submit():
		center = models.RegionalCenter() if center_id == '' else models.RegionalCenter.query.get(center_id)

		center.name = form.name.data
		center.address = form.address.data
		center.city = form.city.data
		center.state = form.state.data
		center.zipcode = form.zipcode.data
		center.rc_id = form.rc_id.data
		center.primary_contact_name = form.primary_contact_name.data
		center.primary_contact_phone = form.primary_contact_phone.data
		center.primary_contact_email = form.primary_contact_email.data

		db.session.add(center)
		db.session.commit()

		return redirect(url_for('billing'))

	return render_template('regional_center.html',
							form=form,
							center=regional_center)


@app.route('/appt_types')
@login_required
def appt_types():
	center_id = request.args.get('center_id')

	regional_center = models.RegionalCenter.query.get(center_id)

	return render_template('appt_types.html',
							center = regional_center)



@app.route('/appt_type', methods=['POST', 'GET'])
@login_required
def appt_type():
	appt_type_id = request.args.get('appt_type_id')
	center_id = request.args.get('center_id')

	appt_type = {} if appt_type_id == None else models.ApptType.query.get(appt_type_id)

	form = ApptTypeForm(obj=appt_type)

	if form.validate_on_submit():
		type = models.ApptType() if appt_type_id == '' else models.ApptType.query.get(appt_type_id)

		type.name = form.name.data
		type.service_code = form.service_code.data
		type.service_type_code = form.service_type_code.data
		type.rate = form.rate.data
		type.regional_center_id = center_id

		db.session.add(type)
		db.session.commit()

		return redirect(url_for('appt_types', center_id=center_id))

	return render_template('appt_type.html',
							form=form,
							type=appt_type,
							center_id=center_id)


@app.route('/appt_type/delete')
@login_required
def appt_type_delete():
	appt_type_id = request.args.get('appt_type_id')
	center_id = request.args.get('center_id')

	type = models.ApptType.query.get(appt_type_id)

	db.session.delete(type)
	db.session.commit()

	return redirect(url_for('appt_types', center_id=center_id))
