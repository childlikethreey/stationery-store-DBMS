import mysql.connector
from flask import Flask, Blueprint, request, jsonify
from db import get_connection
from routes.auth_required import login_required, admin_required
import re

sup_bp = Blueprint("supplier", __name__)

coname_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s\.]{1,255}$")
name_fm = re.compile(r"^[a-zA-Z\u4e00-\u9fff\s]{1,100}$")
phone_fm = re.compile(r"^[\d\-\(\)]{8,30}$")

@sup_bp.route("/sup", methods = ["get"])
@login_required
def show_all_supplier():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("select co_name, contact_name, phone from `Supplier`")
        result = cursor.fetchall()
        return jsonify(result), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

@sup_bp.route("/sup/<int:sup_id>", methods = ["get"])
@login_required
def show_one_supplier(sup_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("select co_name, contact_name, phone from `Supplier` where sup_id = %s", (sup_id,))
        result = cursor.fetchone()
        return jsonify(result), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

@sup_bp.route("/sup", methods = ["post"])
@login_required
def create_new_suplier():
    data = request.get_json(silent=True) or {}
    co_name = data.get("co_name")
    contact_name = data.get("contact_name")
    phone = data.get("phone")

    if not co_name or not coname_fm.match(co_name):
        return jsonify({"error": "Company Name isn't being filled in or format is not correct"}), 400
    if contact_name and not name_fm.match(contact_name):
        return jsonify({"error": "'Contact Name' format is not correct"}), 400
    if not phone or not phone_fm.match(phone):
        return jsonify({"error": "Phnoe no. isn't being filled in or format is not correct"}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    try: 
        if not contact_name:
            cursor.execute("insert into `Supplier` (co_name, phone) values (%s, %s)", (co_name, phone))
        else:
            cursor.execute("insert into `Supplier` (co_name, contact_name, phone) values (%s, %s, %s)", (co_name, contact_name, phone))
        conn.commit()
        return jsonify({"message": "create successed"}), 201
        
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

@sup_bp.route("/sup/<int:sup_id>", methods = ["put"])
@admin_required
def update_supplier(sup_id):
    data = request.get_json(silent=True) or {}
    col = []
    val = []
    if "co_name" in data:
        if not coname_fm.match(data["co_name"]):
            return jsonify({"error": "'Company Name' format is not correct"}), 400
        col.append("co_name = %s")
        val.append(data["co_name"])
    if "contact_name" in data:
        if not name_fm.match(data["contact_name"]):
            return jsonify({"error": "'Contact Name' format is not correct"}), 400
        col.append("contact_name = %s")
        val.append(data["contact_name"])
    if "phone" in data:
        if not phone_fm.match(data["phone"]):
            return jsonify({"error": "Phone format is not correct"}), 400
        col.append("phone = %s")
        val.append(data["phone"])
    val.append(sup_id)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # firm ID exists
        cursor.execute("select * from `Supplier` where sup_id = %s", (sup_id, ))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"error": "ID doesn't exist", "sup_id": sup_id}), 404

        sql_instr = f"update `Supplier` set {', '.join(col)} where sup_id = %s"    
        cursor.execute(sql_instr, tuple(val))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"message": "Not any update", "sup_id": sup_id}), 400
        return jsonify({"message": "update successed", "sup_id": sup_id}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()
