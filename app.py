import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from routes.staff import staff_bp
from routes.auth import auth_bp
from routes.order import order_bp
from routes.customer import cust_bp
from routes.invertory import inv_bp
from routes.supplier import sup_bp
from routes.purchase import pur_bp
from pydantic import ValidationError
import mysql.connector
from routes.helpers import NotFoundError, AuthError
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:8000"])
app.secret_key=os.getenv("SECRET_KEY")
app.json.ensure_ascii = False


@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": e.errors(include_input=False, include_url=False)}), 400

@app.errorhandler(NotFoundError)
def handle_not_found(e):
    return jsonify({"error": str(e)}), 404

@app.errorhandler(AuthError)
def handle_auth_error(e):
    return jsonify({"error": str(e)}), 403

@app.errorhandler(ValueError)
def handle_value_error(e):
    return jsonify({"error": str(e)}), 400

@app.errorhandler(mysql.connector.Error)
def handle_db_error(e):
    return jsonify({"error": str(e)}), 500


app.register_blueprint(staff_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(order_bp)
app.register_blueprint(cust_bp)
app.register_blueprint(inv_bp)
app.register_blueprint(sup_bp)
app.register_blueprint(pur_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
