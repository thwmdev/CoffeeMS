from flask import Blueprint, jsonify, request, render_template

from app.models.accM import (
    get_all_accounts,
    create_account_db,
    delete_account_db,
    reset_password_db
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

    create_account_db(data)

    return jsonify({
        "message": "Tạo tài khoản thành công"
    })


# Reset mật khẩu
@account_bp.route("/reset-password/<int:matk>", methods=["PUT"])
def reset_password(matk):

    password = request.json["password"]

    reset_password_db(matk, password)

    return jsonify({
        "message": "Đặt lại mật khẩu thành công"
    })
@account_bp.route("/delete/<int:matk>", methods=["DELETE"])
def delete_account(matk):

    delete_account_db(matk)

    return jsonify({
        "message": "Xóa tài khoản thành công"
    })