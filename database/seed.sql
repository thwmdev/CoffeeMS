-- =========================================
-- SEED DATABASE - QUAN LY QUAN CAFE
-- UC04 + UC05
-- =========================================

DROP DATABASE IF EXISTS quanlyquancafe;
CREATE DATABASE quanlyquancafe;
USE quanlyquancafe;

-- =========================================
-- TAIKHOAN
-- =========================================

CREATE TABLE TAIKHOAN (
    MaTK INT AUTO_INCREMENT PRIMARY KEY,
    TenDangNhap VARCHAR(50) UNIQUE NOT NULL,
    MatKhau VARCHAR(255) NOT NULL,
    VaiTro NVARCHAR(20) NOT NULL,
    TrangThai NVARCHAR(20) NOT NULL,
    DoiMK BIT DEFAULT 0
);

-- =========================================
-- NHANVIEN
-- =========================================

CREATE TABLE NHANVIEN (
    MaNV INT AUTO_INCREMENT PRIMARY KEY,
    HoTen NVARCHAR(100) NOT NULL,
    SDT VARCHAR(15) NOT NULL,
    Email VARCHAR(100),
    MaTK INT NOT NULL,

    FOREIGN KEY (MaTK)
    REFERENCES TAIKHOAN(MaTK)
);

-- =========================================
-- DANHMUC
-- =========================================

CREATE TABLE DANHMUC (
    MaDM INT AUTO_INCREMENT PRIMARY KEY,
    TenDanhMuc NVARCHAR(100) NOT NULL
);

-- =========================================
-- MON
-- =========================================

CREATE TABLE MON (
    MaMon INT AUTO_INCREMENT PRIMARY KEY,
    TenMon NVARCHAR(100) NOT NULL,
    GiaBan DECIMAL(10,2) NOT NULL,
    TrangThai NVARCHAR(30) NOT NULL,
    MoTa NVARCHAR(255),
    HinhAnh VARCHAR(255),
    MaDM INT NOT NULL,

    FOREIGN KEY (MaDM)
    REFERENCES DANHMUC(MaDM)
);

-- =========================================
-- NGUYENLIEU
-- =========================================

CREATE TABLE NGUYENLIEU (
    MaNL INT AUTO_INCREMENT PRIMARY KEY,
    TenNL NVARCHAR(100) NOT NULL,
    DonViTinh NVARCHAR(50) NOT NULL,
    SoLuongTon FLOAT NOT NULL,
    DinhMucTonKho FLOAT NOT NULL,
    TrangThai NVARCHAR(30) NOT NULL
);

-- =========================================
-- CONGTHUC
-- =========================================

CREATE TABLE CONGTHUC (
    MaCT INT AUTO_INCREMENT PRIMARY KEY,

    MaMon INT NOT NULL,
    MaNL INT NOT NULL,

    SoLuongSuDung FLOAT NOT NULL,

    FOREIGN KEY (MaMon)
    REFERENCES MON(MaMon),

    FOREIGN KEY (MaNL)
    REFERENCES NGUYENLIEU(MaNL)
);

-- =========================================
-- BAN
-- =========================================

CREATE TABLE BAN (
    MaBan INT AUTO_INCREMENT PRIMARY KEY,
    TenBan NVARCHAR(50) NOT NULL,
    SoChoNgoi INT NOT NULL,
    TrangThai NVARCHAR(30) NOT NULL
);

-- =========================================
-- DONHANG
-- =========================================

CREATE TABLE DONHANG (
    MaDon INT AUTO_INCREMENT PRIMARY KEY,

    NgayTao DATETIME NOT NULL,
    TrangThai NVARCHAR(30) NOT NULL,

    TongTien DECIMAL(10,2) NOT NULL,
    GiamGia DECIMAL(10,2),
    ThanhTien DECIMAL(10,2) NOT NULL,

    MaBan INT,
    MaNV INT,

    FOREIGN KEY (MaBan)
    REFERENCES BAN(MaBan),

    FOREIGN KEY (MaNV)
    REFERENCES NHANVIEN(MaNV)
);

-- =========================================
-- CHITIETDONHANG
-- =========================================

CREATE TABLE CHITIETDONHANG (
    MaCTDH INT AUTO_INCREMENT PRIMARY KEY,

    MaDon INT NOT NULL,
    MaMon INT NOT NULL,

    SoLuong INT NOT NULL,
    DonGia DECIMAL(10,2),

    FOREIGN KEY (MaDon)
    REFERENCES DONHANG(MaDon),

    FOREIGN KEY (MaMon)
    REFERENCES MON(MaMon)
);

-- =========================================
-- INSERT TAIKHOAN
-- password demo: 123456
-- =========================================

INSERT INTO TAIKHOAN
(TenDangNhap, MatKhau, VaiTro, TrangThai)
VALUES
(
    'QL',
    '123456',
    'ADMIN',
    'HOATDONG'
),
(
    'NV1',
    '123456',
    'NHANVIEN',
    'HOATDONG'
);


