from app.database.db import get_connection
from app.security.hash import hash_password

def auto_encrypt_passwords():
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT TenDangNhap, MatKhau FROM TAIKHOAN")
    users = cursor.fetchall()

    for user in users:
        username = user["TenDangNhap"]
        current_password = user["MatKhau"]
        
        if isinstance(current_password, (bytes, bytearray)):
            current_password = current_password.decode('utf-8')
        else:
            current_password = str(current_password).strip()

        if len(current_password) < 20: 
            print(f" MMatkhau thuong: [{username}]. Tu dong ma hoa...")
            hashed = hash_password(current_password)
            
            cursor.execute(
                "UPDATE TAIKHOAN SET MatKhau = %s WHERE TenDangNhap = %s",
                (hashed, username)
            )


    conn.commit()
    cursor.close()
    conn.close()
    
    
    
    print("!!!!!!!!!!!!!Hoan thanh ma hoa!!!!!!!!!!!!!!!!!!!!!!!!!!!!!111")
