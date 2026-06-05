from app.database.db import get_connection
from app.security.hash import hash_password


def get_all_accounts():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            nv.MaNV,
            nv.HoTen,
            nv.SDT,
            nv.Email,
            tk.MaTK,
            tk.TenDangNhap,
            tk.VaiTro,
            tk.TrangThai
        FROM NHANVIEN nv
        JOIN TAIKHOAN tk
            ON nv.MaTK = tk.MaTK
        ORDER BY nv.MaNV
    """)

    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def create_account_db(data):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO TAIKHOAN
        (TenDangNhap, MatKhau, VaiTro, TrangThai, DoiMK)
        VALUES (%s, %s, %s, 'HOATDONG', 0)
    """, (
        data["TenDangNhap"],
        data["MatKhau"],
        data["VaiTro"].upper()
    ))

    matk = cursor.lastrowid

    cursor.execute("""
        INSERT INTO NHANVIEN
        (HoTen, SDT, Email, MaTK)
        VALUES (%s, %s, %s, %s)
    """, (
        data["HoTen"],
        data["SDT"],
        data["Email"],
        matk
    ))

    conn.commit()

    cursor.close()
    conn.close()


def reset_password_db(matk, password):

    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = hash_password(password)

    cursor.execute("""
        UPDATE TAIKHOAN
        SET MatKhau = %s
        WHERE MaTK = %s
    """, (
        hashed_password,
        matk
    ))

    conn.commit()

    cursor.close()
    conn.close()

# Cập nhật thông tin tài khoản
def update_account_db(matk, data):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if data.get("MatKhau"):
            cursor.execute("""
                UPDATE TAIKHOAN
                SET TenDangNhap=%s,
                    MatKhau=%s
                WHERE MaTK=%s
            """, (
                data["TenDangNhap"],
                data["MatKhau"],
                matk
            ))

        else:
            cursor.execute("""
                UPDATE TAIKHOAN
                SET TenDangNhap=%s
                WHERE MaTK=%s
            """, (
                data["TenDangNhap"],
                matk
            ))

        cursor.execute("""
            UPDATE NHANVIEN
            SET SDT=%s,
                Email=%s
            WHERE MaTK=%s
        """, (
            data["SDT"],
            data["Email"],
            matk
        ))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def toggle_account_status_db(matk):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE TAIKHOAN SET TrangThai = IF(TrangThai = 'HOATDONG', 'KHOA', 'HOATDONG') WHERE MaTK = %s",
        (matk,)
    )

    conn.commit()
    cursor.close()
    conn.close()