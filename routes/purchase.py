import mysql.connector
from flask import Flask, Blueprint, request, jsonify
from db import get_connection
from routes.auth_required import login_required

pur_bp = Blueprint("purchase", __name__)

@sup_bp.route("/pur", methods = ["get"])
def show_all_order():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("select * from `Purchase`")
        result = cursor.fetchall()
        return jsonify(result), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

    