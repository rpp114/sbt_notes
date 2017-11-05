from flask import render_template, flash, redirect, jsonify, request, g, session, url_for, Markup, send_from_directory
from app import app, models, db, oauth_credentials, login_manager
from .forms import LoginForm, ClientInfoForm, ClientNoteForm, ClientAuthForm, UserInfoForm, LoginForm, PasswordChangeForm, RegionalCenterForm, ApptTypeForm, DateSelectorForm, CompanyForm, NewUserInfoForm, DateTimeSelectorForm, EvalReportForm
from flask_login import login_required, login_user, logout_user, current_user
from sqlalchemy import and_, desc, or_, func
import json, datetime, httplib2, json, sys, os, calendar
from apiclient import discovery
from oauth2client import client
from werkzeug.security import generate_password_hash, check_password_hash
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../jobs'))
from billing import build_appt_xml, get_appts_for_grid
from appts import insert_auth_reminder, move_appts, add_new_client_appt
# from evals import score_eval


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
			user = models.User.query.filter_by(email=form.email.data.lower(), status='active').first()
			if user:
				if check_password_hash(user.password, form.password.data):
					login_user(user, remember=form.remember_me.data)
					if user.first_time_login == 1:
						return redirect(url_for('password_change', user_id=current_user.id))
					if not dest_url:
						dest_url = url_for('user_tasks')
					return redirect(dest_url)
				else:
					flash('Please check your password.')
					return redirect(url_for('index'))
			else:
				flash('Is your email correct?')
				return redirect(url_for('index'))
	else:
		return redirect(url_for('index'))


################################################
# Pages pertaining to Users
################################################

