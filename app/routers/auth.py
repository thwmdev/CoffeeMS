from flask import Blueprint, request, jsonify
import bcrypt
import jwt
import datetime
from app.database.db import get_connection

auth_bp = Blueprint("auth", __name__)

SECRET_KEY = "secret-key-demo"

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    username = data["username"]
    password = data["password"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM TAIKHOAN WHERE TenDangNhap=%s",
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return jsonify({"message": "Sai tài khoản"}), 400

    if not bcrypt.checkpw(password.encode(), user["MatKhau"].encode()):
        return jsonify({"message": "Sai mật khẩu"}), 400

    token = jwt.encode({
        "MaTK": user["MaTK"],
        "role": user["VaiTro"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "token": token,
        "role": user["VaiTro"]
    })