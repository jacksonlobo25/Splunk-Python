from flask import Blueprint, g, escape, session, redirect, render_template, request, jsonify, Response, flash
from app import DAO
from Misc.functions import *
from Common.splunk_logger import log_to_splunk

from Controllers.UserManager import UserManager

user_view = Blueprint('user_routes', __name__, template_folder='/templates')

user_manager = UserManager(DAO)

@user_view.route('/', methods=['GET'])
def home():
	g.bg = 1
	user_manager.user.set_session(session, g)

	log_to_splunk(
		message="User accessed homepage",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'home_access',
			'user_id': g.user if isinstance(g.get("user"), int) else (g.user.get("id") if g.get("user") else None)
		}
	)

	return render_template('home.html', g=g)

@user_view.route('/signin', methods=['GET', 'POST'])
@user_manager.user.redirect_if_login
def signin():
	if request.method == 'POST':
		_form = request.form
		email = str(_form["email"])
		password = str(_form["password"])

		if len(email) < 1 or len(password) < 1:
			return render_template('signin.html', error="Email and password are required")

		d = user_manager.signin(email, password)

		log_to_splunk(
			message="User sign-in attempt",
			status_code=200 if d else 401,
			ip_address=request.remote_addr,
			method=request.method,
			endpoint=request.path,
			user_agent=request.headers.get("User-Agent"),
			extra_data={
				'action': 'user_signin_attempt',
				'email': email,
				'status': 'success' if d else 'failed'
			}
		)

		if d and len(d) > 0:
			session['user'] = int(d['id'])
			return redirect("/")

		return render_template('signin.html', error="Email or password incorrect")

	return render_template('signin.html')

@user_view.route('/signup', methods=['GET', 'POST'])
@user_manager.user.redirect_if_login
def signup():
	if request.method == 'POST':
		name = request.form.get('name')
		email = request.form.get('email')
		password = request.form.get('password')

		if len(name) < 1 or len(email) < 1 or len(password) < 1:
			return render_template('signup.html', error="All fields are required")

		new_user = user_manager.signup(name, email, password)

		log_to_splunk(
			message="User signup attempt",
			status_code=200 if new_user != "already_exists" else 409,
			ip_address=request.remote_addr,
			method=request.method,
			endpoint=request.path,
			user_agent=request.headers.get("User-Agent"),
			extra_data={
				'action': 'user_signup',
				'name': name,
				'email': email,
				'status': new_user
			}
		)

		if new_user == "already_exists":
			return render_template('signup.html', error="User already exists with this email")

		return render_template('signup.html', msg="You've been registered!")

	return render_template('signup.html')

@user_view.route('/signout/', methods=['GET'])
@user_manager.user.login_required
def signout():
	log_to_splunk(
		message="User signed out",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'user_signout',
			'user_id': user_manager.user.uid()
		}
	)

	user_manager.signout()
	return redirect("/", code=302)

@user_view.route('/user/', methods=['GET'])
@user_manager.user.login_required
def show_user(id=None):
	user_manager.user.set_session(session, g)

	if id is None:
		id = int(user_manager.user.uid())

	log_to_splunk(
		message="User viewed profile",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'user_profile_view',
			'user_id': id
		}
	)

	d = user_manager.get(id)
	mybooks = user_manager.getBooksList(id)

	return render_template("profile.html", user=d, books=mybooks, g=g)

@user_view.route('/user', methods=['POST'])
@user_manager.user.login_required
def update():
	user_manager.user.set_session(session, g)

	_form = request.form
	name = str(_form["name"])
	email = str(_form["email"])
	password = str(_form["password"])
	bio = str(_form["bio"])

	user_manager.update(name, email, password, bio, user_manager.user.uid())

	log_to_splunk(
		message="User updated profile",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'user_profile_update',
			'user_id': user_manager.user.uid()
		}
	)

	flash('Your info has been updated!')
	return redirect("/user/")