@app.route('/user/tasklist')
@login_required
def user_tasks():
	therapist = current_user.therapist
	notes_needed = []
	assigned_notes = []
	notes_needing_approval = []
	clients_need_info = []
	clients_need_scheduling = []
	auths_need_renewal = []
	new_auths_needed = []
	reports_to_write = []

	if current_user.role_id == 4:
		notes_needed = models.ClientAppt.query.filter(models.ClientAppt.note.has(intern_id = current_user.intern.id),\
									models.ClientAppt.cancelled== 0,\
									or_(models.ClientAppt.note == None, models.ClientAppt.note.has(note='')))\
									.order_by(models.ClientAppt.start_datetime).all()

		notes_needing_approval = models.ClientApptNote.query.filter(models.ClientApptNote.approved == False, models.ClientApptNote.appt.has(cancelled = 0), models.ClientApptNote.intern_id == current_user.intern.id, or_(models.ClientApptNote.note == None, models.ClientApptNote.note != '')).order_by(models.ClientApptNote.created_date).all()

	elif therapist:
		notes_needed = models.ClientAppt.query.filter(models.ClientAppt.therapist_id == therapist.id,\
										or_(models.ClientAppt.note == None, and_(or_(models.ClientAppt.note.has(note=''), models.ClientAppt.note.has(note=None)), models.ClientAppt.note.has(intern_id=0))),\
										models.ClientAppt.cancelled == 0)\
										.order_by(models.ClientAppt.start_datetime).all()

		assigned_notes = models.ClientApptNote.query.filter(models.ClientApptNote.approved == False, or_(models.ClientApptNote.note == '',models.ClientApptNote.note == None), models.ClientApptNote.appt.has(cancelled = 0), models.ClientApptNote.appt.has(therapist_id = therapist.id), models.ClientApptNote.intern_id != 0).order_by(models.ClientApptNote.created_date).all()

		notes_needing_approval = models.ClientApptNote.query.filter(models.ClientApptNote.approved == False, models.ClientApptNote.note != '', models.ClientApptNote.appt.has(cancelled = 0), models.ClientApptNote.appt.has(therapist_id = therapist.id)).order_by(models.ClientApptNote.created_date).all()

		clients_need_info = models.Client.query.filter(models.Client.therapist_id == therapist.id,
				or_(models.Client.address == None,models.Client.address == ''),
				models.Client.status == 'active')\
										.order_by(models.Client.first_name).all()

		clients_need_scheduling = models.Client.query.filter(models.Client.therapist_id == therapist.id,
				models.Client.needs_appt_scheduled == 1,
				models.Client.status == 'active')\
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
												models.Client.status == 'active',
												models.Client.therapist.has(company_id = therapist.company_id)).order_by(models.Client.first_name).all()

	return render_template('user_tasklist.html',
							user=current_user,
							notes=notes_needed,
							assigned_notes=assigned_notes,
							approval_notes=notes_needing_approval,
							clients=clients_need_info,
							appts_needed = clients_need_scheduling,
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
		start_date = datetime.datetime.strptime(form.start_date.data, '%m/%d/%Y')
		end_date = datetime.datetime.strptime(form.end_date.data, '%m/%d/%Y')
		end_date = end_date.replace(hour=23, minute=59, second=59)
	else:
		start_date = datetime.datetime.now().replace(day=1, hour=00, minute=00)
		end_date = datetime.datetime.now()

	user = models.User.query.get(user_id)

	appts = models.ClientAppt.query.filter(models.ClientAppt.therapist_id == user.therapist.id,
							models.ClientAppt.cancelled == 0,
							models.ClientAppt.start_datetime >= start_date,
							models.ClientAppt.end_datetime <= end_date).order_by(models.ClientAppt.start_datetime).all()
	# Do by Date so that you can have a daily summary  with Totals

	rates = {'private': 40.00,
			 'treatment': 40.00,
			 'evaluation': 40.00,
			 'mileage': .535}

	appt_summary = {'private': {'appts': 0, 'multiplier': 2},
					'treatment': {'appts': 0, 'multiplier': 1},
					'evaluation': {'appts': 0, 'multiplier': 3},
					'mileage': {'miles': 0,  'multiplier': 1},
					'appt_dates': []}

	for appt in appts:
		appt_date = appt.start_datetime.strftime('%m/%d/%y')
		appt_summary['appt_dates'].append(appt_date)
		appt_summary[appt_date] = appt_summary.get(appt_date, {'private': [],
																'treatment': [],
																'evaluation': [],
																'mileage': 0})
		if appt.client.regional_center.name == 'Private':
			appt_summary[appt_date]['private'].append({'name': appt.client.first_name + ' ' + appt.client.last_name,
														'date': appt_date,
														'id': appt.id,
														'mileage': appt.mileage})
			appt_summary['private']['appts'] += 1
		else:
			appt_summary[appt_date][appt.appt_type.name].append({'name': appt.client.first_name + ' ' + appt.client.last_name,
														'date': appt_date,
														'id': appt.id,
														'mileage': appt.mileage})
			appt_summary[appt.appt_type.name]['appts'] += 1
		appt_summary[appt_date]['mileage'] += appt.mileage
		appt_summary['mileage']['miles'] += appt.mileage

	appt_summary['appt_dates'] = sorted(set(appt_summary['appt_dates']))

	return render_template('user_appts.html',
							appts=appt_summary,
							user=user,
							form=form,
							start_date=start_date,
							end_date=end_date,
							rates=rates)

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
				therapist.company_id = user.company_id
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

	# if current_user.role_id < 3:
	# also wrap select for therapists in   <!-- {% if current_user.role_id < 3%} -->
	# for filtering by active therapist
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

@app.route('/clients/totals', methods=['GET', 'POST'])
@login_required
def clients_session_totals():

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

	# if current_user.role_id < 3:
	# also wrap select for therapists in   <!-- {% if current_user.role_id < 3%} -->
	# for filtering by active therapist
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

		client_appts = []
		month_start = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0)
		eom = calendar.monthrange(month_start.year, month_start.month)[1]
		month_end = month_start.replace(day=eom, hour=23, minute=59, second=59)

		for appt_client in clients:
			client_appt_total = {}
			client_appt_total['id'] = appt_client.id
			client_appt_total['name'] = appt_client.last_name + ', ' + appt_client.first_name
			client_appt_total['therapist'] = appt_client.therapist.user.first_name

			auth = appt_client.auths.filter(models.ClientAuth.auth_start_date <= month_start, models.ClientAuth.auth_end_date >= month_start, models.ClientAuth.status == 'active').first()

			client_appt_total['max_visits'] = auth.monthly_visits if auth else 0

			appts = appt_client.appts.filter(models.ClientAppt.start_datetime >= month_start, models.ClientAppt.end_datetime <= month_end, models.ClientAppt.cancelled == 0).all()

			client_appt_total['appts'] = len(appts)
			if client_appt_total['max_visits'] - client_appt_total['appts'] > 0 and appt_client.regional_center.name != 'Private':
				client_appts.append(client_appt_total)


	rcs = models.RegionalCenter.query.filter_by(company_id=therapist.user.company_id).all()

	return render_template('client_session_totals.html',
							clients=client_appts,
							rcs=rcs,
							center_id=center_id,
							start_date=month_start.strftime('%Y-%m-%d'),
							end_date=month_end.strftime('%Y-%m-%d'),
							therapist_id=therapist.id,
							therapists=therapists)

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

	form.regional_center_id.choices = [(c.id, c.name) for c in models.RegionalCenter.query.filter(models.RegionalCenter.company_id == current_user.company_id).all()]

	form.therapist_id.choices = [(t.id, t.user.first_name) for t in models.Therapist.query.filter(and_(models.Therapist.user.has(status = 'active'), models.Therapist.user.has(company_id = current_user.company_id), models.Therapist.status == 'active'))]

	if request.method == 'POST':

		client = models.Client() if client_id == '' else models.Client.query.get(client_id)

		client.first_name = form.first_name.data
		client.last_name = form.last_name.data
		if form.birthdate.data:
			client.birthdate = datetime.datetime.strptime(form.birthdate.data, '%m/%d/%Y')
		client.uci_id = form.uci_id.data
		client.address = form.address.data
		client.city = form.city.data
		client.state = form.state.data
		client.zipcode = form.zipcode.data
		client.phone = form.phone.data
		client.gender = form.gender.data
		client.regional_center_id = form.regional_center_id.data

		from_therapist = None
		to_therapist = None

		if client_id != '' and client.therapist_id != form.therapist_id.data:
			from_therapist = client.therapist_id
			to_therapist = form.therapist_id.data
			db.session.add(client)
			db.session.commit()
			return redirect(url_for('move_client', client_id=client.id, from_therapist=from_therapist, to_therapist=to_therapist))

		client.therapist_id = form.therapist_id.data
		db.session.add(client)
		db.session.commit()
		flash('%s %s information updated.' % (client.first_name, client.last_name))

		if client_id == '':
			return redirect(url_for('new_client_appt', client_id=client.id))


		return redirect(url_for('user_tasks'))

	return render_template('client_profile.html',
							client=client,
							form=form)

