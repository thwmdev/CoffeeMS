from flask import Blueprint, jsonify, request, render_template
from app.database.db import get_connection

inventory_bp = Blueprint(
    "inventory",
    __name__,
    url_prefix="/inventory"
)

# =========================
# GIAO DIỆN
# =========================
@inventory_bp.route("/", methods=["GET"])
def home():
    return render_template("inventory.html")


# =========================
# VALIDATE HÀM DÙNG CHUNG
# =========================
def validate_ingredient(data):
    if not data:
        return {"success": False, "message": "Dữ liệu yêu cầu không hợp lệ hoặc trống"}

    ten_nl = data.get("TenNL", "").strip()
    don_vi_tinh = data.get("DonViTinh", "").strip()
    so_luong_ton = data.get("SoLuongTon", 0)
    dinh_muc = data.get("DinhMucTonKho", 0)

    if ten_nl == "":
        return {"success": False, "message": "Tên nguyên liệu không được để trống"}

    if don_vi_tinh == "":
        return {"success": False, "message": "Đơn vị tính không được để trống"}

    try:
        so_luong_ton = float(so_luong_ton)
        if so_luong_ton < 0:
            return {"success": False, "message": "Số lượng tồn không hợp lệ"}
    except (ValueError, TypeError):
        return {"success": False, "message": "Số lượng tồn phải là số"}

    try:
        dinh_muc = float(dinh_muc)
        if dinh_muc < 0:
            return {"success": False, "message": "Định mức tồn kho không hợp lệ"}
    except (ValueError, TypeError):
        return {"success": False, "message": "Định mức tồn kho phải là số"}

    return {"success": True}


# =========================
# LẤY TOÀN BỘ NGUYÊN LIỆU
# =========================
@inventory_bp.route("/api", methods=["GET"])
def get_ingredients():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT * FROM NGUYENLIEU ORDER BY MaNL ASC"
        cursor.execute(sql)
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# =========================
# LẤY THEO ID
# =========================
@inventory_bp.route("/<int:id>", methods=["GET"])
def get_ingredient_by_id(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM NGUYENLIEU WHERE MaNL = %s"
        cursor.execute(sql, (id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"success": False, "message": "Không tìm thấy nguyên liệu"}), 404

        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# =========================
# THÊM NGUYÊN LIỆU
# =========================
@inventory_bp.route("/add", methods=["POST"])
def add_ingredient():
    data = request.json
    validate = validate_ingredient(data)
    if not validate["success"]:
        return jsonify(validate), 400

    ten_nl = data["TenNL"].strip()
    don_vi_tinh = data["DonViTinh"].strip()
    so_luong_ton = float(data["SoLuongTon"])
    dinh_muc = float(data["DinhMucTonKho"])

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check trùng tên
        cursor.execute("""
            SELECT MaNL FROM NGUYENLIEU 
            WHERE TRIM(LOWER(TenNL)) = TRIM(LOWER(%s)) LIMIT 1
        """, (ten_nl,))

        if cursor.fetchone():
            return jsonify({"success": False, "message": "Nguyên liệu đã tồn tại"}), 400

        # Thêm mới (Đã xóa TrangThai)
        cursor.execute("""
            INSERT INTO NGUYENLIEU (TenNL, DonViTinh, SoLuongTon, DinhMucTonKho)
            VALUES (%s, %s, %s, %s)
        """, (ten_nl, don_vi_tinh, so_luong_ton, dinh_muc))
        
        conn.commit()
        return jsonify({"success": True, "message": "Thêm nguyên liệu thành công"}), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# =========================
# CẬP NHẬT NGUYÊN LIỆU
# =========================
@inventory_bp.route("/update/<int:id>", methods=["PUT"])
def update_ingredient(id):
    data = request.json
    validate = validate_ingredient(data)
    if not validate["success"]:
        return jsonify(validate), 400

    ten_nl = data["TenNL"].strip()
    don_vi_tinh = data["DonViTinh"].strip()
    so_luong_ton = float(data["SoLuongTon"])
    dinh_muc = float(data["DinhMucTonKho"])

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check trùng tên với các nguyên liệu khác
        cursor.execute("""
            SELECT MaNL FROM NGUYENLIEU 
            WHERE TRIM(LOWER(TenNL)) = TRIM(LOWER(%s)) AND MaNL != %s LIMIT 1
        """, (ten_nl, id))

        if cursor.fetchone():
            return jsonify({"success": False, "message": "Tên nguyên liệu đã tồn tại"}), 400

        # Cập nhật (Đã xóa TrangThai)
        cursor.execute("""
            UPDATE NGUYENLIEU
            SET TenNL=%s, DonViTinh=%s, SoLuongTon=%s, DinhMucTonKho=%s
            WHERE MaNL=%s
        """, (ten_nl, don_vi_tinh, so_luong_ton, dinh_muc, id))
        
        conn.commit()
        return jsonify({"success": True, "message": "Cập nhật thành công"})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# =========================
# XÓA NGUYÊN LIỆU
# =========================
@inventory_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_ingredient(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM NGUYENLIEU WHERE MaNL=%s", (id,))
        conn.commit()
        return jsonify({"success": True, "message": "Xóa thành công"})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# =========================
# NHẬP KHO
# =========================
@inventory_bp.route("/import/<int:id>", methods=["PATCH"])
def import_inventory(id):
    data = request.json or {}
    so_luong_nhap = data.get("SoLuongNhap", 0)

    try:
        so_luong_nhap = float(so_luong_nhap)
        if so_luong_nhap <= 0:
            return jsonify({"success": False, "message": "Số lượng nhập phải lớn hơn 0"}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Số lượng nhập không hợp lệ"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE NGUYENLIEU
            SET SoLuongTon = SoLuongTon + %s
            WHERE MaNL = %s
        """, (so_luong_nhap, id))

        conn.commit()
        return jsonify({"success": True, "message": "Nhập kho thành công"})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()