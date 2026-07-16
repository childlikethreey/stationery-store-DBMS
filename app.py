import os
from dotenv import load_dotenv
from flask import Flask
from routes.staff import staff_bp
from routes.auth import auth_bp
from routes.order import order_bp
from routes.order_details import order_detail_bp
from routes.customer import cust_bp
from routes.invertory import inv_bp
from routes.supplier import sup_bp
from routes.purchase import pur_bp
from routes.purchase_details import pur_detail_bp
# from routes.promotion import promo_bp


load_dotenv()
app = Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY")
app.json.ensure_ascii = False

app.register_blueprint(staff_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(order_bp)
app.register_blueprint(order_detail_bp)
app.register_blueprint(cust_bp)
app.register_blueprint(inv_bp)
app.register_blueprint(sup_bp)
app.register_blueprint(pur_bp)
app.register_blueprint(pur_detail_bp)
# app.register_blueprint(promo_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5001)