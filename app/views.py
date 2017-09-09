from flask import render_template, flash, redirect, jsonify, request, g, session, url_for, Markup
from app import app, models, db, oauth_credentials, login_manager
from .forms import LoginForm, ClientInfoForm, ClientNoteForm, ClientAuthForm, UserInfoForm, LoginForm, PasswordChangeForm, RegionalCenterForm, ApptTypeForm, DateSelectorForm, CompanyForm, NewUserInfoForm
from flask_login import login_required, login_user, logout_user, current_user
from sqlalchemy import and_, desc
import json, datetime, httplib2, json, sys, os
from apiclient import discovery
from oauth2client import client
from werkzeug.security import generate_password_hash, check_password_hash
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../jobs'))
from billing import build_appt_xml, get_appts_for_grid
from appts import insert_auth_reminder, move_appts


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

@login_manager.unauthorized_handler
def needs_login():
	flash('You have to log in to access this page.')
	return redirect(url_for('index', next=request.path))

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

@app.route('/password', methods=['GET', 'POST'])
@login_required
def password_change():
	user_id = request.args.get('user_id')

	user = models.User.query.get(user_id)

	form = PasswordChangeForm()

	if form.validate_on_submit():
		user.password = generate_password_hash(form.password.data)
		user.first_time_login = False
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
			if models.User.query.filter_by(email=form.email.data.lower()).first():
				flash('That Email Already Exists. Please log in.')
				return redirect(url_for('index'))
			else:
				new_user = models.User(email=form.email.data.lower(), password=generate_password_hash(form.password.data))
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

	dest_url = request.args.get('next')

	if request.method == 'GET':
		return render_template('index.html',
								form=form)
	elif request.method == 'POST':
		if form.validate_on_submit():
			user = models.User.query.filter_by(email=form.email.data.lower()).first()
			if user:
				if check_password_hash(user.password, form.password.data):
					login_user(user, remember=form.remember_me.data)
					if user.first_time_login == 1:
						return redirect(url_for('password_change', user_id=current_user.id))
					if not dest_url:
						dest_url = url_for('user_tasks')
					return redirect(dest_url)
				else:
					flash('Please Check Your Password.')
					return redirect(url_for('index'))
			else:
				flash('Please Check Your Email')
				return redirect(url_for('index'))
	else:
		return redirect(url_for('index'))


################################################
# Pages pertaining to Users
################################################

@app.route('/user/tasklist')
@login_required
def user_tasks():
	if current_user.role_id == 4:
		return redirect(url_for('clients_page'))

	therapist = current_user.therapist
	notes_needed = []
	notes_needing_approval = []
	clients_need_info = []
	auths_need_renewal = []
	new_auths_needed = []
	reports_to_write = []

	if therapist:
		notes_needed = models.ClientAppt.query.filter(models.ClientAppt.therapist_id == therapist.id,
										models.ClientAppt.note == None,
										models.ClientAppt.cancelled == 0)\
										.order_by(models.ClientAppt.start_datetime).all()

		notes_needing_approval = models.ClientApptNote.query.filter(models.ClientApptNote.approved == False, models.ClientApptNote.appt.has(cancelled = 0), models.ClientApptNote.appt.has(therapist_id = therapist.id)).all()

		clients_need_info = models.Client.query.filter(models.Client.therapist_id == therapist.id,
										models.Client.uci_id == None)\
										.order_by(models.Client.first_name).all()

		# evals_need_reports = models.ClientEval.query.filter(models.ClientEval.therapist_id == current_user.therapist.id,
													# need to link report to Eval to pull query)

		if current_user.role_id < 3:
			auths_need_renewal = db.session.query(models.ClientAuth).join(models.Client).join(models.Therapist)\
										.filter(models.ClientAuth.status == 'active',
										models.Client.status == 'active',
										models.ClientAuth.auth_end_date <= datetime.datetime.now(), models.ClientAuth.is_eval_only == 0,
										models.Therapist.company_id == therapist.company_id)\
										.order_by(models.ClientAuth.auth_end_date).all()

			new_auths_needed = models.Client.query.filter(models.Client.auths == None,
												models.Client.status == 'active').order_by(models.Client.first_name).all()

	return render_template('user_tasklist.html',
							user=current_user,
							notes=notes_needed,
							approval_notes=notes_needing_approval,
							clients=clients_need_info,
							reports=reports_to_write,
							old_auths=auths_need_renewal,
							new_auths=new_auths_needed)

