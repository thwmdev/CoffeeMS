from flask import Blueprint, request, jsonify
from app.database import SessionLocal, db
from app.models.orderM import Mon

mon_bp = Blueprint("mon", __name__, url_prefix="/mon")


def get_db():
    db = SessionLocal()
    return db


@mon_bp.route("/them-mon", methods=["POST"])
def them_mon():
    db = SessionLocal()

    try:
        data = request.get_json()

        # tạo entity Mon giống MonCreate
        mon_moi = Mon(
            TenMon=data.get("ten_mon"),
            GiaBan=data.get("gia"),
            MoTa=data.get("mo_ta"),
            MaDM=data.get("ma_dm")
        )

        db.add(mon_moi)
        db.commit()
        db.refresh(mon_moi)

        return jsonify({
            "message": "Thêm món thành công",
            "data": {
                "MaMon": mon_moi.MaMon,
                "TenMon": mon_moi.TenMon
            }
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({
            "message": "Lỗi khi thêm món",
            "error": str(e)
        }), 500

    finally:
        db.close()