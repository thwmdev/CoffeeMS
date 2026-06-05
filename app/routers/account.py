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


@account_bp.route("/list")
def get_accounts():
    return jsonify(get_all_accounts())


@account_bp.route("/create", methods=["POST"])
def create_account():
    try:
        data = request.json
        create_account_db(data)
        return jsonify({
            "message": "Tạo tài khoản thành công!"
        })
    except ValueError as val_err:
        return jsonify({
            "message": str(val_err)
        }), 400
    except Exception as e:
        print("CREATE ACCOUNT ERROR:", e)
        return jsonify({
            "message": "Có lỗi hệ thống xảy ra, vui lòng thử lại!"
        }), 500


@account_bp.route("/update/<int:matk>", methods=["PUT"])
def update_account(matk):
    try:
        data = request.json
        update_account_db(matk, data)
        return jsonify({
            "message": "Cập nhật thông tin tài khoản thành công!"
        })
    except ValueError as val_err:
        return jsonify({
            "message": str(val_err)
        }), 400
    except Exception as e:
        print("UPDATE ACCOUNT ERROR:", e)
        return jsonify({
            "message": "Có lỗi hệ thống xảy ra, vui lòng thử lại!"
        }), 500


@account_bp.route("/toggle-status/<int:matk>", methods=["PUT"])
def toggle_account_status(matk):
    try:
        toggle_account_status_db(matk)
        return jsonify({
            "message": "Cập nhật trạng thái tài khoản thành công!"
        })
    except Exception as e:
        print("TOGGLE STATUS ERROR:", e)
        return jsonify({
            "message": "Có lỗi hệ thống xảy ra, vui lòng thử lại!"
        }), 500