@app.route('/users')
@login_required
def users_page():

	if current_user.role_id > 3:
		return redirect(url_for('user_tasks'))


	company_id = request.args.get('company_id')

	if not company_id or current_user.role_id > 1:
		company_id = current_user.company_id

	if current_user.role_id == 3:
		users = models.User.query.filter(models.User.status=='active',\
							models.User.company_id==company_id,\
							models.User.role_id==4,\
							models.User.intern.has(therapist_id=current_user.therapist.id))\
							.order_by(models.User.last_name)
	else:
		users = models.User.query.filter(models.User.status=='active',\
	 			models.User.company_id==company_id,\
				models.User.role_id > 1).order_by(models.User.last_name)

	return render_template('users.html',
							users=users,
							company_id=company_id)

@app.route('/user/appts', methods=['GET', 'POST'])
@login_required
def user_appts():
	user_id = request.args.get('user_id')

	if current_user.role_id > 2:
		user_id = current_user.id

	form = DateSelectorForm()

	if request.method == 'POST':
		start_date = form.start_date.data
		end_date = form.end_date.data
	else:
		start_date = datetime.datetime.now().replace(day=1, hour=00, minute=00)
		end_date = datetime.datetime.now()

	user = models.User.query.get(user_id)

	appts = models.ClientAppt.query.filter(models.ClientAppt.therapist_id == user.therapist.id,
							models.ClientAppt.start_datetime >= start_date,
							models.ClientAppt.end_datetime <= end_date).all()

	appt_summary = {'Private': {'appts': 0, 'multiplier': 2},
					'treatment': {'appts': 0, 'multiplier': 1},
					'evaluation': {'appts': 0, 'multiplier': 3}}

	for appt in appts:
		if appt.client.regional_center.name == 'Private':
			appt_summary['Private']['appts'] += 1
		else:
			appt_summary[appt.appt_type.name]['appts'] += 1

	return render_template('user_appts.html',
							appts=appt_summary,
							user=user,
							form=form,
							start_date=start_date,
							end_date=end_date)

@app.route('/user/delete')
@login_required
def delete_user():
	user = models.User.query.get(request.args.get('user_id'))
	user.status='inactive'
	db.session.commit()
	return redirect('/users')


@app.route('/user/new', methods=['GET', 'POST'])
@login_required
def new_user():
	company_id = request.args.get('company_id')

	if current_user.role_id > 1:
		company_id = str(current_user.company_id)

	company = models.Company.query.get(company_id)

	form = NewUserInfoForm()

	form.role_id.choices = [(role.id, role.name) for role in models.Role.query.filter(models.Role.id >= current_user.role_id).all()]

	if form.validate_on_submit():
		user = models.User()

		user.first_name = form.first_name.data
		user.last_name = form.last_name.data
		user.email = form.email.data.lower()
		user.calendar_access = form.calendar_access.data
		user.role_id = form.role_id.data
		user.company_id = company_id
		user.password = generate_password_hash(form.password.data)
		db.session.add(user)
		db.session.commit()

		return redirect(url_for('users_page', company_id=company_id))

	return render_template('new_user_profile.html',
						form=form,
						company=company)