INSERT INTO NHANVIEN
(HoTen, SDT, Email, MaTK)
VALUES
(
    'Nguyen Van Admin',
    '0900000001',
    'admin@gmail.com',
    1
),
(
    'Tran Thi Nhan Vien',
    '0900000002',
    'nhanvien@gmail.com',
    2
);

-- =========================================
-- INSERT DANHMUC
-- =========================================

INSERT INTO DANHMUC
(TenDanhMuc)
VALUES
('Tra Sua'),
('Cafe'),
('Da Xay'),
('Tra'),
('Nuoc Ep');

-- =========================================
-- INSERT MON
-- =========================================

INSERT INTO MON
(TenMon, GiaBan, TrangThai, MoTa, HinhAnh, MaDM)
VALUES

(
    'Tra Sua Truyen Thong',
    35000,
    'ACTIVE',
    'Tra sua dai loan',
    NULL,
    1
),

(
    'Tra Sua Matcha',
    42000,
    'ACTIVE',
    'Tra sua matcha',
    NULL,
    1
),

(
    'Cafe Sua',
    30000,
    'ACTIVE',
    'Cafe sua da',
    NULL,
    2
),

(
    'Bac Xiu',
    32000,
    'ACTIVE',
    'Bac xiu',
    NULL,
    2
),

(
    'Tra Dao',
    40000,
    'ACTIVE',
    'Tra dao cam sa',
    NULL,
    4
);

-- =========================================
-- INSERT NGUYENLIEU
-- =========================================

INSERT INTO NGUYENLIEU
(
    TenNL,
    DonViTinh,
    SoLuongTon,
    DinhMucTonKho,
    TrangThai
)
VALUES

(
    'Tra Den',
    'gram',
    5000,
    500,
    'CONHANG'
),

(
    'Sua Tuoi',
    'ml',
    10000,
    1000,
    'CONHANG'
),

(
    'Duong',
    'gram',
    7000,
    700,
    'CONHANG'
),

(
    'Bot Matcha',
    'gram',
    2000,
    200,
    'CONHANG'
),

(
    'Cafe',
    'gram',
    4000,
    400,
    'CONHANG'
),

(
    'Sua Dac',
    'ml',
    5000,
    500,
    'CONHANG'
),

(
    'Dao',
    'mieng',
    100,
    10,
    'CONHANG'
),

(
    'Cam Sa',
    'gram',
    1000,
    100,
    'CONHANG'
);

-- =========================================
-- INSERT CONGTHUC
-- =========================================

-- Tra Sua Truyen Thong

INSERT INTO CONGTHUC
(MaMon, MaNL, SoLuongSuDung)
VALUES
(1, 1, 10),
(1, 2, 100),
(1, 3, 20);

-- Tra Sua Matcha

INSERT INTO CONGTHUC
(MaMon, MaNL, SoLuongSuDung)
VALUES
(2, 1, 8),
(2, 2, 100),
(2, 4, 15),
(2, 3, 15);

-- Cafe Sua

INSERT INTO CONGTHUC
(MaMon, MaNL, SoLuongSuDung)
VALUES
(3, 5, 15),
(3, 6, 50);

-- Bac Xiu

INSERT INTO CONGTHUC
(MaMon, MaNL, SoLuongSuDung)
VALUES
(4, 5, 10),
(4, 6, 80);

-- Tra Dao

INSERT INTO CONGTHUC
(MaMon, MaNL, SoLuongSuDung)
VALUES
(5, 1, 8),
(5, 7, 2),
(5, 8, 5),
(5, 3, 10);

-- =========================================
-- INSERT BAN
-- =========================================

INSERT INTO BAN
(TenBan, SoChoNgoi, TrangThai)
VALUES
('Ban 1', 4, 'TRONG'),
('Ban 2', 4, 'TRONG'),
('Ban 3', 6, 'TRONG'),
('Ban 4', 2, 'TRONG'),
('Ban 5', 8, 'TRONG');

-- =========================================
-- INSERT DONHANG
-- =========================================

INSERT INTO DONHANG
(
    NgayTao,
    TrangThai,
    TongTien,
    GiamGia,
    ThanhTien,
    MaBan,
    MaNV
)
VALUES
(
    NOW(),
    'DATHANHTOAN',
    70000,
    0,
    70000,
    1,
    2
);

-- =========================================
-- INSERT CHITIETDONHANG
-- =========================================

INSERT INTO CHITIETDONHANG
(
    MaDon,
    MaMon,
    SoLuong,
    DonGia
)
VALUES
(
    1,
    1,
    2,
    35000
);

-- =========================================
-- TEST QUERY
-- =========================================

SELECT * FROM MON;
SELECT * FROM NGUYENLIEU;
SELECT * FROM CONGTHUC;