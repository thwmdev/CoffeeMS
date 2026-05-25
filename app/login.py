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

sql = """
SELECT * FROM TAIKHOAN
WHERE TenDangNhap = %s
"""

cursor.execute(sql, (username,))

result = cursor.fetchone()

if result:
    hashed_password = result[2]

    if bcrypt.checkpw(
        password.encode(),
        hashed_password.encode()
    ):

        print("Đăng nhập thành công")
        print("Vai trò:", result[3])

        if result[3] == "ADMIN":
            print("Toàn quyền hệ thống")

        elif result[3] == "NHANVIEN":
            print("Chỉ được gọi món")

    else:
        print("Sai mật khẩu")

else:
    print("Không tồn tại tài khoản")