@app.route('/user/profile', methods=['GET','POST'])
@login_required
def user_profile():
	user_id = request.args.get('user_id')

	if current_user.role_id > 3 and user_id != str(current_user.id):
		return redirect(url_for('user_profile', user_id=current_user.id))

	user = models.User.query.get(user_id)

	form = UserInfoForm(obj=user)

	form.role_id.choices = [(role.id, role.name) for role in models.Role.query.filter(models.Role.id >= current_user.role_id).all()]

	form.therapist_id.choices = [(t.id, t.user.first_name) for t in models.Therapist.query.filter(and_(models.Therapist.user.has(status = 'active'), models.Therapist.user.has(company_id = user.company_id), models.Therapist.status == 'active'))]
	if request.method == 'POST':
		user = models.User() if user_id == '' else models.User.query.get(user_id)

		user.first_name = form.first_name.data
		user.last_name = form.last_name.data
		user.email = form.email.data
		user.calendar_access = form.calendar_access.data
		user.role_id = form.role_id.data
		db.session.add(user)
		if user.role_id == 4 and form.therapist_id.data:
			intern = models.Intern.query.filter_by(user_id=user.id).first()
			if not intern:
				intern = models.Intern(user_id=user.id)
			intern.therapist_id=form.therapist_id.data
			db.session.add(intern)
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

		if user.calendar_access and user.therapist.calendar_credentials == None:
			session['oauth_user_id'] = user.id
			return redirect('/oauth2callback')

		return redirect(url_for('users_page'))

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
		user.therapist.calendar_credentials = json.dumps(credentials.to_json())
		db.session.add(user)
		db.session.commit()
		session.pop('oauth_user_id', None)
		# session['credentials'] = credentials.to_json()
		return redirect(url_for('user_tasks'))


######################################################
# Company Profile Pages for Site Admin
######################################################

@app.route('/companies')
@login_required
def companies():
	if current_user.role_id > 1:
		companies = [models.Company.query.get(current_user.company_id)]
	else:
		companies = models.Company.query.all()

	return render_template('companies.html',
							companies=companies)

@app.route('/company', methods=['GET','POST'])
@login_required
def company_page():
	company_id = request.args.get('company_id')

	if company_id == None:
		company = {}
	else:
		company = models.Company.query.get(company_id)

	form = CompanyForm(obj=company)

	if form.validate_on_submit():
		company = models.Company() if company_id == '' else models.Company.query.get(company_id)

		company.name = form.name.data
		company.address = form.address.data
		company.city = form.city.data
		company.state = form.state.data
		company.zipcode = form.zipcode.data
		company.vendor_id = form.vendor_id.data

		db.session.add(company)
		db.session.commit()

		return redirect(url_for('companies'))

	return render_template('company.html',
							form=form,
							company=company)




######################################################
# Client pages including profiles and summaries
######################################################


@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients_page():

	therapist = current_user.therapist

	if current_user.id == 1:
		therapist = models.Therapist.query.get(1)

	if current_user.role_id == 4:
		intern = models.Intern.query.filter_by(user_id = current_user.id).first()
		therapist = intern.therapist

	if request.method == 'POST' and request.form.get('therapist', None):
		therapist = models.Therapist.query.get(request.form['therapist'])

	center_id = 0
	clients = []
	therapists = []
	archive = False

	if current_user.role_id < 3:
		therapists = models.Therapist.query.filter(models.Therapist.user.has(company_id =  current_user.company_id, status = 'active'), models.Therapist.status == 'active').all()

	if therapist:
		if request.method == 'POST' and request.form['regional_center'] != '0':
			clients = models.Client.query.filter_by(status='active',\
			regional_center_id=request.form['regional_center'],\
			therapist_id = therapist.id)\
			.order_by(models.Client.last_name).all()
			center_id = int(request.form['regional_center'])
		else:
			clients = models.Client.query.filter_by(status='active',\
			therapist_id = therapist.id)\
			.order_by(models.Client.last_name).all()


	rcs = models.RegionalCenter.query.filter_by(company_id=therapist.user.company_id).all()

	return render_template('clients.html',
							clients=clients,
							rcs=rcs,
							center_id=center_id,
							therapist_id=therapist.id,
							therapists=therapists,
							archive=archive)

