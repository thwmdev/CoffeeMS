from flask import Flask

def create_app():
    app = Flask(__name__)

    # import blueprint
    from app.routers.menu import menu_bp
    from app.routers.auth import auth_bp

    app.register_blueprint(menu_bp)
    app.register_blueprint(auth_bp)

    return app