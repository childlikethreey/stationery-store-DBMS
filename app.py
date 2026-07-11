import os
from dotenv import load_dotenv
from flask import Flask
from routes.staff import staff_bp
from routes.auth import auth_bp

load_dotenv()
app = Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY")
app.json.ensure_ascii = False

app.register_blueprint(staff_bp)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5001)