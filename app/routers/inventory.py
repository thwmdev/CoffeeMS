
from flask import Blueprint, jsonify, request, render_template
from app.database.db import get_connection

inventory_bp = Blueprint(
    "inventory",
    __name__,
    url_prefix="/inventory"
)

# =====================================================
# GIAO DIỆN
# =====================================================
@inventory_bp.route("/", methods=["GET"])
def home():
    return render_template("inventory.html")


# =====================================================
# VALIDATE DÙNG CHUNG
# =====================================================
def validate_ingredient(data):

    if not data:
        return {
            "success": False,
            "message": "Dữ liệu không hợp lệ"
        }

    ten_nl = data.get("TenNL", "").strip()
    don_vi_tinh = data.get("DonViTinh", "").strip()

    so_luong_ton = data.get("SoLuongTon", 0)
    dinh_muc = data.get("DinhMucTonKho", 0)

    if ten_nl == "":
        return {
            "success": False,
            "message": "Tên nguyên liệu không được để trống"
        }

    if don_vi_tinh == "":
        return {
            "success": False,
            "message": "Đơn vị tính không được để trống"
        }

    try:
        so_luong_ton = float(so_luong_ton)

        if so_luong_ton < 0:
            return {
                "success": False,
                "message": "Số lượng tồn không hợp lệ"
            }

    except:
        return {
            "success": False,
            "message": "Số lượng tồn phải là số"
        }

    try:
        dinh_muc = float(dinh_muc)

        if dinh_muc < 0:
            return {
                "success": False,
                "message": "Định mức tồn kho không hợp lệ"
            }

    except:
        return {
            "success": False,
            "message": "Định mức tồn kho phải là số"
        }

    return {
        "success": True
    }


