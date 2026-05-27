from flask import Blueprint, jsonify, request, render_template
from app.database.db import get_connection

menu_bp = Blueprint(
    "menu",
    __name__,
    url_prefix="/menu"
)


# =========================
# GIAO DIỆN
# =========================
@menu_bp.route("/", methods=["GET"])
def home():

    return render_template("menu.html")


# =========================
# LẤY TOÀN BỘ MENU
# =========================
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
        MON.MaDM,
        DANHMUC.TenDanhMuc
    FROM MON
    JOIN DANHMUC
        ON MON.MaDM = DANHMUC.MaDM
    ORDER BY MON.MaMon DESC
    """

    cursor.execute(sql)

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(result)


# =========================
# LẤY MÓN THEO ID
# =========================
@menu_bp.route("/<int:id>", methods=["GET"])
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

    if not result:

        return jsonify({
            "success": False,
            "message": "Không tìm thấy món"
        }), 404

    return jsonify(result)


# =========================
# VALIDATE
# =========================
def validate_menu(data):

    ten_mon = data.get("TenMon", "").strip()

    gia_ban = data.get("GiaBan", 0)

    ma_dm = data.get("MaDM")

    if ten_mon == "":

        return {
            "success": False,
            "message": "Tên món không được để trống"
        }

    try:

        gia_ban = float(gia_ban)

        if gia_ban <= 0:

            return {
                "success": False,
                "message": "Giá bán phải lớn hơn 0"
            }

    except:

        return {
            "success": False,
            "message": "Giá bán không hợp lệ"
        }

    if ma_dm is None:

        return {
            "success": False,
            "message": "Vui lòng nhập mã danh mục"
        }

    return {
        "success": True
    }


# =========================
# THÊM MÓN
# =========================
@menu_bp.route("/add", methods=["POST"])
def add_menu():

    data = request.json

    # VALIDATE
    validate = validate_menu(data)

    if not validate["success"]:

        return jsonify(validate), 400

    ten_mon = data["TenMon"].strip()

    gia_ban = float(data["GiaBan"])

    mo_ta = data.get("MoTa", "").strip()

    trang_thai = data["TrangThai"]

    ma_dm = int(data["MaDM"])

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    # CHECK TRÙNG
    check_sql = """
    SELECT MaMon
    FROM MON
    WHERE
        TRIM(LOWER(TenMon))
        =
        TRIM(LOWER(%s))
    AND MaDM = %s
    LIMIT 1
    """

    cursor.execute(
        check_sql,
        (
            ten_mon,
            ma_dm
        )
    )

    existing = cursor.fetchone()

    if existing:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Tên món đã tồn tại trong danh mục này"
        }), 400

    # INSERT
    insert_sql = """
    INSERT INTO MON (
        TenMon,
        GiaBan,
        TrangThai,
        MoTa,
        MaDM
    )
    VALUES (%s,%s,%s,%s,%s)
    """

    values = (
        ten_mon,
        gia_ban,
        trang_thai,
        mo_ta,
        ma_dm
    )

    cursor.execute(insert_sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Thêm món thành công"
    })


# =========================
# CẬP NHẬT MÓN
# =========================
@menu_bp.route("/update/<int:id>", methods=["PUT"])
def update_menu(id):

    data = request.json

    # VALIDATE
    validate = validate_menu(data)

    if not validate["success"]:

        return jsonify(validate), 400

    ten_mon = data["TenMon"].strip()

    gia_ban = float(data["GiaBan"])

    mo_ta = data.get("MoTa", "").strip()

    trang_thai = data["TrangThai"]

    ma_dm = int(data["MaDM"])

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    # CHECK TRÙNG
    check_sql = """
    SELECT MaMon
    FROM MON
    WHERE
        TRIM(LOWER(TenMon))
        =
        TRIM(LOWER(%s))
    AND MaDM = %s
    AND MaMon != %s
    LIMIT 1
    """

    cursor.execute(
        check_sql,
        (
            ten_mon,
            ma_dm,
            id
        )
    )

    existing = cursor.fetchone()

    if existing:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Tên món đã tồn tại trong danh mục này"
        }), 400

    # UPDATE
    update_sql = """
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
        ten_mon,
        gia_ban,
        trang_thai,
        mo_ta,
        ma_dm,
        id
    )

    cursor.execute(update_sql, values)

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Cập nhật thành công"
    })


# =========================
# XÓA MÓN
# =========================
@menu_bp.route("/delete/<int:id>", methods=["DELETE"])
def delete_menu(id):

    conn = get_connection()

    cursor = conn.cursor()

    try:

        # XÓA CÔNG THỨC
        cursor.execute(
            """
            DELETE FROM CONGTHUC
            WHERE MaMon = %s
            """,
            (id,)
        )

        # XÓA MÓN
        cursor.execute(
            """
            DELETE FROM MON
            WHERE MaMon = %s
            """,
            (id,)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Xóa món thành công"
        })

    except Exception as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()