import mysql.connector
import os

def get_connection():
    # Lấy đường dẫn tuyệt đối của file ca.pem nằm ở thư mục gốc dự án
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    ssl_ca_path = os.path.join(base_dir, 'ca.pem')

    return mysql.connector.connect(
        host="coffeems-mysql-coffeems.i.aivencloud.com",
        port=28420,
        user="avnadmin",
        password="AVNS_O8rNgn6hXH4ziWooDIT",
        database="defaultdb",
        
        ssl_ca=ssl_ca_path,
        ssl_disabled=False
    )