@app.route('/clients/archive', methods=['GET', 'POST'])
@login_required
def clients_archive_page():
	therapist = current_user.therapist

	if current_user.id == 1:
		therapist = models.Therapist.query.get(1)

	if current_user.role_id == 4:
		intern = models.Intern.query.filter_by(user_id = current_user.id).first()
		therapist = intern.therapist

	if request.method == 'POST' and request.form.get('therapist', None):
		therapist = models.Therapist.query.get(request.form['therapist'])

	center_id = 0
	clients = []
	therapists = []
	archive = True

	if current_user.role_id < 3:
		therapists = models.Therapist.query.filter(models.Therapist.user.has(company_id =  current_user.company_id, status = 'active'), models.Therapist.status == 'active').all()

	if therapist:
		if request.method == 'POST' and request.form['regional_center'] != '0':
			clients = models.Client.query.filter_by(status='inactive',\
			regional_center_id=request.form['regional_center'],\
			therapist_id = therapist.id)\
			.order_by(models.Client.last_name).all()
			center_id = int(request.form['regional_center'])
		else:
			clients = models.Client.query.filter_by(status='inactive',\
			therapist_id = therapist.id)\
			.order_by(models.Client.last_name).all()


	rcs = models.RegionalCenter.query.filter_by(company_id=therapist.user.company_id).all()

	return render_template('clients.html',
							clients=clients,
							rcs=rcs,
							center_id=center_id,
							therapist_id=therapist.id,
							therapists=therapists,
							archive=archive)

@app.route('/client/status')
@login_required
def change_client_status():

	client_id = request.args.get('client_id')

	client = models.Client.query.get(client_id)
	if client.status == 'active':
		client.status = 'inactive'
		flash('Archived %s %s' % (client.first_name, client.last_name))
	else:
		client.status = 'active'
		flash('Activated %s %s' % (client.first_name, client.last_name))
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

	form.therapist_id.choices = [(t.id, t.user.first_name) for t in models.Therapist.query.filter(and_(models.Therapist.user.has(status = 'active'), models.Therapist.user.has(company_id = current_user.company_id), models.Therapist.status == 'active'))]

	if form.validate_on_submit():

		client = models.Client() if client_id == '' else models.Client.query.get(client_id)

		client.first_name = form.first_name.data
		client.last_name = form.last_name.data
		client.birthdate = datetime.datetime.strptime(form.birthdate.data, '%m/%d/%Y')
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
		flash('%s %s information updated.' % (client.first_name, client.last_name))
		# make it so if the therapist changes you move the appts from one to the other
		# move_appts(from , to , client_name, from_date, to_date optional)
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
# Change the link so it works through email, unless the form works in email?  with /client/note/<appt_id>
@app.route('/client/note', methods=['GET', 'POST'])
@login_required
def client_note():
	appt_id = request.args.get('appt_id')

	appt = models.ClientAppt.query.get(appt_id)

	appt.date_string = datetime.datetime.strftime(appt.start_datetime, '%b %-d, %Y at %-I:%M %p')

	form = ClientNoteForm() if appt.note == None else ClientNoteForm(approved=appt.note.approved, notes=appt.note.note)

	if request.method == 'POST':

		if request.form.get('appt_date', False) or request.form.get('appt_time', False):

			new_datetime = appt.start_datetime
			duration = appt.end_datetime - appt.start_datetime

			if request.form.get('appt_date', False):
				date = datetime.datetime.strptime(request.form.get('appt_date'), '%m/%d/%Y')
				new_datetime = new_datetime.replace(year=date.year, month=date.month, day=date.day)


			if request.form.get('appt_time', False):
				time = datetime.datetime.strptime(request.form.get('appt_time'), '%I:%M%p')
				new_datetime = new_datetime.replace(hour=time.hour, minute=time.minute, second=00)
			flash('Appt for %s moved from %s to %s' %(appt.client.first_name + ' ' + appt.client.last_name, appt.start_datetime.strftime('%b %d, %Y'), new_datetime.strftime('%b %d, %Y')))
			appt.start_datetime = new_datetime
			appt.end_datetime = new_datetime + duration

		if appt.note == None:
			appt_note = models.ClientApptNote(note=form.notes.data, appt=appt, user_id=current_user.id)
		else:
			appt_note = appt.note

		appt.cancelled = 0
		if form.cancelled.data:
			appt.cancelled = 1

		appt_note.approved = 0

		if current_user.role_id <= 3 or form.approved.data:
			appt_note.approved = 1

		db.session.add(appt_note)
		db.session.add(appt)
		db.session.commit()
		flash('Appt note added for %s' %(appt.client.first_name + ' ' + appt.client.last_name))
		return redirect(url_for('user_tasks'))

	form.cancelled.data = appt.cancelled

	return render_template('client_note.html',
							form=form,
							appt=appt)


