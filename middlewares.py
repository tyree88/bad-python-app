import os
from functools import wraps
from flask import request, redirect, url_for, render_template_string, current_app


API_KEY = os.environ.get('VULN_FLASK_APP_API_KEY')

# Decorator to check if user is logged in
def require_api_key(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        api_key = request.cookies.get('api_key')
        if API_KEY is None or api_key == API_KEY:
            return f(*args, **kwargs)
        else:
            return render_template_string('no api key found'), 401
    return wrap


def require_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        session_token = request.cookies.get('session_token')

        if not user_id or not session_token:
            return render_template_string('Unauthorized: admin access required'), 403

        db_result = current_app.db_helper.execute_read(
            "SELECT * FROM users WHERE id=:user_id AND password=:session_token AND is_admin=1",
            {'user_id': user_id, 'session_token': session_token}
        )

        if len(db_result) == 0:
            return render_template_string('Unauthorized: admin access required'), 403

        return f(*args, **kwargs)
    return wrap
