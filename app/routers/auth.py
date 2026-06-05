from flask import Blueprint, request, jsonify
from app.database.db import get_connection

# 👉 ĐỒNG BỘ BẢO MẬT
from app.security.hash import verify_password
from app.security.jwthandler import encode_token

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

    # 1. Kiểm tra tài khoản tồn tại
    if not user:
        return jsonify({"message": "Tài khoản không tồn tại."}), 401

    if user["TrangThai"] != "HOATDONG":
        return jsonify({"message": "Tài khoản của bạn đã bị khóa."}), 403

    try:
        db_password = user["MatKhau"]
        
        # ép chuyển đổi sang str
        if isinstance(db_password, (bytes, bytearray)):
            db_password = db_password.decode('utf-8')
        else:
            db_password = str(db_password)

        print(f"Mat khau vao: {password}")
        print(f"Mat khau tu db: {db_password}")

        if not verify_password(password, db_password):
            return jsonify({"message": "Mật khẩu không chính xác"}), 401
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "validation error", "error": str(e)}), 500


    # JWT Token 
    
    payload = {
        "username": user["TenDangNhap"],
        "role": user["VaiTro"]
    }
    real_token = encode_token(payload)

    return jsonify({
        "token": real_token,
        "role": user["VaiTro"]
    })