@app.route('/client/appts', methods=['GET', 'POST'])
@login_required
def client_appts():
	client_id = request.args.get('client_id')
	start_date = request.args.get('start_date')
	end_date = request.args.get('end_date')

	form = DateSelectorForm()

	if request.method == 'POST':
		form_start_date = request.form.get('start_date', None)
		form_end_date = request.form.get('end_date', None)

		if form_start_date == None:
			start_date = datetime.datetime.now().replace(day=1)
		else:
			form_start_date = datetime.datetime.strptime(form_start_date, '%m/%d/%Y')
			start_date = datetime.datetime.combine(form_start_date, datetime.datetime.min.time())

		if form_end_date== None:
			end_date = datetime.datetime.now()
		else:
			form_end_date = datetime.datetime.strptime(form_end_date, '%m/%d/%Y')
			end_date = datetime.datetime.combine(form_end_date, datetime.datetime.min.time())
	elif start_date != None and end_date != None:
		start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
	else:
		end_date = datetime.datetime.now()
		start_date = end_date - datetime.timedelta(30)

	start_date = start_date.replace(hour=0, minute=0, second=0)
	end_date = end_date.replace(hour=23, minute=59, second=59)

	client = models.Client.query.get(client_id)

	appts = models.ClientAppt.query.filter(models.ClientAppt.client_id == client_id,
										models.ClientAppt.start_datetime >= start_date,
										models.ClientAppt.end_datetime <= end_date)\
										.order_by(models.ClientAppt.start_datetime).all()


	return render_template('client_appts.html',
						client=client,
						appts=appts,
						form=form,
						start_date=start_date,
						end_date=end_date)


@app.route('/client/notes', methods=['GET', 'POST'])
@login_required
def client_notes():
	client_id = request.args.get('client_id')
	start_date = request.args.get('start_date')
	end_date = request.args.get('end_date')

	start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
	end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

	client = models.Client.query.get(client_id)

	appts = models.ClientAppt.query.filter(models.ClientAppt.client_id == client_id,
										models.ClientAppt.start_datetime >= start_date,
										models.ClientAppt.end_datetime <= end_date)\
										.order_by(models.ClientAppt.start_datetime).all()

	return render_template('client_notes.html',
							client=client,
							appts=appts,
							start_date=start_date,
							end_date=end_date)



###########################################################
# Pages dealing with Client Goals
###########################################################

@app.route('/client/goal', methods=['GET', 'POST'])
@login_required
def client_goal():
	goal_id = request.args.get('goal_id')
	client_id = request.args.get('client_id')
	copy = request.args.get('copy')

	client = None
	goal = None

	if client_id:
		client = models.Client.query.get(client_id)

	if goal_id:
		goal = models.ClientGoal.query.get(goal_id)

	if request.method == 'POST':
		if not goal:
			goal_text = client.first_name + ' will ' + request.form['goal']
		else:
			goal_text = request.form['goal']

		goal = goal if goal else models.ClientGoal()

		goal.goal = goal_text
		goal.client_id = client.id
		db.session.add(goal)
		db.session.commit()

		return redirect(url_for('client_goals', client_id=client_id))

	return render_template('client_goal.html',
							client=client,
							goal=goal)

