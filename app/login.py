from flask import Blueprint, request, jsonify
import bcrypt
from app.database.db import get_connection

auth_bp = Blueprint("auth", __name__)

# Sửa từ "/" thành "/login" để khớp với định tuyến hệ thống /auth/login
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

    # check user
    if not user:
        return jsonify({"message": "Sai tài khoản"}), 401

    try:
        # Ép kiểu dữ liệu mật khẩu từ database về dạng chuỗi utf-8 trước khi encode
        db_password = str(user["MatKhau"])
        if not bcrypt.checkpw(
            password.encode('utf-8'),
            db_password.encode('utf-8')
        ):
            return jsonify({"message": "Sai mật khẩu"}), 401
    except Exception as e:
        return jsonify({"message": "Password error", "error": str(e)}), 500

    return jsonify({
        "token": "demo-token",
        "role": user["VaiTro"]
    })
