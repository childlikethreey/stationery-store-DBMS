import mysql.connector
from flask import Flask, Blueprint, request, jsonify
from db import get_connection
from routes.auth_required import login_required, admin_required
from routes.commonly_used import coname_fm, name_fm, phone_fm, mix_chk

sup_bp = Blueprint("supplier", __name__)

col_and_fm = {
    "co_name": coname_fm,
    "contact_name": name_fm,
    "phone": phone_fm
}

def get_one_sup(cursor, sup_id: int) -> tuple[dict | None, tuple | None]:
    cursor.execute("select * from `Supplier` where sup_id = %s", (sup_id, ))
    sup = cursor.fetchone()
    if not sup:
        return None, (jsonify({"error": "This supplier doesn't exist"}), 404)
    return sup, None

required_col = ("co_name", "phone")


@sup_bp.route("/sup", methods = ["get"])
@login_required
def show_all_supplier():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("select * from `Supplier`")
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
        sup, error = get_one_sup(cursor, sup_id)
        if error:
            return error
        else:
            return jsonify(sup), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()


@sup_bp.route("/sup", methods = ["post"])
@login_required
def create_new_supplier():
    data = request.get_json(silent=True) or {}
    val = {key: data.get(key) for key in col_and_fm}

    error = mix_chk(required_col, col_and_fm, val, True)
    if error: return error
    
    conn = get_connection()
    cursor = conn.cursor()
    try: 
        columns = []
        values = []
        for a, b in val.items():
            if b is None:
                continue
            columns.append(a)
            values.append(b)
        s_num = ", ".join(["%s"] * len(values))
        cursor.execute(f"insert into `Supplier` ({', '.join(columns)}) values ({s_num})", tuple(values))
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
    val = {key: data.get(key) for key in col_and_fm}

    error = mix_chk(required_col, col_and_fm, val, False)
    if error: return error

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # firm ID exists
        _, error = get_one_sup(cursor, sup_id)
        if error: return error

        columns = []
        values = []
        for a, b in val.items():
            if b is None:
                continue
            if a == "contact_name" and b == "":
                columns.append("contact_name = %s")
                values.append(None)
            else:
                columns.append(f"{a} = %s")
                values.append(b)
        values.append(sup_id)
        cursor.execute(f"update `Supplier` set {", ". join(columns)} where sup_id = %s", tuple(values))
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
