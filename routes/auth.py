import mysql.connector
from flask import Blueprint, request, jsonify, session
from db import get_connection
from routes.auth_required import login_required
import bcrypt

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

        if not user or not bcrypt.checkpw(pw.encode("utf-8"), user["pw_hash"].encode("utf-8")):
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

@auth_bp.route("/account", methods = ["patch"])
@login_required
def change_pw():
    data = request.get_json(silent=True) or {}
    old_pw = data.get("old_pw")
    new_pw = data.get("new_pw")
    if not old_pw or not new_pw:
        return jsonify({"message": "please fill in old password and new password"}), 400
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
       cursor.execute("select * from `login_info` where staff_id = %s", (session["staff_id"], ))
       user = cursor.fetchone()

       if not bcrypt.checkpw(old_pw.encode("utf-8"), user["pw_hash"].encode("utf-8")):
           return jsonify({"message": "wrong old password"}), 400
       if old_pw == new_pw:
           return jsonify({"message": "new password cannnot same as old password"}), 400
       
       temp = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt())
       cursor.execute("update `login_info` set pw_hash = %s where staff_id = %s", (temp, session["staff_id"]))
       conn.commit()
       return jsonify({"message": "change password successed"}), 200
    
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()
    