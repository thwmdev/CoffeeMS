from flask import Blueprint, jsonify, request, render_template
from app.database.db import get_connection

recipe_bp = Blueprint(
    "recipe",
    __name__,
    url_prefix="/recipe"
)

# =========================
# GIAO DIỆN CHÍNH
# =========================
@recipe_bp.route("/", methods=["GET"])
def home():
    return render_template("recipe.html")

# =========================
# LẤY TOÀN BỘ CÔNG THỨC
# =========================
# =========================
# LẤY TOÀN BỘ CÔNG THỨC
# =========================
@recipe_bp.route("/recipes", methods=["GET"])
def get_all_recipes():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Đã thêm NGUYENLIEU.SoLuongTon vào SELECT
        sql = """
        SELECT
            MON.MaMon,
            MON.TenMon,
            NGUYENLIEU.MaNL,
            NGUYENLIEU.TenNL,
            CONGTHUC.SoLuongSuDung,
            NGUYENLIEU.DonViTinh,
            NGUYENLIEU.SoLuongTon
        FROM CONGTHUC
        JOIN MON
            ON CONGTHUC.MaMon = MON.MaMon
        JOIN NGUYENLIEU
            ON CONGTHUC.MaNL = NGUYENLIEU.MaNL
        ORDER BY MON.MaMon
        """
        cursor.execute(sql)
        result = cursor.fetchall()
        
        return jsonify(result)
    except Exception as e:
        print(f"LỖI TẢI CÔNG THỨC: {str(e)}") 
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()

# =========================
# LẤY CÔNG THỨC THEO MÃ MÓN
# =========================
@recipe_bp.route("/recipes/<int:ma_mon>", methods=["GET"])
def get_recipe(ma_mon):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Đã bỏ CONGTHUC.MaCT
    sql = """
    SELECT
        NGUYENLIEU.MaNL,
        NGUYENLIEU.TenNL,
        CONGTHUC.SoLuongSuDung,
        NGUYENLIEU.DonViTinh
    FROM CONGTHUC
    JOIN NGUYENLIEU
        ON CONGTHUC.MaNL = NGUYENLIEU.MaNL
    WHERE CONGTHUC.MaMon = %s
    """
    cursor.execute(sql, (ma_mon,))
    result = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(result)

# =========================
# THÊM CÔNG THỨC MỚI
# =========================
@recipe_bp.route("/recipes", methods=["POST"])
def add_recipe():
    data = request.json
    ma_mon = data["MaMon"]
    ingredients = data["ingredients"]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for item in ingredients:
            sql = """
            INSERT INTO CONGTHUC (MaMon, MaNL, SoLuongSuDung)
            VALUES (%s, %s, %s)
            """
            values = (ma_mon, item["MaNL"], item["SoLuongSuDung"])
            cursor.execute(sql, values)

        conn.commit()
        return jsonify({"message": "Thêm công thức thành công"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# =========================
# CẬP NHẬT CÔNG THỨC (THEO MA_MON & MA_NL CŨ)
# =========================
@recipe_bp.route("/recipes/<int:ma_mon>/<int:old_ma_nl>", methods=["PUT"])
def update_recipe(ma_mon, old_ma_nl):
    data = request.json
    new_ma_nl = data["MaNL"]
    so_luong = data["SoLuongSuDung"]

    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = """
        UPDATE CONGTHUC
        SET MaNL = %s, SoLuongSuDung = %s
        WHERE MaMon = %s AND MaNL = %s
        """
        values = (new_ma_nl, so_luong, ma_mon, old_ma_nl)
        cursor.execute(sql, values)
        conn.commit()
        return jsonify({"message": "Cập nhật công thức thành công"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# =========================
# XÓA CÔNG THỨC (THEO MA_MON & MA_NL)
# =========================
@recipe_bp.route("/recipes/<int:ma_mon>/<int:ma_nl>", methods=["DELETE"])
def delete_recipe(ma_mon, ma_nl):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        sql = "DELETE FROM CONGTHUC WHERE MaMon = %s AND MaNL = %s"
        cursor.execute(sql, (ma_mon, ma_nl))
        conn.commit()
        return jsonify({"message": "Xóa công thức thành công"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==================================
# KIỂM TRA KHẢ NĂNG PHỤC VỤ (AVAILABILITY)
# ==================================
@recipe_bp.route("/menu/<int:ma_mon>/availability", methods=["GET"])
def calculate_availability(ma_mon):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT
        MON.TenMon,
        NGUYENLIEU.TenNL,
        NGUYENLIEU.SoLuongTon,
        CONGTHUC.SoLuongSuDung
    FROM CONGTHUC
    JOIN NGUYENLIEU
        ON CONGTHUC.MaNL = NGUYENLIEU.MaNL
    JOIN MON
        ON CONGTHUC.MaMon = MON.MaMon
    WHERE CONGTHUC.MaMon = %s
    """
    cursor.execute(sql, (ma_mon,))
    ingredients = cursor.fetchall()

    if len(ingredients) == 0:
        cursor.close()
        conn.close()
        return jsonify({"message": "Món chưa được thiết lập công thức"})

    servings = []
    details = []

    for item in ingredients:
        available = item["SoLuongTon"] // item["SoLuongSuDung"]
        servings.append(available)

        details.append({
            "NguyenLieu": item["TenNL"],
            "TonKho": item["SoLuongTon"],
            "CanDung": item["SoLuongSuDung"],
            "PhucVuDuoc": int(available)
        })

    so_phan_con_lai = int(min(servings))
    status = "CONBAN" if so_phan_con_lai > 0 else "HETHANG"

    result = {
        "TenMon": ingredients[0]["TenMon"],
        "SoPhanConLai": so_phan_con_lai,
        "TrangThai": status,
        "ChiTiet": details
    }

    cursor.close()
    conn.close()
    return jsonify(result)