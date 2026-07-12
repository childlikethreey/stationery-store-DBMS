import mysql.connector
from flask import Flask, Blueprint, jsonify, request
from db import get_connection
from routes.auth_required import admin_required
import bcrypt

staff_bp = Blueprint("staff", __name__)

@staff_bp.route("/staff", methods = ["get"])
@admin_required
def show_all_staff():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("select staff_no, name, phone, dept, is_active from `Staff`")
        result = cursor.fetchall()
        return jsonify(result)
    
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        conn.close()

@staff_bp.route("/staff/<int:staff_id>", methods = ["get"])
@admin_required
def show_one_staff(staff_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("select staff_no, name, phone, dept, is_active from `Staff` where staff_id = %s", (staff_id, ))
        result = cursor.fetchone()
        return jsonify(result)
    
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500

    finally:
        cursor.close()
        conn.close()

@staff_bp.route("/staff", methods = ["post"])
@admin_required
def create_staff():
    data = request.get_json()
    name = data.get("name")
    dept = data.get("dept")
    phone = data.get("phone")
    if not dept:
        return jsonify({"error": "dept must be fill in"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "insert into `Staff` (name, dept, phone) VALUES (%s, %s, %s)",
            (name, dept, phone)
        )

        num = cursor.lastrowid
        staff_no = f'CS-{num:06d}'
        cursor.execute("update `Staff` set staff_no = %s where staff_id = %s", (staff_no, num))

        conn.commit()
        return jsonify({"message": "create successed", "staff_id": num}), 201

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

@staff_bp.route("/staff/<int:staff_id>/account", methods = ["post"])
@admin_required
def create_new_acc(staff_id):
    data = request.get_json(silent=True) or {}
    role = data["role"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("select staff_no, dept from `Staff` where staff_id = %s", (staff_id, ))
        user = cursor.fetchone()
        if user["dept"] == "清潔部門":
            return jsonify({"message": "清潔人員不能建立帳號"}), 403
        pw = "test123"
        pw_hash = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())
        cursor.execute("insert into `login_info` (staff_id, pw_hash, role) values (%s, %s, %s)", (staff_id, pw_hash, role))
        conn.commit()
        return jsonify({"message": "create successed\n Please remind staff change the password", "staff_id": staff_id, "password": "test123"}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()
        

@staff_bp.route("/staff/<int:staff_id>", methods = ["put"])
@admin_required
def update_staff(staff_id):
    data = request.get_json(silent=True) or {}
    col = []
    val = []
    if "name" in data:
        col.append("name = %s")
        val.append(data["name"])
    if "phone" in data:
        col.append("phone = %s")
        val.append(data["phone"])
    if "dept" in data:
        col.append("dept = %s")
        val.append(data["dept"])
    if "is_active" in data:
        col.append("is_active = %s")
        val.append(data["is_active"])
    val.append(staff_id)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # firm ID exists
        cursor.execute("select * from `Staff` where staff_id = %s", (staff_id, ))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"message": "ID doesn't exist", "staff_id": staff_id}), 404

        sql_instr = f"update `Staff` set {', '.join(col)} where staff_id = %s"    
        cursor.execute(sql_instr, tuple(val))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Not any update", "staff_id": staff_id}), 400
        return jsonify({"message": "update successed", "staff_id": staff_id}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()
