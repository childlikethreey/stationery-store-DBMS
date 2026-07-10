from flask import Flask
from routes.staff import staff_bp

app = Flask(__name__)
app.json.ensure_ascii = False
app.register_blueprint(staff_bp)

@app.route("/hello")
def hello():
    try:
        return "Hello World"
    except:
        return ValueError

if __name__ == "__main__":
    app.run(debug=True, port=5001)