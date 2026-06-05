from flask import Blueprint, jsonify, request, render_template
from app.security.hash import hash_password

from app.models.accM import (
    get_all_accounts,
    create_account_db,
    update_account_db,
    toggle_account_status_db    
)

account_bp = Blueprint(
    "account",
    __name__,
    url_prefix="/account"
)

@account_bp.route("/")
def account_page():
    return render_template("account.html")


# API lấy danh sách
@account_bp.route("/list")
def get_accounts():
    return jsonify(get_all_accounts())

# Tạo tài khoản
@account_bp.route("/create", methods=["POST"])
def create_account():

    data = request.json
    raw_password = data.get('MatKhau') or data.get('password')
    

    hashed_pw = hash_password(str(raw_password))
    if 'MatKhau' in data:
        data['MatKhau'] = hashed_pw
    else:
        data['password'] = hashed_pw
        
    create_account_db(data)

    return jsonify({
        "message": "Tạo tài khoản thành công"
    })

# Cập nhật thông tin tài khoản
@account_bp.route("/update/<int:matk>", methods=["PUT"])
def update_account(matk):

    data = request.json

    if data.get("MatKhau"):
        data["MatKhau"] = hash_password(data["MatKhau"])

    update_account_db(matk, data)

    return jsonify({
        "message": "Cập nhật thông tin tài khoản thành công"
    })

# Khóa/Mở khóa tài khoản
@account_bp.route("/toggle-status/<int:matk>", methods=["PUT"])
def toggle_account_status(matk):

    toggle_account_status_db(matk)

    return jsonify({
        "message": "Cập nhật trạng thái tài khoản thành công"
    })