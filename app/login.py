from flask import Blueprint, request, jsonify
import bcrypt
from database.db import get_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    username = data.get("username")
    password = data.get("password")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM TAIKHOAN WHERE TenDangNhap=%s",
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    # ❌ phải check user trước
    if not user:
        return jsonify({"message": "Sai tài khoản"}), 401

    try:
        if not bcrypt.checkpw(
            password.encode(),
            user["MatKhau"].encode()
        ):
            return jsonify({"message": "Sai mật khẩu"}), 401
    except Exception as e:
        return jsonify({"message": "Password error", "error": str(e)}), 500

    return jsonify({
        "token": "demo-token",
        "role": user["VaiTro"]
    })