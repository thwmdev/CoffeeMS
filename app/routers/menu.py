from flask import Blueprint, jsonify, request, render_template
from database.db import get_connection 


menu_bp = Blueprint("menu", __name__, url_prefix="/menu")

@menu_bp.route("/", methods=["GET"])
def home():
    return render_template("menu.html")

@menu_bp.route("/api", methods=["GET"])
def get_menu():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT
        MON.MaMon,
        MON.TenMon,
        MON.GiaBan,
        MON.TrangThai,
        MON.MoTa,
        DANHMUC.TenDanhMuc,
        MON.MaDM
    FROM MON
    JOIN DANHMUC ON MON.MaDM = DANHMUC.MaDM
    """

    cursor.execute(sql)
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(result)

@menu_bp.route("/<int:id>", methods=["GET"])
def get_menu_by_id(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM MON WHERE MaMon = %s"
    cursor.execute(sql, (id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify(result)

@menu_bp.route("/", methods=["POST"])
def add_menu():

    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO MON (TenMon, GiaBan, TrangThai, MoTa, MaDM)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        data["TenMon"],
        data["GiaBan"],
        data["TrangThai"],
        data["MoTa"],
        data["MaDM"]
    )

    cursor.execute(sql, values)
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Thêm món thành công"})

@menu_bp.route("/<int:id>", methods=["PUT"])
def update_menu(id):

    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    UPDATE MON
    SET TenMon=%s, GiaBan=%s, TrangThai=%s, MoTa=%s, MaDM=%s
    WHERE MaMon=%s
    """

    values = (
        data["TenMon"],
        data["GiaBan"],
        data["TrangThai"],
        data["MoTa"],
        data["MaDM"],
        id
    )

    cursor.execute(sql, values)
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Cập nhật thành công"})

@menu_bp.route("/<int:id>", methods=["DELETE"])
def delete_menu(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM MON WHERE MaMon = %s", (id,))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Xóa món thành công"})