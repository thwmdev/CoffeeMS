from app.routers.menu import menu_bp
from app.routers.inventory import inventory_bp
from app.routers.recipe import recipe_bp

app = Flask(__name__)

app.register_blueprint(menu_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(recipe_bp)

if __name__ == "__main__":
    app.run(debug=True)