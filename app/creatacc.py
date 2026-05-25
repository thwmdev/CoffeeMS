import bcrypt
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="Nia",
    password="123456",
    database="quanlyquancafe"
)

cursor = conn.cursor()


username = input("Tên đăng nhập: ")
password = input("Mật khẩu: ")
vaitro = input("Vai trò (ADMIN/NHANVIEN): ")


hashed_password = bcrypt.hashpw(
    password.encode(),
    bcrypt.gensalt()
).decode()

sql = """
INSERT INTO TAIKHOAN
(TenDangNhap, MatKhau, VaiTro, TrangThai)
VALUES (%s, %s, %s, %s)
"""

values = (
    username,
    hashed_password,
    vaitro,
    "HOATDONG"
)

try:

    cursor.execute(sql, values)

    conn.commit()

    print("Tạo tài khoản thành công")

except mysql.connector.Error as err:

    print("Lỗi:", err)

finally:

    cursor.close()
    conn.close()