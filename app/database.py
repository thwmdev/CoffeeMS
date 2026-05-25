import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="Nia",
    password="123456",
    database="quanlyquancafe"
)

print("Kết nối thành công!")

cursor = conn.cursor()

cursor.execute("SELECT * FROM TAIKHOAN")

for row in cursor.fetchall():
    print(row)