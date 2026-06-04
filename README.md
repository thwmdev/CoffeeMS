# CoffeeMS - Coffee Shop Management System

## 1. Giới thiệu

CoffeeMS là hệ thống quản lý quán cà phê được xây dựng bằng Python Flask và MySQL.

Hệ thống hỗ trợ:

* Quản lý thực đơn
* Quản lý nguyên liệu
* Quản lý công thức pha chế
* Quản lý đơn hàng
* Thanh toán hóa đơn
* Quản lý tài khoản nhân viên
* Báo cáo doanh thu
* Xác thực đăng nhập bằng JWT

## 2. Công nghệ sử dụng

### Backend

* Python 3.12
* Flask
* SQLAlchemy
* MySQL Connector
* JWT Authentication
* Bcrypt Password Hashing

### Database

* MySQL 8.0

### Containerization

* Docker
* Docker Compose

## 3. Kiến trúc hệ thống

```text
Client
   │
   ▼
Flask API
   │
   ▼
MySQL Database
```

Các module chính:

```text
app/
├── database/
├── models/
├── routers/
├── security/
├── templates/
├── static/
└── login.py
```

## 4. Chức năng chính

### Quản lý tài khoản

* Đăng nhập
* Phân quyền ADMIN
* Phân quyền NHANVIEN
* Mã hóa mật khẩu bằng Bcrypt

### Quản lý thực đơn

* Xem danh sách món
* Thêm món
* Sửa món
* Xóa món

### Quản lý nguyên liệu

* Quản lý kho
* Nhập nguyên liệu
* Kiểm tra tồn kho

### Quản lý công thức

* Thêm công thức pha chế
* Cập nhật công thức
* Xóa công thức

### Quản lý đơn hàng

* Tạo đơn
* Thêm món vào đơn
* Chuyển bếp
* Gộp bàn
* Chuyển bàn

### Thanh toán

* Áp dụng voucher
* In hóa đơn
* Thanh toán đơn hàng

### Báo cáo

* Doanh thu
* Lịch sử chỉnh sửa
* Xuất Excel
* Xuất PDF

## 5. Cài đặt
## 5.1 Cài đặt bằng Docker

### Yêu cầu

* Docker Desktop
* Docker Compose

### Clone project

```bash
git clone https://github.com/thwmdev/CoffeeMS.git

cd CoffeeMS
```

### Chạy hệ thống

```bash
docker-compose up --build
```

Sau khi chạy thành công:

```text
Flask:
http://localhost:5000

MySQL:
localhost:3307
```

### Dừng hệ thống

```bash
docker-compose down
```

### Khởi động lại

```bash
docker-compose up
```

## 5.2. Cài đặt Local (không dùng Docker)

### Cài Python dependencies

```bash
pip install -r requirements.txt
```

### Tạo database

```sql
SOURCE database.sql;
```

### Chỉnh thông tin kết nối

File:

```python
app/database/db.py
```

Ví dụ:

```python
host="localhost"
user="root"
password="root123"
database="quanlyquancafe"
```

### Chạy ứng dụng

```bash
python run.py
```

Ứng dụng chạy tại:

```text
http://localhost:5000
```

## 9. Thành viên thực hiện
* Huỳnh Thị Hồng Thắm (Leader)
* Lương Võ Hân Hân
* Trần Đức Thành
* Bùi Kiếm Khoa
* Đoàn Minh Trí

## 10. License
Dự án được phát triển phục vụ mục đích học tập và nghiên cứu môn Nhập môn công nghệ phần mềm
