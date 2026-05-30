from flask import Blueprint, jsonify, request, render_template
from app.database.db import get_connection

recipe_bp = Blueprint(
    "recipe",
    __name__,
    url_prefix="/recipe"
)

# =========================
# GIAO DIỆN
# =========================
@recipe_bp.route("/", methods=["GET"])
def home():

    role = request.cookies.get("role")

    if role != "ADMIN":
        return "Không có quyền", 403

    return render_template("recipe.html")


# =========================
# LẤY TOÀN BỘ CÔNG THỨC
# URL: /recipe/recipes
# =========================
@recipe_bp.route("/recipes", methods=["GET"])
def get_all_recipes():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:

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

        return jsonify(cursor.fetchall())

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        cursor.close()
        conn.close()


# =========================
# LẤY CÔNG THỨC THEO MÓN
# URL: /recipe/recipes/1
# =========================
@recipe_bp.route("/recipes/<int:ma_mon>", methods=["GET"])
def get_recipe(ma_mon):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

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
# THÊM CÔNG THỨC
# URL: POST /recipe/recipes
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

            cursor.execute(
                """
                INSERT INTO CONGTHUC
                (MaMon, MaNL, SoLuongSuDung)
                VALUES (%s,%s,%s)
                """,
                (
                    ma_mon,
                    item["MaNL"],
                    item["SoLuongSuDung"]
                )
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Thêm công thức thành công"
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


# =========================
# CẬP NHẬT CÔNG THỨC
# URL: PUT /recipe/recipes/1/2
# =========================
@recipe_bp.route("/recipes/<int:ma_mon>/<int:old_ma_nl>", methods=["PUT"])
def update_recipe(ma_mon, old_ma_nl):

    data = request.json

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE CONGTHUC
            SET
                MaNL = %s,
                SoLuongSuDung = %s
            WHERE
                MaMon = %s
            AND
                MaNL = %s
            """,
            (
                data["MaNL"],
                data["SoLuongSuDung"],
                ma_mon,
                old_ma_nl
            )
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Cập nhật công thức thành công"
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


# =========================
# XÓA CÔNG THỨC
# URL: DELETE /recipe/recipes/1/2
# =========================
@recipe_bp.route("/recipes/<int:ma_mon>/<int:ma_nl>", methods=["DELETE"])
def delete_recipe(ma_mon, ma_nl):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM CONGTHUC
            WHERE MaMon = %s
            AND MaNL = %s
            """,
            (ma_mon, ma_nl)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Xóa công thức thành công"
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