@app.route('/client/goals', methods=['GET', 'POST'])
@login_required
def client_goals():

	client_id = request.args.get('client_id')
	start_date = request.args.get('start_date')
	end_date = request.args.get('end_date')

	form = DateSelectorForm()

	if request.method == 'POST':

		form_start_date = request.form.get('start_date', None)
		form_end_date = request.form.get('end_date', None)

		for goal_id in request.form:
			if goal_id not in ['start_date', 'end_date', 'csrf_token']:
				if request.form.get(goal_id):
					goal = models.ClientGoal.query.get(goal_id)
					goal.goal_status = request.form.get(goal_id)
					db.session.add(goal)
					db.session.commit()

		if form_start_date == None:
			start_date = datetime.datetime.now().replace(day=1)
		else:
			form_start_date = datetime.datetime.strptime(form_start_date, '%m/%d/%Y')
			start_date = datetime.datetime.combine(form_start_date, datetime.datetime.min.time())

		if form_end_date== None:
			end_date = datetime.datetime.now()
		else:
			form_end_date = datetime.datetime.strptime(form_end_date, '%m/%d/%Y')
			end_date = datetime.datetime.combine(form_end_date, datetime.datetime.min.time())

		start_date = start_date.strftime('%Y-%m-%d')
		end_date = end_date.strftime('%Y-%m-%d')

		return redirect(url_for('client_goals', client_id=client_id, start_date=start_date, end_date=end_date))

	elif start_date != None and end_date != None:

		start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
	else:
		end_date = datetime.datetime.now()
		start_date = end_date - datetime.timedelta(30)

	start_date = start_date.replace(hour=0, minute=0, second=0)
	end_date = end_date.replace(hour=23, minute=59, second=59)

	client = models.Client.query.get(client_id)

	goals = models.ClientGoal.query.filter(models.ClientGoal.client_id == client.id,
										models.ClientGoal.created_date >= start_date,
										models.ClientGoal.created_date <= end_date)\
										.order_by(models.ClientGoal.created_date).all()

	return render_template('client_goals.html',
						client=client,
						goals=goals,
						form=form,
						start_date=start_date,
						end_date=end_date)


###########################################################
# Pages dealing with Client Authorizations
###########################################################
@app.route('/client/auths', methods=['GET'])
@login_required
def client_auths():
	client_id = request.args.get('client_id')

	client = models.Client.query.get(client_id)

	auths = models.ClientAuth.query.filter(models.ClientAuth.client_id == client_id).order_by(models.ClientAuth.auth_start_date).all()

	return render_template('client_auths.html',
						client=client,
						auths=auths)

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
		if client_auth_id == '':
			auths = client.auths
			for a in auths:
				a.status = 'inactive'
				db.session.add(a)
			auth = models.ClientAuth()
		else:
			auth = models.ClientAuth.query.get(client_auth_id)
		auth.client = client
		auth.monthly_visits = form.monthly_visits.data
		print(form.auth_start_date.data)
		auth.auth_start_date = datetime.datetime.strptime(form.auth_start_date.data, '%m/%d/%Y').strftime('%Y-%m-%d')
		auth.auth_end_date = datetime.datetime.strptime(form.auth_end_date.data, '%m/%d/%Y').strftime('%Y-%m-%d')
		auth.is_eval_only = form.is_eval_only.data
		auth.auth_id = form.auth_id.data
		db.session.add(auth)
		db.session.commit()

		if not auth.is_eval_only and client_auth_id == '':
			insert_auth_reminder(auth)
			flash('Auth Reminder for %s inserted into Google Calendar' % (client.first_name + ' ' + client.last_name))

		return redirect(url_for('client_auths', client_id=client_id))

	return render_template('client_auth.html',
							client = client,
							form = form,
							auth = auth)


############################
# Billing Views
############################

