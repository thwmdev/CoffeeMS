from flask import Blueprint, request, jsonify
from app.security.roles import role_required

food_bp = Blueprint("order", __name__, url_prefix="/order")


@food_bp.route("/them-mon", methods=["POST"])
@role_required("admin")
def them_mon():
    data = request.get_json()

    mon = {
        "ten_mon": data.get("ten_mon"),
        "gia": data.get("gia"),
        "mo_ta": data.get("mo_ta")
    }

    return jsonify({
        "message": "Them mon thanh cong",
        "data": mon
    }), 201