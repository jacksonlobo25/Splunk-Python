from flask import Blueprint, g, escape, session, redirect, render_template, request, jsonify, Response
from app import DAO
from Misc.functions import *
from Common.splunk_logger import log_to_splunk

from Controllers.AdminManager import AdminManager
from Controllers.BookManager import BookManager
from Controllers.UserManager import UserManager

import traceback

admin_view = Blueprint('admin_routes', __name__, template_folder='../templates/admin/', url_prefix='/admin')

book_manager = BookManager(DAO)
user_manager = UserManager(DAO)
admin_manager = AdminManager(DAO)

@admin_view.route('/', methods=['GET'])
@admin_manager.admin.login_required
def home():
	admin_manager.admin.set_session(session, g)
	log_to_splunk(
		message="Admin accessed home",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'admin_home_access',
			'admin_id': admin_manager.admin.uid()
		}
	)
	return render_template('admin/home.html', g=g)

@admin_view.route('/signin/', methods=['GET', 'POST'])
@admin_manager.admin.redirect_if_login
def signin():
	g.bg = 1

	if request.method == 'POST':
		_form = request.form
		email = str(_form["email"])
		password = str(_form["password"])

		if len(email) < 1 or len(password) < 1:
			return render_template('admin/signin.html', error="Email and password are required")

		d = admin_manager.signin(email, password)

		log_to_splunk(
			message="Admin sign-in attempt",
			status_code=200 if d else 401,
			ip_address=request.remote_addr,
			method=request.method,
			endpoint=request.path,
			user_agent=request.headers.get("User-Agent"),
			extra_data={
				'action': 'admin_signin_attempt',
				'email': email,
				'status': 'success' if d else 'failed'
			}
		)

		if d and len(d) > 0:
			session['admin'] = int(d["id"])
			return redirect("/admin")

		return render_template('admin/signin.html', error="Email or password incorrect")

	return render_template('admin/signin.html')

@admin_view.route('/signout/', methods=['GET'])
@admin_manager.admin.login_required
def signout():
	log_to_splunk(
		message="Admin signed out",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'admin_signout',
			'admin_id': admin_manager.admin.uid()
		}
	)
	admin_manager.signout()
	return redirect("/admin/", code=302)

@admin_view.route('/users/view/', methods=['GET'])
@admin_manager.admin.login_required
def users_view():
	admin_manager.admin.set_session(session, g)
	id = int(admin_manager.admin.uid())
	admin = admin_manager.get(id)
	myusers = admin_manager.getUsersList()

	log_to_splunk(
		message="Admin viewed users",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'admin_view_users',
			'admin_id': id,
			'user_count': len(myusers)
		}
	)
	return render_template('users.html', g=g, admin=admin, users=myusers)

@admin_view.route('/books/', methods=['GET'])
@admin_manager.admin.login_required
def books():
	admin_manager.admin.set_session(session, g)
	id = int(admin_manager.admin.uid())
	admin = admin_manager.get(id)
	mybooks = book_manager.list(availability=0)

	log_to_splunk(
		message="Admin viewed books",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'admin_view_books',
			'admin_id': id,
			'book_count': len(mybooks)
		}
	)

	return render_template('books/views.html', g=g, books=mybooks, admin=admin)

@admin_view.route('/books/<int:id>')
@admin_manager.admin.login_required
def view_book(id):
	admin_manager.admin.set_session(session, g)

	if id is not None:
		b = book_manager.getBook(id)
		users = user_manager.getUsersByBook(id)

		log_to_splunk(
			message="Admin viewed specific book",
			status_code=200 if b else 404,
			ip_address=request.remote_addr,
			method=request.method,
			endpoint=request.path,
			user_agent=request.headers.get("User-Agent"),
			extra_data={
				'action': 'admin_view_book',
				'book_id': id,
				'admin_id': admin_manager.admin.uid(),
				'user_count': len(users) if users else 0
			}
		)

		if b and len(b) < 1:
			return render_template('books/book_view.html', error="No book found!")

		return render_template("books/book_view.html", books=b, books_owners=users, g=g)

@admin_view.route('/books/add', methods=['GET', 'POST'])
@admin_manager.admin.login_required
def book_add():
	admin_manager.admin.set_session(session, g)
	log_to_splunk(
		message="Admin opened add book page",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'admin_add_book_view',
			'admin_id': admin_manager.admin.uid()
		}
	)
	return render_template('books/add.html', g=g)

@admin_view.route('/books/edit/<int:id>', methods=['GET', 'POST'])
@admin_manager.admin.login_required
def book_edit(id):
	admin_manager.admin.set_session(session, g)

	if id is not None:
		b = book_manager.getBook(id)

		log_to_splunk(
			message="Admin opened edit book page",
			status_code=200 if b else 404,
			ip_address=request.remote_addr,
			method=request.method,
			endpoint=request.path,
			user_agent=request.headers.get("User-Agent"),
			extra_data={
				'action': 'admin_edit_book_view',
				'book_id': id,
				'admin_id': admin_manager.admin.uid()
			}
		)

		if b and len(b) < 1:
			return render_template('edit.html', error="No book found!")

		return render_template("books/edit.html", book=b, g=g)

	return redirect('/books')

@admin_view.route('/books/delete/<int:id>', methods=['GET'])
@admin_manager.admin.login_required
def book_delete(id):
	id = int(id)

	if id is not None:
		book_manager.delete(id)
		log_to_splunk(
			message="Admin deleted a book",
			status_code=200,
			ip_address=request.remote_addr,
			method=request.method,
			endpoint=request.path,
			user_agent=request.headers.get("User-Agent"),
			extra_data={
				'action': 'admin_delete_book',
				'book_id': id,
				'admin_id': admin_manager.admin.uid()
			}
		)

	return redirect('/admin/books/')

@admin_view.route('/books/search', methods=['GET'])
def search():
	admin_manager.admin.set_session(session, g)

	if "keyword" not in request.args:
		return render_template("books/view.html")

	keyword = request.args["keyword"]

	if len(keyword) < 1:
		return redirect('/admin/books')

	id = int(admin_manager.admin.uid())
	admin = admin_manager.get(id)

	d = book_manager.search(keyword, 0)

	log_to_splunk(
		message="Admin searched books",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'admin_search_books',
			'keyword': keyword,
			'admin_id': id,
			'result_count': len(d)
		}
	)

	if len(d) > 0:
		return render_template("books/views.html", search=True, books=d, count=len(d), keyword=escape(keyword), g=g, admin=admin)

	return render_template('books/views.html', error="No books found!", keyword=escape(keyword))

# Error handler for unhandled exceptions (500 errors)
@admin_view.app_errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()

    log_to_splunk(
        message="Unhandled exception occurred",
        status_code=500,
        ip_address=request.remote_addr,
        method=request.method,
        endpoint=request.path,
        user_agent=request.headers.get("User-Agent"),
        extra_data={
            'action': 'unhandled_exception',
            'error': str(e),
            'traceback': tb,
            'admin_id': session.get('admin')
        }
    )
    return render_template("errors/500.html"), 500


# Optional: Error handler for 404 Not Found
@admin_view.app_errorhandler(404)
def not_found_error(e):
    log_to_splunk(
        message="Page not found",
        status_code=404,
        ip_address=request.remote_addr,
        method=request.method,
        endpoint=request.path,
        user_agent=request.headers.get("User-Agent"),
        extra_data={
            'action': 'not_found',
            'admin_id': session.get('admin')
        }
    )
    return render_template("errors/404.html"), 404
