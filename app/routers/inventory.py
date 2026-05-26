import sys

sys.path.append(r"C:\Users\MY PC\Desktop\CofeeMs\app")

from flask import Blueprint, jsonify, request
from database import get_connection

inventory_bp = Blueprint("inventory", __name__)

@inventory_bp.route("/inventory", methods=["GET"])
def get_ingredients():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT *
    FROM NGUYENLIEU
    """

    cursor.execute(sql)

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(result)

# ======================================
# GET INGREDIENT BY ID
# ======================================

@inventory_bp.route("/inventory/<int:id>", methods=["GET"])
def get_ingredient_by_id(id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT *
    FROM NGUYENLIEU
    WHERE MaNL = %s
    """

    cursor.execute(sql, (id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify(result)

# ======================================
# ADD INGREDIENT
# ======================================

@inventory_bp.route("/inventory", methods=["POST"])
def add_ingredient():

    data = request.json

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    INSERT INTO NGUYENLIEU
    (
        TenNL,
        DonViTinh,
        SoLuongTon,
        DinhMucTonKho,
        TrangThai
    )
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        data["TenNL"],
        data["DonViTinh"],
        data["SoLuongTon"],
        data["DinhMucTonKho"],
        data["TrangThai"]
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Them nguyen lieu thanh cong"
    })

# ======================================
# UPDATE INGREDIENT
# ======================================

@inventory_bp.route("/inventory/<int:id>", methods=["PUT"])
def update_ingredient(id):

    data = request.json

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    UPDATE NGUYENLIEU
    SET
        TenNL = %s,
        DonViTinh = %s,
        SoLuongTon = %s,
        DinhMucTonKho = %s,
        TrangThai = %s
    WHERE MaNL = %s
    """

    values = (
        data["TenNL"],
        data["DonViTinh"],
        data["SoLuongTon"],
        data["DinhMucTonKho"],
        data["TrangThai"],
        id
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Cap nhat nguyen lieu thanh cong"
    })

# ======================================
# DELETE INGREDIENT
# ======================================

@inventory_bp.route("/inventory/<int:id>", methods=["DELETE"])
def delete_ingredient(id):

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    DELETE FROM NGUYENLIEU
    WHERE MaNL = %s
    """

    cursor.execute(sql, (id,))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Xoa nguyen lieu thanh cong"
    })

# ======================================
# IMPORT INVENTORY
# ======================================

@inventory_bp.route("/inventory/<int:id>/import", methods=["PATCH"])
def import_inventory(id):

    data = request.json

    so_luong_nhap = data["SoLuongNhap"]

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    UPDATE NGUYENLIEU
    SET SoLuongTon = SoLuongTon + %s
    WHERE MaNL = %s
    """

    cursor.execute(sql, (so_luong_nhap, id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Nhap kho thanh cong"
    })