# =====================================================
# LẤY TOÀN BỘ NGUYÊN LIỆU
# =====================================================
@inventory_bp.route("/api", methods=["GET"])
def get_ingredients():

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM NGUYENLIEU
            ORDER BY MaNL ASC
        """)

        result = cursor.fetchall()

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# LẤY THEO ID
# =====================================================
@inventory_bp.route("/<int:id>", methods=["GET"])
def get_ingredient_by_id(id):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM NGUYENLIEU
            WHERE MaNL = %s
        """, (id,))

        result = cursor.fetchone()

        if not result:

            return jsonify({
                "success": False,
                "message": "Không tìm thấy nguyên liệu"
            }), 404

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# THÊM NGUYÊN LIỆU
# =====================================================
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

        # CHECK TRÙNG TÊN
        cursor.execute("""
            SELECT MaNL
            FROM NGUYENLIEU
            WHERE LOWER(TRIM(TenNL)) = LOWER(TRIM(%s))
        """, (ten_nl,))

        if cursor.fetchone():

            return jsonify({
                "success": False,
                "message": "Nguyên liệu đã tồn tại"
            }), 400

        cursor.execute("""
            INSERT INTO NGUYENLIEU
            (
                TenNL,
                DonViTinh,
                SoLuongTon,
                DinhMucTonKho
            )
            VALUES (%s,%s,%s,%s)
        """, (
            ten_nl,
            don_vi_tinh,
            so_luong_ton,
            dinh_muc
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Thêm nguyên liệu thành công"
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# CẬP NHẬT NGUYÊN LIỆU
# =====================================================
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

        # CHECK TRÙNG TÊN
        cursor.execute("""
            SELECT MaNL
            FROM NGUYENLIEU
            WHERE LOWER(TRIM(TenNL)) = LOWER(TRIM(%s))
            AND MaNL != %s
        """, (
            ten_nl,
            id
        ))

        if cursor.fetchone():

            return jsonify({
                "success": False,
                "message": "Tên nguyên liệu đã tồn tại"
            }), 400

        cursor.execute("""
            UPDATE NGUYENLIEU
            SET
                TenNL = %s,
                DonViTinh = %s,
                SoLuongTon = %s,
                DinhMucTonKho = %s
            WHERE MaNL = %s
        """, (
            ten_nl,
            don_vi_tinh,
            so_luong_ton,
            dinh_muc,
            id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Cập nhật thành công"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# XÓA NGUYÊN LIỆU
# =====================================================
@inventory_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_ingredient(id):

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM NGUYENLIEU
            WHERE MaNL = %s
        """, (id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Xóa thành công"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# NHẬP HÀNG
# =====================================================
@inventory_bp.route("/import/<int:maNL>", methods=["POST"])
def save_import_inventory(maNL):

    data = request.json or {}

    try:

        so_luong = float(data.get("SoLuong", 0))
        gia_nhap = float(data.get("GiaNhap", 0))

    except:

        return jsonify({
            "success": False,
            "message": "Dữ liệu số không hợp lệ"
        }), 400

    nha_cc = data.get("NhaCungCap", "").strip()
    ngay_nhap = data.get("NgayNhap")
    ghi_chu = data.get("GhiChu", "").strip()

    ma_nv = 1

    if so_luong <= 0:

        return jsonify({
            "success": False,
            "message": "Số lượng nhập phải lớn hơn 0"
        }), 400

    if gia_nhap <= 0:

        return jsonify({
            "success": False,
            "message": "Giá nhập phải lớn hơn 0"
        }), 400

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # KIỂM TRA NGUYÊN LIỆU
        cursor.execute("""
            SELECT *
            FROM NGUYENLIEU
            WHERE MaNL = %s
        """, (maNL,))

        nl = cursor.fetchone()

        if not nl:

            return jsonify({
                "success": False,
                "message": "Nguyên liệu không tồn tại"
            }), 404

        # UPDATE TỒN KHO
        cursor.execute("""
            UPDATE NGUYENLIEU
            SET SoLuongTon = SoLuongTon + %s
            WHERE MaNL = %s
        """, (
            so_luong,
            maNL
        ))

        # LƯU PHIẾU NHẬP
        cursor.execute("""
            INSERT INTO PHIEUNHAP
            (
                MaNL,
                MaNV,
                SoLuong,
                GiaNhap,
                NhaCungCap,
                GhiChu,
                NgayNhap
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            maNL,
            ma_nv,
            so_luong,
            gia_nhap,
            nha_cc,
            ghi_chu,
            ngay_nhap
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Lưu phiếu nhập thành công"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =====================================================
# KIỂM KHO
# =====================================================
@inventory_bp.route("/check/<int:maNL>", methods=["POST"])
def kiem_kho(maNL):

    data = request.json or {}

    try:

        so_thuc_te = float(data.get("SoLuongThucTe", 0))

    except:

        return jsonify({
            "success": False,
            "message": "Số lượng thực tế không hợp lệ"
        }), 400

    ma_nv = 1

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM NGUYENLIEU
            WHERE MaNL = %s
        """, (maNL,))

        nl = cursor.fetchone()

        if not nl:

            return jsonify({
                "success": False,
                "message": "Nguyên liệu không tồn tại"
            }), 404

        so_he_thong = float(nl["SoLuongTon"])

        chenh_lech = so_thuc_te - so_he_thong

        # TÍNH TỶ LỆ CHÊNH LỆCH
        if so_he_thong == 0:
            ty_le = 100
        else:
            ty_le = abs(chenh_lech) / so_he_thong * 100

        trang_thai = "Approved"

        if ty_le > 20:
            trang_thai = "PendingReview"

        # LƯU PHIẾU KIỂM KHO
        cursor.execute("""
            INSERT INTO PHIEUKIEMKHO
            (
                MaNL,
                MaNV,
                SoLuongHeThong,
                SoLuongThucTe,
                ChenhLech,
                TyLeChenhLech,
                TrangThai
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            maNL,
            ma_nv,
            so_he_thong,
            so_thuc_te,
            chenh_lech,
            ty_le,
            trang_thai
        ))

        # CHỈ UPDATE KHO KHI <=20%
        if ty_le <= 20:

            cursor.execute("""
                UPDATE NGUYENLIEU
                SET SoLuongTon = %s
                WHERE MaNL = %s
            """, (
                so_thuc_te,
                maNL
            ))

        conn.commit()

        if ty_le > 20:

            return jsonify({
                "success": True,
                "message":
                "Chênh lệch >20%. Đã chuyển PendingReview."
            })

        return jsonify({
            "success": True,
            "message": "Kiểm kho thành công"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

