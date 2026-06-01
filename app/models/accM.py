from app.database.db import get_connection


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

    cursor.execute("""
        UPDATE TAIKHOAN
        SET MatKhau=%s
        WHERE MaTK=%s
    """, (password, matk))

    conn.commit()

    cursor.close()
    conn.close()



def delete_account_db(matk):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM TAIKHOAN WHERE MaTK = %s",
        (matk,)
    )

    conn.commit()

    cursor.close()
    conn.close()