import mysql.connector
from flask import Flask, Blueprint, request, jsonify, session
from db import get_connection
from routes.auth_required import login_required, admin_required
from routes.commonly_used import coname_fm, name_fm, phone_fm, staff_no_fm, check_fm, not_empty, must_fill_in

cust_bp = Blueprint("customer", __name__)

col_and_fm = {
    "co_name": coname_fm,
    "contact_name": name_fm,
    "phone": phone_fm,
    "staff_no": staff_no_fm
}

required_col = ("co_name", "phone", "staff_no")

def get_one_cust(cursor, cust_id: int) -> tuple[dict | None, tuple | None]:
    cursor.execute(
        """
        select cust_no, co_name, contact_name, C.phone, staff_no, staff_id
        from `Customer` C join `Staff` using (staff_id)
        where cust_id = %s
        """, (cust_id, ))
    cust = cursor.fetchone()
    
    if not cust:
        return None, (jsonify({"error": "This customer doesn't exist"}), 404)
    if session["role"] != "admin" and session["staff_id"] != cust["staff_id"]:
        return None, (jsonify({"error": "You do not have permission"}), 403)
    del cust["staff_id"]
    return cust, None


@cust_bp.route("/cust", methods = ["get"])
@login_required
def show_all_customer():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # role limits
        if session["role"] == "admin":
            cursor.execute(
                """
                select cust_no, co_name, contact_name, C.phone, staff_no 
                from `Customer` C join `Staff` using (staff_id)
                """)
        else:
            cursor.execute(
                """
                select cust_no, co_name, contact_name, C.phone, staff_no 
                from `Customer` C join `Staff` using (staff_id)
                where staff_id = %s"
                """, (session["staff_id"], ))
        result = cursor.fetchall()
        return jsonify(result), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()


@cust_bp.route("/cust/<int:cust_id>", methods = ["get"])
@login_required
def show_one_customer(cust_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cust, error = get_one_cust(cursor, cust_id)
        if error:
            return error
        else:
            return jsonify(cust), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()


@cust_bp.route("/cust", methods = ["post"])
@login_required
def create_customer():
    data = request.get_json(silent=True) or {}
    val = {key: data.get(key) for key in col_and_fm}

    # 捉必填, 不能空字串, 格式不對
    error1 = must_fill_in(required_col, val)
    if error1: return error1
    error2 = not_empty(required_col, val)
    if error2: return error2
    error3 = check_fm(col_and_fm, val)
    if error3: return error3

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("select staff_id, is_active from `Staff` where staff_no = %s", (val["staff_no"], ))
        staff = cursor.fetchone()
        if not staff:
            return jsonify({"error": "ID doesn't exist"}), 404
        if not staff["is_active"]:
            return jsonify({"error": "He/She no longer works here"}), 400

        columns = []
        values = []
        for a, b in val.items():
            if b is None:
                continue
            if a == "staff_no":
                columns.append("staff_id")
                values.append(staff["staff_id"])
            else:
                columns.append(a)
                values.append(b)
        s_num = ", ".join(["%s"] * len(values))
        cursor.execute(f"insert into `Customer` ({', '.join(columns)}) values ({s_num})", tuple(values))
        
        num = cursor.lastrowid
        cust_no = f"K{num:06d}"
        cursor.execute("update `Customer` set cust_no = %s where cust_id = %s", (cust_no, num))
        conn.commit()
        return jsonify({"message": "create successed"}), 201

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()


@cust_bp.route("/cust/<int:cust_id>", methods = ["put"])
@login_required
def update_customer(cust_id):
    data = request.get_json(silent=True) or {}
    val = {key: data.get(key) for key in col_and_fm}
    
    # 1. 捉必填的不能空字串
    error1 = not_empty(required_col, val)
    if error1:
        return error1
    # 2. 捉格式不對的
    error2 = check_fm(col_and_fm, val)
    if error2:
        return error2
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # role limit
        _, error = get_one_cust(cursor, cust_id)
        if error:
            return error
        if val["staff_no"] is not None and session["role"] != "admin":
            return jsonify({"error": "You do not have permission"}), 403

        # firm Staff ID exist and He/She is working
        if val["staff_no"] is not None:
            cursor.execute("select staff_id, is_active from `Staff` where staff_no = %s", (val["staff_no"], ))
            staff = cursor.fetchone()
            if not staff:
                return jsonify({"error": "ID doesn't exist"}), 404
            if not staff["is_active"]:
                return jsonify({"error": "He/She no longer works here"}), 400

        columns = []
        values = []
        for a, b in val.items():
            if b is None:
                continue
            if a == "staff_no":
                    columns.append("staff_id = %s")
                    values.append(staff["staff_id"])
            elif a == "contact_name" and b == "":
                columns.append("contact_name = %s")
                values.append(None)
            else:
                columns.append(f"{a} = %s")
                values.append(b)     
        values.append(cust_id)
    
        cursor.execute(f"update `Customer` set {', '.join(columns)} where cust_id = %s", tuple(values))
        conn.commit()
        return jsonify({"message": "update successed"}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()
