import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="Nia",
    password="123456",
    database="quanlyquancafe"
)

cursor = conn.cursor()

tenmon = input("Tên món: ")
giaban = float(input("Giá bán: "))
trangthai = "CONBAN"
madm = int(input("Mã danh mục: "))

sql = """
INSERT INTO MON
(TenMon, GiaBan, TrangThai, MaDM)
VALUES (%s, %s, %s, %s)
"""

values = (
    tenmon,
    giaban,
    trangthai,
    madm
)

cursor.execute(sql, values)

conn.commit()

print("Thêm món thành công")