from flask import Flask
from flask_cors import CORS

from app.routers.auth import auth_bp

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "secret-key-demo"

# register blueprint
app.register_blueprint(auth_bp, url_prefix="/api/auth")


if __name__ == "__main__":
    app.run(debug=True)