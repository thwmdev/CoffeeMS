from flask import Blueprint, jsonify
from app.security.roles import role_required

product_bp = Blueprint("product", __name__)

@product_bp.route("/products", methods=["GET"])
@role_required("employee", "manager")
def view_products():
    return jsonify({"data": "list products"})