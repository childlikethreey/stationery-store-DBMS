from functools import wraps
from flask import session, jsonify

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "staff_id" not in session:
            return jsonify({"message": "Please login"}), 401
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "staff_id" not in session:
            return jsonify({"message": "Please login"}), 401
        if session.get("role") != "admin":
            return jsonify({"message": "You do not have permission"}), 403
        return f(*args, **kwargs)
    return wrapper