from flask import Blueprint, jsonify, request, render_template
import sys

sys.path.append(r"C:\Users\MY PC\Desktop\CofeeMs\app")
from database import get_connection

menu_bp = Blueprint("menu", __name__)

@menu_bp.route("/menu", methods=["GET"])
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
        DANHMUC.TenDanhMuc
    FROM MON
    JOIN DANHMUC
        ON MON.MaDM = DANHMUC.MaDM
    """

    cursor.execute(sql)

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(result)

@menu_bp.route("/menu/<int:id>", methods=["GET"])
def get_menu_by_id(id):

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
    SELECT *
    FROM MON
    WHERE MaMon = %s
    """

    cursor.execute(sql, (id,))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify(result)

@menu_bp.route("/menu", methods=["POST"])
def add_menu():

    data = request.json

    tenmon = data["TenMon"]
    giaban = data["GiaBan"]
    trangthai = data["TrangThai"]
    mota = data["MoTa"]
    madm = data["MaDM"]

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    INSERT INTO MON
    (TenMon, GiaBan, TrangThai, MoTa, MaDM)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        tenmon,
        giaban,
        trangthai,
        mota,
        madm
    )

    cursor.execute(sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Them mon thanh cong"
    })

@menu_bp.route("/menu/<int:id>", methods=["PUT"])
def update_menu(id):

    data = request.json

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    UPDATE MON
    SET
        TenMon = %s,
        GiaBan = %s,
        TrangThai = %s,
        MoTa = %s,
        MaDM = %s
    WHERE MaMon = %s
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

    return jsonify({
        "message": "Cap nhat thanh cong"
    })

@menu_bp.route("/menu/<int:id>", methods=["DELETE"])
def delete_menu(id):

    conn = get_connection()

    cursor = conn.cursor()

    sql = """
    DELETE FROM MON
    WHERE MaMon = %s
    """

    cursor.execute(sql, (id,))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Xoa mon thanh cong"
    })

@menu_bp.route("/")
def home():

    return render_template("menu.html")