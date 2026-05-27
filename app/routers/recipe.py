import sys

sys.path.append(r"C:\Users\MY PC\Desktop\CofeeMs\app")

from flask import Blueprint, jsonify, request
from database.db import get_connection

recipe_bp = Blueprint("recipe", __name__)

@recipe_bp.route("/recipes/<int:ma_mon>", methods=["GET"])
def get_recipe(ma_mon):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT
        CONGTHUC.MaCT,
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

@recipe_bp.route("/recipes", methods=["POST"])
def add_recipe():

    data = request.json

    ma_mon = data["MaMon"]

    ingredients = data["ingredients"]

    conn = get_connection()

    cursor = conn.cursor()

    for item in ingredients:

        sql = """
        INSERT INTO CONGTHUC
        (
            MaMon,
            MaNL,
            SoLuongSuDung
        )
        VALUES (%s, %s, %s)
        """

        values = (
            ma_mon,
            item["MaNL"],
            item["SoLuongSuDung"]
        )

        cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Them cong thuc thanh cong"
    })

@recipe_bp.route("/recipes/<int:ma_ct>", methods=["PUT"])
def update_recipe(ma_ct):

    data = request.json

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    UPDATE CONGTHUC
    SET
        MaNL = %s,
        SoLuongSuDung = %s
    WHERE MaCT = %s
    """

    values = (
        data["MaNL"],
        data["SoLuongSuDung"],
        ma_ct
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Cap nhat cong thuc thanh cong"
    })

@recipe_bp.route("/recipes/<int:ma_ct>", methods=["DELETE"])
def delete_recipe(ma_ct):

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    DELETE FROM CONGTHUC
    WHERE MaCT = %s
    """

    cursor.execute(sql, (ma_ct,))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Xoa cong thuc thanh cong"
    })

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

        return jsonify({
            "message": "Mon chua co cong thuc"
        })

    servings = []

    details = []

    for item in ingredients:

        available = (
            item["SoLuongTon"] //
            item["SoLuongSuDung"]
        )

        servings.append(available)

        details.append({
            "NguyenLieu": item["TenNL"],
            "TonKho": item["SoLuongTon"],
            "CanDung": item["SoLuongSuDung"],
            "PhucVuDuoc": int(available)
        })

    so_phan_con_lai = int(min(servings))

    status = "CONBAN"

    if so_phan_con_lai <= 0:
        status = "HETHANG"

    result = {
        "TenMon": ingredients[0]["TenMon"],
        "SoPhanConLai": so_phan_con_lai,
        "TrangThai": status,
        "ChiTiet": details
    }


    cursor.close()
    conn.close()

    return jsonify(result)

@recipe_bp.route("/recipes", methods=["GET"])
def get_all_recipes():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT
        MON.MaMon,
        MON.TenMon,
        NGUYENLIEU.MaNL,
        NGUYENLIEU.TenNL,
        CONGTHUC.SoLuongSuDung,
        NGUYENLIEU.DonViTinh

    FROM CONGTHUC

    JOIN MON
        ON CONGTHUC.MaMon = MON.MaMon

    JOIN NGUYENLIEU
        ON CONGTHUC.MaNL = NGUYENLIEU.MaNL

    ORDER BY MON.MaMon
    """

    cursor.execute(sql)

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(result)