from flask import Flask

# routers
from app.routers.order import food_bp
from app.routers.menu import menu_bp
from app.routers.inventory import inventory_bp
from app.routers.recipe import recipe_bp
from app.routers.auth import auth_bp
from app.routers.admin import admin_bp
app = Flask(__name__)

# register blueprint
app.register_blueprint(food_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(recipe_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True)