@app.route('/billing', methods=['POST', 'GET'])
@login_required
def billing_appt():

	company_id = request.args.get('company_id', None)

	if current_user.role_id > 1 or not company_id:
		company_id = current_user.company_id

	if request.method == 'POST':
		new_appts = []
		for x in request.form:
			appt_list = request.form.getlist(x)
			for y in appt_list:
				z = y.split(',')
				new_appts += z
		new_appts = [models.ClientAppt.query.get(a) for a in new_appts]

		monthly_billing(new_appts)


	appts = db.session.query(models.ClientAppt).join(models.Client).join(models.Therapist).join(models.User)\
		.filter(models.ClientAppt.start_datetime <= datetime.datetime.now().replace(day=1, hour=0, minute=0),
		models.ClientAppt.cancelled == 0,
		models.ClientAppt.billing_xml_id == None,
		models.User.company_id == company_id)\
		.order_by(models.Client.first_name).all()

	unbilled_appts = {}

	for appt in appts:
		regional_center = appt.appt_type.regional_center.name
		unbilled_appts[regional_center] = unbilled_appts.get(regional_center, {})
		billing_month_date = appt.start_datetime.replace(day=1)
		billing_month = billing_month_date.strftime('%Y-%m-%d')
		client_id = appt.client.first_name + ' ' + appt.client.last_name + ':' + str(appt.client.id)
		unbilled_appts[regional_center][billing_month] = unbilled_appts[regional_center].get(billing_month, {'date': appt.start_datetime.replace(day=1).strftime('%b %Y'),'clients': {}})
		unbilled_appts[regional_center][billing_month]['clients'][client_id] = unbilled_appts[regional_center][billing_month]['clients'].get(client_id, {'appts': [], 'auth': False})
		for auth in appt.client.auths.order_by(models.ClientAuth.created_date).all():
			if billing_month_date >= auth.auth_start_date.replace(day=1) and billing_month_date <= auth.auth_end_date:
				unbilled_appts[regional_center][billing_month]['clients'][client_id]['auth'] = True

		unbilled_appts[regional_center][billing_month]['clients'][client_id]['appts'].append(str(appt.id))

	rcs = models.RegionalCenter.query.order_by(models.RegionalCenter.id).all()

	# Need to sort the client list by name so they are ordered.

	return render_template('billing_appts.html',
							unbilled_appts=unbilled_appts,
							rcs=rcs)

@app.route('/billing/invoices', methods=['POST', 'GET'])
@login_required
def center_invoices():
	rc_id = request.args.get('center_id')
	start_date = request.args.get('start_date')
	end_date = request.args.get('end_date')

	form = DateSelectorForm()

	if request.method == 'POST':
		start_date = datetime.datetime.combine(form.start_date.data, datetime.datetime.min.time())
		end_date = datetime.datetime.combine(form.end_date.data, datetime.datetime.min.time())
	elif start_date != None and end_date != None:
		start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
		end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
	else:
		end_date = datetime.datetime.now()
		start_date = end_date.replace(day=1)

	start_date = start_date.replace(hour=0, minute=0, second=0)
	end_date = end_date.replace(hour=23, minute=59, second=59)

	rc = models.RegionalCenter.query.get(rc_id)


	xmls = models.BillingXml.query\
	.filter(models.BillingXml.regional_center_id == rc.id,
			models.BillingXml.created_date >= start_date,\
			models.BillingXml.created_date <= end_date)\
	.order_by(desc(models.BillingXml.created_date), desc(models.BillingXml.billing_month))

	return render_template('regional_center_invoices.html',
					form=form,
					rc=rc,
					start_date=start_date,
					end_date=end_date,
					invoices=xmls)



	#  Needs to be show all unbilled Appts and invoices