@app.route('/client/new/appt', methods=['GET', 'POST'])
@login_required
def new_client_appt():
	client_id = request.args.get('client_id')
	client = models.Client.query.get(client_id)

	form = DateTimeSelectorForm()

	if request.method == 'POST':

		if request.form.get('appt_date', False) and request.form.get('appt_time', False):

			date = datetime.datetime.strptime(request.form.get('appt_date'), '%m/%d/%Y')

			time = datetime.datetime.strptime(request.form.get('appt_time'), '%I:%M%p')

			appt_type = request.form.get('appt_type')
			at_rc = True if request.form.get('at_rc') else False

			duration = 90 if appt_type == 'evaluation' else 60

			date = date.replace(year=date.year, month=date.month, day=date.day)
			start_datetime = date.replace(hour=time.hour, minute=time.minute, second=00)

			add_new_client_appt(client, start_datetime, duration, at_rc)


			client.needs_appt_scheduled = 0
			db.session.add(client)
			db.session.commit()

			flash('Added Appt for %s %s on %s' % (client.first_name, client.last_name, start_datetime.strftime('%b %d, %Y at %I:%M%p')))

		return redirect(url_for('user_tasks'))


	form.appt_type.choices = [(type.name, type.name) for type in client.regional_center.appt_types.all()]

	return render_template('new_client_appt.html',
				form=form,
				client=client)


