import mysql.connector
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from db import get_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods = ["post"])
def staff_login():
    data = request.get_json(silent=True) or {}
    staff_no = data.get("staff_no")
    pw = data.get("pw")
    if not (staff_no or pw):
        return jsonify({"message": "please fill in staff no and password"}), 400
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            select staff_id, is_active, pw_hash, role
            from `Staff` left outer join `login_info` using (staff_id)
            where staff_no = %s
            """, (staff_no, )
        )
        user = cursor.fetchone()

        if not (user or check_password_hash(user["pw_hash"], pw)):
            return jsonify({"message": "wrong staff no or password"}), 401
        if not user["is_active"]:
            return jsonify({"message": "this staff is not work here already"}), 403

        session["staff_id"] = user["staff_id"]
        session["role"] = user["role"]

        return jsonify({"message": "login successed", "role": user["role"]}), 200
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

@auth_bp.route("/logout", methods = ["post"])
def staff_logout():
    session.clear()
    return jsonify({"message": "logout"}), 200