@app.route('/billing/monthly', methods=['POST', 'GET'])
@login_required
def monthly_billing(appts=[]):

	center_id = request.args.get('center_id')
	file_link = None

	if appts:
		invoices = build_appt_xml(appts, write=True)
		# print(invoices)
		for invoice in invoices:
			if invoice['xml_invoice_id']:
				xml_invoice = models.BillingXml.query.get(invoice['xml_invoice_id'])
				rc_name = xml_invoice.regional_center.name
				flash(Markup('Created Invoice for <a href="/billing/invoice?invoice_id=%s">%s for %s</a>' % (xml_invoice.id, rc_name, xml_invoice.billing_month.strftime('%b %Y'))))


		return redirect(url_for('billing_appt'))

	else:
		end_date = datetime.datetime.now().replace(day=1, hour=23, minute=59, second=59) - datetime.timedelta(1)
		start_date = end_date.replace(day=1, hour=00, minute=00, second=00)

		end_date_max = start_date - datetime.timedelta(1)
		start_date_max = end_date_max.replace(day=1)

		max_appts = db.session.query(models.ClientAppt).join(models.ClientApptNote).join(models.Client)\
						.filter(models.ClientAppt.start_datetime >= start_date_max,
						models.ClientAppt.start_datetime <= end_date_max,
						models.ClientApptNote.note.like('Max%'),
						models.ClientAppt.cancelled == 0,
						models.Client.regional_center_id == center_id).all()

		appts = db.session.query(models.ClientAppt).join(models.Client)\
						.filter(models.ClientAppt.start_datetime >= start_date,
						models.ClientAppt.end_datetime <= end_date,
						models.ClientAppt.cancelled == 0,
						models.Client.regional_center_id == center_id).all()

		if request.method == 'GET':
			invoice = build_appt_xml(appts, maxed_appts=max_appts, write=False)[0]
		else:
			invoice = build_appt_xml(appts, maxed_appts=max_appts, write=True)[0]
			# print(invoice)
			return redirect(url_for('billing_invoice', invoice_id = invoice['xml_invoice_id']))

		rc = models.RegionalCenter.query.get(center_id)

		if len(invoice) > 0:
			invoice_summary = get_appts_for_grid(invoice['invoice'],invoice['notes'])
		else:
			flash('No Appts to Generate Invoice From')
			return redirect(url_for('billing_appt'))

		return render_template('invoice_grid.html',
								appt_count=invoice_summary['appt_count'],
								appt_amount=invoice_summary['appt_amount'],
								appts_for_grid=invoice_summary['appts_for_grid'],
								daily_totals=invoice_summary['daily_totals'],
								days=invoice_summary['days'],
								notes=invoice_summary['notes'],
								file_link=file_link,
								start_date=start_date,
								rc=rc)


@app.route('/billing/invoice', methods=['POST', 'GET'])
@login_required
def billing_invoice():
	invoice_id = request.args.get('invoice_id')

	invoice = models.BillingXml.query.get(invoice_id)
	invoice_xml = ElementTree(file=invoice.file_link)
	file_link = invoice.file_link
	notes = invoice.notes.all()

	start_date = invoice.billing_month
	rc = invoice.regional_center

	invoice_summary = get_appts_for_grid(invoice_xml, notes)

	return render_template('invoice_grid.html',
							appt_count=invoice_summary['appt_count'],
							appt_amount=invoice_summary['appt_amount'],
							appts_for_grid=invoice_summary['appts_for_grid'],
							daily_totals=invoice_summary['daily_totals'],
							days=invoice_summary['days'],
							notes=invoice_summary['notes'],
							file_link=file_link,
							start_date=start_date,
							rc=rc)



	# Shows summary and all appts billed in a grid with invoice notes


##################################
#  Regional Center Views
##################################

@app.route('/regional_centers')
@login_required
def centers():
	company_id = request.args.get('company_id')

	if current_user.role_id >1:
		company_id = current_user.company_id

	company = models.Company.query.get(company_id)

	rcs = models.RegionalCenter.query.filter_by(company_id=company_id).all()

	return render_template('regional_centers.html',
							regional_centers=rcs,
							company=company)


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
		center.appt_reference_name = form.appt_reference_name.data.strip()
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

		return redirect(url_for('centers'))

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