@app.route('/client/move', methods=['GET', 'POST'])
@login_required
def move_client():
	client_id = request.args.get('client_id')
	from_therapist_id = request.args.get('from_therapist')
	to_therapist_id = request.args.get('to_therapist')

	form = DateSelectorForm()

	client = models.Client.query.get(client_id)

	from_therapist = models.Therapist.query.get(from_therapist_id)
	to_therapist = models.Therapist.query.get(to_therapist_id)

	if request.method == 'POST':
		form_start_date = request.form.get('start_date', None)
		form_end_date = request.form.get('end_date', None)

		if form_start_date == None:
			start_date = datetime.datetime.now()
		else:
			form_start_date = datetime.datetime.strptime(form_start_date, '%m/%d/%Y')
			start_date = datetime.datetime.combine(form_start_date, datetime.datetime.min.time())
			start_date = start_date.replace(hour=0, minute=0, second=0)

		if form_end_date == '':
			end_date = ''
		else:
			form_end_date = datetime.datetime.strptime(form_end_date, '%m/%d/%Y')
			end_date = datetime.datetime.combine(form_end_date, datetime.datetime.min.time())
			end_date = end_date.replace(hour=23, minute=59, second=59)

		move_appts(from_therapist, to_therapist, client.first_name + ' ' + client.last_name, from_date=start_date, to_date=end_date)

		flash('Moved %s %s from %s to %s' %(client.first_name, client.last_name, from_therapist.user.first_name, to_therapist.user.first_name))
		return redirect(url_for('user_tasks'))

	now = datetime.datetime.now().strftime('%m/%d/%Y')

	return render_template('move_client.html',
							client=client,
							from_therapist=from_therapist,
							to_therapist=to_therapist,
							form=form,
							now=now)



##############################################
# Pages dealing with Evaluations
##############################################


@app.route('/client/evals', methods=['GET', 'POST'])
@login_required
def eval_directory():
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

	client_evals = client.evals.filter(models.ClientEval.created_date >= start_date,
									   models.ClientEval.created_date <= end_date).all()

	return render_template('eval_directory.html',
	client=client,
	evals=client_evals,
	form=form,
	start_date=start_date,
	end_date=end_date)

@app.route('/client/new_eval', methods=['GET', 'POST'])
@login_required
def new_eval():

	client_id = request.args.get('client_id')
	client = models.Client.query.get(client_id)

	if request.method == 'POST':# and form.is_submitted():
		form_data = sorted([s for s in request.form])
		subtest_ids = [int(request.form[id]) for id in form_data]
		new_eval = models.ClientEval(client=client, therapist=current_user.therapist)
		new_eval.subtests = models.EvalSubtest.query.filter(models.EvalSubtest.id.in_(subtest_ids)).all()
		db.session.add(new_eval)
		db.session.commit()

		session['subtest_ids'] = subtest_ids

		age = (new_eval.created_date - client.birthdate).days
		session['starting_points'] = dict(db.session.query(models.EvalSubtestStart.subtest_id, func.max(models.EvalSubtestStart.start_point)).filter(models.EvalSubtestStart.age <= age).group_by(models.EvalSubtestStart.subtest_id).all())

		return redirect(url_for('evaluation',eval_id=new_eval.id, subtest_id=subtest_ids[0])) #,_anchor=str(start_question_num) )

	evals_form = []
	evals = [(e.id, e.name) for e in models.Evaluation.query.order_by(models.Evaluation.id)]

	for eval_type in evals:
		evals_form.append((eval_type[1], [(s.id, s.name) for s in models.EvalSubtest.query.filter(models.EvalSubtest.eval_id == eval_type[0]).order_by(models.EvalSubtest.eval_subtest_id).all()]))

	return render_template('new_eval.html',
							evals_form=evals_form,
							client=client)


@app.route('/client/eval', methods=['GET', 'POST'])
@login_required
def evaluation():
	eval_id = request.args.get('eval_id')
	subtest_id = request.args.get('subtest_id')

	subtest_ids = session['subtest_ids']
	subtest_index = subtest_ids.index(int(subtest_id))
	eval = models.ClientEval.query.get(eval_id)

	if request.method == 'POST':
		for q in request.form:
			answer = models.ClientEvalAnswer(eval_question_id=q, answer=request.form[q])
			eval.answers.append(answer)
		db.session.commit()
		subtest_index += 1

	if subtest_index == len(subtest_ids):
		session.pop('subtest_ids', None)
		session.pop('starting_points', None)
		score_eval(eval_id)
		return redirect(url_for('eval_scores', eval_id=eval_id))

	subtest = models.EvalSubtest.query.get(subtest_ids[subtest_index])

	start_point = session['starting_points'][str(subtest.id)]

	questions = subtest.questions.all()

	return render_template('eval.html',
							eval=eval,
							subtest=subtest,
							questions=questions,
							start_point=start_point)


