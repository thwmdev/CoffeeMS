from flask import Blueprint, jsonify
from app.security.roles import role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/users")
@role_required("manager")
def list_users():
    return jsonify({"msg": "admin only data"})