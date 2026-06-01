from flask import Flask
from flask_cors import CORS

def create_app():

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    CORS(app)

    # import routers
    from app.routers.auth import auth_bp
    from app.routers.menu import menu_bp
    from app.routers.inventory import inventory_bp
    from app.routers.recipe import recipe_bp
    from app.routers.pageR import pageR
    from app.routers.order_manage import order_manage_bp
    from app.routers.report import report_bp
    from app.routers.payment import payment_bp
    from app.routers.account import account_bp
    # register blueprint
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(menu_bp, url_prefix="/menu")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(recipe_bp, url_prefix="/recipe")
    app.register_blueprint(pageR)
    app.register_blueprint(order_manage_bp,  url_prefix="/order")
    app.register_blueprint(report_bp, url_prefix="/report")
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(account_bp)

    print(app.url_map)

    return app