@app.route('/client/eval/scores')
@login_required
def eval_scores():
	eval_id = request.args.get('eval_id')

	eval_list = []

	evals = models.Evaluation.query.order_by(models.Evaluation.id).all()

	for eval in evals:
		subtests = [x.id for x in models.EvalSubtest.query.filter(models.EvalSubtest.eval_id == eval.id).order_by(models.EvalSubtest.eval_subtest_id).all()]
		eval_list.append((eval.name, subtests))

	client_eval = models.ClientEval.query.get(eval_id)

	client_age_days = (client_eval.created_date - client_eval.client.birthdate).days

	subtest_scores = client_eval.eval_subtests

	subtest_scores_obj = dict([(x.subtest_id, {'raw_score': x.raw_score,
												'scaled_score': x.scaled_score})
												for x in subtest_scores])

	responses = {}

	for answer in client_eval.answers.order_by(models.ClientEvalAnswer.id):
		eval_name = answer.question.subtest.eval.name
		sub_id = answer.question.subtest.id

		responses[eval_name] = responses.get(eval_name, {})
		responses[eval_name][sub_id] = responses[eval_name].get(sub_id, {'name': answer.question.subtest.name, 'subtest_id': answer.question.subtest.eval_subtest_id, 'raw_score': subtest_scores_obj[sub_id]['raw_score'],
		'scaled_score': subtest_scores_obj[sub_id]['scaled_score'],
		'responses':[]})
		responses[eval_name][sub_id]['responses'].append((answer.question.question_num, answer.question.question, answer.answer))

	return render_template('eval_scores.html',
							responses=responses,
							eval_list=eval_list,
							eval=client_eval,
							age=client_age_days)


@app.route('/client/eval/report', methods=['GET', 'POST'])
@login_required
def eval_report():
	eval_id = request.args.get('eval_id')

	eval = models.ClientEval.query.get(eval_id)

	if request.method == 'POST':
		if eval.report == None:
			eval_report = models.EvalReport(eval=eval)

			for x in request.form:
				if x =='csrf_token':
					continue
				report_section = models.ReportSection(name=x, text=request.form[x], report=eval_report)
				eval_report.sections.append(report_section)
				print(x, request.form[x])


		else:
			eval_report = eval.report

			for section in eval_report.sections:
				section.text = request.form[section.name]

		db.session.add(eval_report)
		db.session.commit()

		return redirect(url_for('eval_report', eval_id=eval.id))

	if eval.report == None:
		form = EvalReportForm()
	else:
		form = EvalReportForm()

		for section in eval.report.sections:
			form[section.name].data  = section.text

	return render_template('eval_report.html',
							eval=eval,
							form=form)



###################################################
# Pages dealing with Client Appts and Notes
###################################################
@app.route('/client/note', methods=['GET', 'POST'])
@login_required
def client_note():
	appt_id = request.args.get('appt_id')

	appt = models.ClientAppt.query.get(appt_id)

	appt.date_string = datetime.datetime.strftime(appt.start_datetime, '%b %-d, %Y at %-I:%M %p')

	interns = []

	if current_user.role_id <= 3:
		interns_objs = models.Intern.query.filter(models.Intern.user.has(status='active'), models.Intern.user.has(company_id=current_user.company_id)).all()
		# to filter interns to active therapist add: ,models.Intern.therapist == appt.therapist
		interns = [(0, 'None')] + [(i.id, i.user.first_name + ' ' + i.user.last_name) for i in interns_objs]


	form = ClientNoteForm() if appt.note == None else ClientNoteForm(approved=appt.note.approved, notes=appt.note.note)

	if appt.note:
		if appt.note.intern_id:
			form.intern_id.data = appt.note.intern_id

	form.intern_id.choices = interns

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
			appt_note = models.ClientApptNote(note=form.notes.data, appt=appt)
		else:
			appt_note = appt.note

		if form.notes.data != '' and appt_note.user == None:
			appt_note.user = current_user

		appt.cancelled = 0
		if form.cancelled.data:
			appt.cancelled = 1

		appt_note.approved = 0
		if appt_note.user:
			if appt_note.user.role_id <= 3 or form.approved.data:
				appt_note.approved = form.approved.data

		if request.form.get('intern_id', None) != None:
			appt_note.intern_id = request.form.get('intern_id')

		if form.notes.data != '':
			appt_note.note = form.notes.data

		db.session.add(appt_note)
		db.session.add(appt)
		db.session.commit()
		flash('Note updated for %s' %(appt.client.first_name + ' ' + appt.client.last_name))
		return redirect(url_for('user_tasks'))

	form.cancelled.data = appt.cancelled

	return render_template('client_note.html',
							form=form,
							appt=appt,
							interns=interns)

