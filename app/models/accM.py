import re
from app.database.db import get_connection
from app.security.hash import hash_password


def validate_nhanvien_fields(data, is_update=False, current_matk=None):
    required_fields = ["TenDangNhap", "HoTen", "SDT", "Email", "VaiTro"]
    
    if not is_update:
        required_fields.append("MatKhau")

    for field in required_fields:
        val = data.get(field)
        if val is None or str(val).strip() == "":
            raise ValueError("Vui lòng điền đầy đủ thông tin!")

    email = str(data.get("Email")).strip()
    sdt = str(data.get("SDT")).strip()
    tendangnhap = str(data.get("TenDangNhap")).strip()

    if not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email):
        raise ValueError("Email không hợp lệ!")

    if not re.match(r"^0[0-9]{9}$", sdt):
        raise ValueError("Số điện thoại bắt đầu bằng số 0 và đủ 10 chữ số.")

    #KIỂM TRA TRÙNG 
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if is_update and current_matk:
        cursor.execute("SELECT COUNT(*) as total FROM TAIKHOAN WHERE TenDangNhap = %s AND MaTK != %s", (tendangnhap, current_matk))
        if cursor.fetchone()["total"] > 0:
            cursor.close()
            conn.close()
            raise ValueError("Tên đăng nhập này đã có người sử dụng!")

        
        cursor.execute("SELECT COUNT(*) as total FROM NHANVIEN WHERE SDT = %s AND MaTK != %s", (sdt, current_matk))
        if cursor.fetchone()["total"] > 0:
            cursor.close()
            conn.close()
            raise ValueError("Số điện thoại này đã có người sử dụng!")

        
        
        
        cursor.execute("SELECT COUNT(*) as total FROM NHANVIEN WHERE Email = %s AND MaTK != %s", (email, current_matk))
        if cursor.fetchone()["total"] > 0:
            cursor.close()
            conn.close()
            raise ValueError("Email này đã có người sử dụng!")
    else:
        
        
        
        cursor.execute("SELECT COUNT(*) as total FROM TAIKHOAN WHERE TenDangNhap = %s", (tendangnhap,))
        if cursor.fetchone()["total"] > 0:
            cursor.close()
            conn.close()
            raise ValueError("Tên đăng nhập này đã tồn tại!")

        
        
        
        cursor.execute("SELECT COUNT(*) as total FROM NHANVIEN WHERE SDT = %s", (sdt,))
        if cursor.fetchone()["total"] > 0:
            cursor.close()
            conn.close()
            raise ValueError("Số điện thoại này đã tồn tại!")


        cursor.execute("SELECT COUNT(*) as total FROM NHANVIEN WHERE Email = %s", (email,))
        if cursor.fetchone()["total"] > 0:
            cursor.close()
            conn.close()
            raise ValueError("Email này đã tồn tại!")

    cursor.close()
    conn.close()


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
    # Gọi hàm validate (bên trong đã tích hợp kiểm tra trùng)
    validate_nhanvien_fields(data, is_update=False)

    raw_password = data.get("MatKhau") or data.get("password")
    hashed_pw = hash_password(str(raw_password))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO TAIKHOAN
        (TenDangNhap, MatKhau, VaiTro, TrangThai, DoiMK)
        VALUES (%s, %s, %s, 'HOATDONG', 0)
    """, (
        data["TenDangNhap"].strip(),
        hashed_pw,
        data["VaiTro"].upper()
    ))

    matk = cursor.lastrowid

    cursor.execute("""
        INSERT INTO NHANVIEN
        (HoTen, SDT, Email, MaTK)
        VALUES (%s, %s, %s, %s)
    """, (
        data["HoTen"].strip(),
        data["SDT"].strip(),
        data["Email"].strip(),
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


def update_account_db(matk, data):
    # Truyền thêm mã tài khoản hiện tại (matk) vào hàm validate để tránh việc tự trùng với chính mình khi cập nhật thông tin cũ
    validate_nhanvien_fields(data, is_update=True, current_matk=matk)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        if data.get("MatKhau"):
            hashed_pw = hash_password(data["MatKhau"])
            cursor.execute("""
                UPDATE TAIKHOAN
                SET TenDangNhap=%s,
                    MatKhau=%s
                WHERE MaTK=%s
            """, (
                data["TenDangNhap"].strip(),
                hashed_pw,
                matk
            ))

        else:
            cursor.execute("""
                UPDATE TAIKHOAN
                SET TenDangNhap=%s
                WHERE MaTK=%s
            """, (
                data["TenDangNhap"].strip(),
                matk
            ))

        cursor.execute("""
            UPDATE NHANVIEN
            SET SDT=%s,
                Email=%s
            WHERE MaTK=%s
        """, (
            data["SDT"].strip(),
            data["Email"].strip(),
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