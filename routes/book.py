from flask import Blueprint, g, escape, session, redirect, render_template, request, jsonify, Response
from app import DAO
from Common.splunk_logger import log_to_splunk

from Controllers.UserManager import UserManager
from Controllers.BookManager import BookManager

import traceback

book_view = Blueprint('book_routes', __name__, template_folder='/templates')

book_manager = BookManager(DAO)
user_manager = UserManager(DAO)

@book_view.route('/books/', defaults={'id': None})
@book_view.route('/books/<int:id>')
def home(id):
	user_manager.user.set_session(session, g)

	user_id = user_manager.user.uid() if user_manager.user.isLoggedIn() else None

	if id is not None:
		b = book_manager.getBook(id)

		log_to_splunk(
			message="Viewed book detail",
			status_code=200 if b else 404,
			ip_address=request.remote_addr,
			method=request.method,
			endpoint=request.path,
			user_agent=request.headers.get("User-Agent"),
			extra_data={
				'action': 'view_book_detail',
				'book_id': id,
				'user_id': user_id
			}
		)

		user_books = {}
		if user_manager.user.isLoggedIn():
			user_books = book_manager.getReserverdBooksByUser(user_id=user_id)['user_books'].split(',')

		if b and len(b) < 1:
			return render_template('book_view.html', error="No book found!")

		return render_template("book_view.html", books=b, g=g, user_books=user_books)

	else:
		b = book_manager.list()
		user_books = []

		if user_manager.user.isLoggedIn():
			reserved_books = book_manager.getReserverdBooksByUser(user_id=user_id)
			if reserved_books is not None:
				user_books = reserved_books['user_books'].split(',')

		log_to_splunk(
			message="Viewed books list",
			status_code=200,
			ip_address=request.remote_addr,
			method=request.method,
			endpoint=request.path,
			user_agent=request.headers.get("User-Agent"),
			extra_data={
				'action': 'view_books_list',
				'user_id': user_id,
				'book_count': len(b)
			}
		)

		if b and len(b) < 1:
			return render_template('books.html', error="No books found!")

		return render_template("books.html", books=b, g=g, user_books=user_books)

@book_view.route('/books/add/<id>', methods=['GET'])
@user_manager.user.login_required
def add(id):
	user_id = user_manager.user.uid()
	book_manager.reserve(user_id, id)

	log_to_splunk(
		message="Reserved a book",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'reserve_book',
			'user_id': user_id,
			'book_id': id
		}
	)

	b = book_manager.list()
	user_manager.user.set_session(session, g)

	return render_template("books.html", msg="Book reserved", books=b, g=g)

@book_view.route('/books/search', methods=['GET'])
def search():
	user_manager.user.set_session(session, g)

	if "keyword" not in request.args:
		return render_template("search.html")

	keyword = request.args["keyword"]

	if len(keyword) < 1:
		return redirect('/books')

	d = book_manager.search(keyword)

	log_to_splunk(
		message="Searched books",
		status_code=200,
		ip_address=request.remote_addr,
		method=request.method,
		endpoint=request.path,
		user_agent=request.headers.get("User-Agent"),
		extra_data={
			'action': 'search_books',
			'keyword': keyword,
			'result_count': len(d),
			'user_id': user_manager.user.uid() if user_manager.user.isLoggedIn() else None
		}
	)

	if len(d) > 0:
		return render_template("books.html", search=True, books=d, count=len(d), keyword=escape(keyword), g=g)

	return render_template('books.html', error="No books found!", keyword=escape(keyword))

# Error handler for unhandled exceptions (500 errors)
@book_view.app_errorhandler(Exception)
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
            'user_id': session.get('user')
        }
    )
    return render_template("errors/500.html"), 500


# Optional: Error handler for 404 Not Found
@book_view.app_errorhandler(404)
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
            'user_id': session.get('user')
        }
    )
    return render_template("errors/404.html"), 404
