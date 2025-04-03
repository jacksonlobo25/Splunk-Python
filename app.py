from flask import Flask, g, escape, session, redirect, render_template, request, jsonify, Response, got_request_exception
from Misc.functions import *
import logging

# ⬇️ Import your custom Splunk logger
from Common.splunk_logger import log_to_splunk, stdout_logger

# ⬇️ Create custom handler that uses log_to_splunk()
class SplunkLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            log_to_splunk(log_entry)
        except Exception as e:
            stdout_logger.error(f"SplunkLogHandler error: {e}")

# 🔧 Initialize Flask app
app = Flask(__name__)
app.secret_key = '#$ab9&^BB00_.'

# 🔧 Logging setup
app.logger.setLevel(logging.INFO)
splunk_handler = SplunkLogHandler()
splunk_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
splunk_handler.setFormatter(formatter)

# ➕ Attach handler to app and Werkzeug loggers
app.logger.addHandler(splunk_handler)
logging.getLogger().addHandler(splunk_handler)
logging.getLogger('werkzeug').addHandler(splunk_handler)

# 🔁 Optional: forward Flask logs to root logger too
app.logger.propagate = True

# 🔥 Automatically log uncaught exceptions
def log_exception(sender, exception, **extra):
    app.logger.exception("Uncaught Exception: %s", exception)

got_request_exception.connect(log_exception, app)

# ➕ Setting DAO Class
from Models.DAO import DAO
DAO = DAO(app)

# ➕ Registering blueprints
from routes.user import user_view
from routes.book import book_view
from routes.admin import admin_view

# ➕ Registering custom functions to be used within templates
app.jinja_env.globals.update(
    ago=ago,
    str=str,
)

app.register_blueprint(user_view)
app.register_blueprint(book_view)
app.register_blueprint(admin_view)

# ✅ Public access setup
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
