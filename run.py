from flask import Flask
from flask_cors import CORS

# routers
from app.routers.order import food_bp
from app.routers.menu import menu_bp
from app.routers.inventory import inventory_bp
from app.routers.recipe import recipe_bp
from app.routers.auth import auth_bp
from app.routers.admin import admin_bp

app = Flask(__name__)

# CORS
CORS(app)

# config
app.config["SECRET_KEY"] = "secret-key-demo"

# register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/api/admin")

app.register_blueprint(food_bp, url_prefix="/api/order")
app.register_blueprint(menu_bp, url_prefix="/api/menu")
app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
app.register_blueprint(recipe_bp, url_prefix="/api/recipe")


if __name__ == "__main__":
    app.run(debug=True)