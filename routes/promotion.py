import mysql.connector
from flask import Flask, Blueprint, request, jsonify
from db import get_connection
from routes.auth_required import login_required

promo_bp = Blueprint("promotion", __name__)

@promo_bp.route("/promo", methods = ["get"])
def show_all_order():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("select * from `Promotion`")
        result = cursor.fetchall()
        return jsonify(result), 200

    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    
    finally:
        cursor.close()
        conn.close()

    