@app.route('/client/appt/delete')
@login_required
def delete_appt():
	appt_id = request.args.get('appt_id')

	appt = models.ClientAppt.query.get(appt_id)

	client_id = appt.client.id

	flash('Deleted appt and note for %s %s on %s' %(appt.client.first_name, appt.client.last_name, appt.start_datetime.strftime('%b %d, %Y')), 'error')

	db.session.delete(appt)
	if appt.note:
		db.session.delete(appt.note)
	db.session.commit()

	return redirect(url_for('client_appts', client_id=client_id))


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
										.order_by(desc(models.ClientAppt.start_datetime)).all()


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
										models.ClientAppt.end_datetime <= end_date,
										models.ClientAppt.cancelled == 0,
										models.ClientAppt.note.has(approved=True))\
										.order_by(desc(models.ClientAppt.start_datetime)).all()

	return render_template('client_notes.html',
							form=form,
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
		goal = goal if goal else models.ClientGoal()

		goal.goal = request.form['goal']
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

	goals = models.ClientGoal.query.filter(models.ClientGoal.client_id == client.id, models.ClientGoal.created_date <= end_date, models.ClientGoal.created_date >= start_date)\
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

	rcs = models.RegionalCenter.query.filter(models.RegionalCenter.company_id == company_id).order_by(models.RegionalCenter.id).all()

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

		max_appts = db.session.query(models.ClientAppt).join(models.BillingNote).join(models.Client)\
						.filter(models.ClientAppt.start_datetime >= start_date_max,
						models.ClientAppt.start_datetime <= end_date_max,
						models.BillingNote.note.like('Max%'),
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

		invoice_id = 0

		return render_template('invoice_grid.html',
								invoice_id=invoice_id,
								evals=invoice_summary['evaluation'],
								treatments=invoice_summary['treatment'],
								days=invoice_summary['days'],
								notes=invoice_summary['notes'],
								file_link=file_link,
								start_date=start_date,
								rc=rc)

@app.route('/invoice/download')
@login_required
def download_invoice():
	invoice_id = request.args.get('invoice_id')
	invoice_id = invoice_id.split()[0]

	invoice = models.BillingXml.query.get(invoice_id)

	vendor_id = invoice.regional_center.company.vendor_id
	billing_month = invoice.billing_month.strftime('%m-%Y')
	service_code = invoice.regional_center.appt_types.first().service_code

	download_name = ' '.join([vendor_id,billing_month,str(service_code)])

	file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs/billing/')

	return send_from_directory(file_path, invoice.file_name, as_attachment=True, attachment_filename=download_name + '.xml')


@app.route('/billing/invoice', methods=['POST', 'GET'])
@login_required
def billing_invoice():
	invoice_id = request.args.get('invoice_id')

	# separate out evals vs treatments and build a invoice total.

	invoice = models.BillingXml.query.get(invoice_id)
	file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs/billing/', invoice.file_name)
	invoice_xml = ElementTree(file=file_path)
	file_link = os.path.join(app.root_path,'docs/billing', invoice.file_name)
	notes = invoice.notes.all()

	start_date = invoice.billing_month
	rc = invoice.regional_center

	invoice_summary = get_appts_for_grid(invoice_xml, notes)

	return render_template('invoice_grid.html',
							invoice_id=invoice_id,
							evals=invoice_summary['evaluation'],
							treatments=invoice_summary['treatment'],
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
	company_id = request.args.get('company_id')

	if center_id == None:
		regional_center = {}
	else:
		regional_center = models.RegionalCenter.query.get(center_id)

	form = RegionalCenterForm(obj=regional_center)

	if request.method == 'POST':
		center = models.RegionalCenter() if center_id == None else models.RegionalCenter.query.get(center_id)

		center.name = form.name.data
		center.company_id = company_id
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

		return redirect(url_for('centers', company_id=company_id))

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

	if request.method == 'POST':
		type = models.ApptType() if appt_type_id == None else models.ApptType.query.get(appt_type_id)

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
