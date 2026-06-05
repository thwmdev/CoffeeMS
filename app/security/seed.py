from app.database.db import get_connection
from app.security.hash import hash_password

def auto_encrypt_passwords():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)


    # Lấy danh sách
    cursor.execute("SELECT TenDangNhap, MatKhau FROM TAIKHOAN")
    users = cursor.fetchall()

    for user in users:
        username = user["TenDangNhap"]
        current_password = user["MatKhau"]
        
        
        # Xử lý định dạng
        if isinstance(current_password, (bytes, bytearray)):
            current_password = current_password.decode('utf-8')
        else:
            current_password = str(current_password).strip()

        
        # Ktra tiền tố của bcrypt ($2b$)
        if not current_password.startswith('$2b$'): 
            print(f"MAT KHAU CHUA MA HOA CHO user: [{username}] , {current_password}]")
            
            
            # Băm
            hashed = hash_password(current_password)
            
            # Cập nhật vào db
            cursor.execute(
                "UPDATE TAIKHOAN SET MatKhau = %s WHERE TenDangNhap = %s",
                (hashed, username)
            )
        else:
            # $2b$ => bỏ qua, giữ nguyên
            print(f" -> Tài khoản [{username}] đã được bảo mật. Bỏ qua.")

    conn.commit()
    cursor.close()
    conn.close()
    
    print("!!!!!!!!!!!!!Hoan thanh ma hoa!!!!!!!!!!!!!!!!!!!!!!!!!!!!!111")
