from flask import Flask
from flask_cors import CORS

from app.routers.menu import menu_bp

app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

CORS(app)

app.register_blueprint(menu_bp)

if __name__ == "__main__":
    app.run(debug=True)