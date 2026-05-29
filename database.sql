
-- =========================================
-- CREATE DATABASE
-- =========================================

DROP DATABASE IF EXISTS quanlyquancafe;
CREATE DATABASE quanlyquancafe;
USE quanlyquancafe;

-- =========================================
-- TAIKHOAN
-- =========================================

CREATE TABLE TAIKHOAN (
    MaTK INT AUTO_INCREMENT PRIMARY KEY,
    TenDangNhap VARCHAR(50) NOT NULL UNIQUE,
    MatKhau VARCHAR(255) NOT NULL,
    VaiTro VARCHAR(20) NOT NULL, -- ADMIN, NHANVIEN, THUNGAN
    TrangThai VARCHAR(20) NOT NULL, -- HOATDONG, KHOA
    DoiMK BOOLEAN DEFAULT FALSE
);

-- =========================================
-- NHANVIEN
-- =========================================

CREATE TABLE NHANVIEN (
    MaNV INT AUTO_INCREMENT PRIMARY KEY,
    HoTen VARCHAR(100) NOT NULL,
    SDT VARCHAR(15) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    MaTK INT NOT NULL,

    CONSTRAINT FK_NHANVIEN_TAIKHOAN
    FOREIGN KEY (MaTK)
    REFERENCES TAIKHOAN(MaTK)
    ON DELETE CASCADE
);

-- =========================================
-- BAN
-- =========================================

CREATE TABLE BAN (
    MaBan INT AUTO_INCREMENT PRIMARY KEY,
    TenBan VARCHAR(50) NOT NULL UNIQUE,
    SoChoNgoi INT NOT NULL,
    TrangThai VARCHAR(30) NOT NULL, -- TRONG, DANGSUDUNG, DADAT

    CHECK (SoChoNgoi > 0)
);

-- =========================================
-- DANHMUC
-- =========================================

CREATE TABLE DANHMUC (
    MaDM INT AUTO_INCREMENT PRIMARY KEY,
    TenDanhMuc VARCHAR(100) NOT NULL
);

-- =========================================
-- MON
-- =========================================

CREATE TABLE MON (
    MaMon INT AUTO_INCREMENT PRIMARY KEY,
    TenMon VARCHAR(100) NOT NULL,
    GiaBan DECIMAL(10,2) NOT NULL,
    TrangThai VARCHAR(30) NOT NULL, -- CONBAN, HETBAN
    MoTa VARCHAR(255),
    MaDM INT NOT NULL,

    CONSTRAINT FK_MON_DANHMUC
    FOREIGN KEY (MaDM)
    REFERENCES DANHMUC(MaDM)
    ON DELETE CASCADE,

    CHECK (GiaBan > 0)
);

-- =========================================
-- DONHANG
-- =========================================

CREATE TABLE DONHANG (
    MaDon INT AUTO_INCREMENT PRIMARY KEY,
    NgayTao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    TrangThai VARCHAR(30) NOT NULL, -- XACNHAN, DANGPHUCVU, CHOTHANHTOAN, DATHANHTOAN, HUY
    TongTien DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    GiamGia DECIMAL(10,2) DEFAULT 0.00,
    ThanhTien DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    MaBan INT NOT NULL,
    MaNV INT NOT NULL,

    CONSTRAINT FK_DONHANG_BAN
    FOREIGN KEY (MaBan)
    REFERENCES BAN(MaBan),

    CONSTRAINT FK_DONHANG_NHANVIEN
    FOREIGN KEY (MaNV)
    REFERENCES NHANVIEN(MaNV),

    CHECK (TongTien >= 0),
    CHECK (ThanhTien >= 0)
);

-- =========================================
-- CHITIETDONHANG
-- =========================================

CREATE TABLE CHITIETDONHANG (
    MaCTDH INT AUTO_INCREMENT PRIMARY KEY,
    MaDon INT NOT NULL,
    MaMon INT NOT NULL,
    SoLuong INT NOT NULL,
    DonGia DECIMAL(10,2) NOT NULL,
    GhiChu VARCHAR(255),
    TrangThaiMon VARCHAR(30) NOT NULL, -- CHOLAM, DANGLAM, DAPHUCVU

    CONSTRAINT FK_CTDH_DONHANG
    FOREIGN KEY (MaDon)
    REFERENCES DONHANG(MaDon)
    ON DELETE CASCADE,

    CONSTRAINT FK_CTDH_MON
    FOREIGN KEY (MaMon)
    REFERENCES MON(MaMon)
    ON DELETE CASCADE,

    CHECK (SoLuong > 0),
    CHECK (DonGia >= 0)
);

-- =========================================
-- KHUYENMAI
-- =========================================

CREATE TABLE KHUYENMAI (
    MaKM INT AUTO_INCREMENT PRIMARY KEY,
    MaCode VARCHAR(50) NOT NULL UNIQUE,
    LoaiKM VARCHAR(20) NOT NULL, -- PHANTRAM, TIENMAT
    GiaTri DECIMAL(10,2) NOT NULL,
    NgayHetHan DATETIME,
    TrangThai VARCHAR(20) NOT NULL, -- HOATDONG, HETHAN

    CHECK (GiaTri >= 0)
);

-- =========================================
-- THANHTOAN
-- =========================================

CREATE TABLE THANHTOAN (
    MaTT INT AUTO_INCREMENT PRIMARY KEY,
    MaDon INT NOT NULL UNIQUE,
    MaKM INT,
    PhuongThuc VARCHAR(30) NOT NULL, -- TIENMAT, CHUYENKHOAN, THE
    SoTienVao DECIMAL(10,2) DEFAULT 0.00,
    TienThoi DECIMAL(10,2) DEFAULT 0.00,
    VAT DECIMAL(10,2) DEFAULT 0.00,
    NgayThanhToan DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT FK_THANHTOAN_DONHANG
    FOREIGN KEY (MaDon)
    REFERENCES DONHANG(MaDon)
    ON DELETE CASCADE,

    CONSTRAINT FK_THANHTOAN_KHUYENMAI
    FOREIGN KEY (MaKM)
    REFERENCES KHUYENMAI(MaKM)
    ON DELETE SET NULL
);

-- =========================================
-- NGUYENLIEU
-- =========================================

CREATE TABLE NGUYENLIEU (
    MaNL INT AUTO_INCREMENT PRIMARY KEY,
    TenNL VARCHAR(100) NOT NULL,
    DonViTinh VARCHAR(20) NOT NULL,
    SoLuongTon DECIMAL(10,2) NOT NULL,
    DinhMucTonKho DECIMAL(10,2) NOT NULL,
    SoLuongTruTam DECIMAL(10,2) DEFAULT 0.00,

    CHECK (SoLuongTon >= 0),
    CHECK (DinhMucTonKho >= 0)
);

-- =========================================
-- CONGTHUC
-- =========================================

CREATE TABLE CONGTHUC (
    MaMon INT NOT NULL,
    MaNL INT NOT NULL,
    SoLuongSuDung DECIMAL(10,2) NOT NULL,

    PRIMARY KEY (MaMon, MaNL),

    CONSTRAINT FK_CONGTHUC_MON
    FOREIGN KEY (MaMon)
    REFERENCES MON(MaMon)
    ON DELETE CASCADE,

    CONSTRAINT FK_CONGTHUC_NGUYENLIEU
    FOREIGN KEY (MaNL)
    REFERENCES NGUYENLIEU(MaNL)
    ON DELETE CASCADE,

    CHECK (SoLuongSuDung > 0)
);

-- =========================================
-- LICHSUDONHANG
-- =========================================

CREATE TABLE LICHSUDONHANG (
    MaLS INT AUTO_INCREMENT PRIMARY KEY,
    MaDon INT NOT NULL,
    MaNV INT NOT NULL,
    HanhDong VARCHAR(50) NOT NULL,
    NoiDung VARCHAR(255),
    ThoiGian DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT FK_LSDH_DONHANG
    FOREIGN KEY (MaDon)
    REFERENCES DONHANG(MaDon)
    ON DELETE CASCADE,

    CONSTRAINT FK_LSDH_NHANVIEN
    FOREIGN KEY (MaNV)
    REFERENCES NHANVIEN(MaNV)
);

-- =========================================
-- PHIEUNHAP
-- =========================================

CREATE TABLE PHIEUNHAP (
    MaPN INT AUTO_INCREMENT PRIMARY KEY,

    MaNL INT NOT NULL,
    MaNV INT NOT NULL,

    SoLuong DECIMAL(10,2) NOT NULL,
    GiaNhap DECIMAL(10,2) NOT NULL,

    NhaCungCap VARCHAR(255) NOT NULL,
    GhiChu TEXT,

    NgayNhap DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT FK_PHIEUNHAP_NGUYENLIEU
    FOREIGN KEY (MaNL)
    REFERENCES NGUYENLIEU(MaNL),

    CONSTRAINT FK_PHIEUNHAP_NHANVIEN
    FOREIGN KEY (MaNV)
    REFERENCES NHANVIEN(MaNV),

    CHECK (SoLuong > 0),
    CHECK (GiaNhap > 0)
);

-- =========================================
-- PHIEUKIEMKHO
-- =========================================

CREATE TABLE PHIEUKIEMKHO (
    MaKK INT AUTO_INCREMENT PRIMARY KEY,

    MaNL INT NOT NULL,
    MaNV INT NOT NULL,

    SoLuongHeThong DECIMAL(10,2) NOT NULL,
    SoLuongThucTe DECIMAL(10,2) NOT NULL,

    ChenhLech DECIMAL(10,2) NOT NULL,
    TyLeChenhLech DECIMAL(10,2) NOT NULL,

    TrangThai VARCHAR(50) NOT NULL DEFAULT 'Approved',
    GhiChu TEXT,

    ThoiGian DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT FK_KIEMKHO_NL
    FOREIGN KEY (MaNL)
    REFERENCES NGUYENLIEU(MaNL),

    CONSTRAINT FK_KIEMKHO_NV
    FOREIGN KEY (MaNV)
    REFERENCES NHANVIEN(MaNV)
);

-- =========================================
-- DATBAN
-- =========================================

CREATE TABLE DATBAN (
    MaDatBan INT AUTO_INCREMENT PRIMARY KEY,
    MaBan INT NOT NULL,
    TenKhach VARCHAR(100) NOT NULL,
    SDT VARCHAR(15) NOT NULL,
    GioDen DATETIME NOT NULL,
    SoNguoi INT NOT NULL,

    CONSTRAINT FK_DATBAN_BAN
    FOREIGN KEY (MaBan)
    REFERENCES BAN(MaBan)
    ON DELETE CASCADE,

    CHECK (SoNguoi > 0)
);

-- =========================================
-- DỮ LIỆU MẪU
-- =========================================

-- ---- TAIKHOAN ----
INSERT INTO TAIKHOAN
(TenDangNhap, MatKhau, VaiTro, TrangThai, DoiMK)
VALUES
('admin', '123456', 'ADMIN', 'HOATDONG', 0),
('nhanvien1', '123456', 'NHANVIEN', 'HOATDONG', 0),
('thungan1', '123456', 'THUNGAN', 'HOATDONG', 0);

-- ---- NHANVIEN ----
INSERT INTO NHANVIEN
(HoTen, SDT, Email, MaTK)
VALUES
('Nguyen Van A', '0900000001', 'a@gmail.com', 1),
('Tran Thi B', '0900000002', 'b@gmail.com', 2),
('Le Van C', '0900000003', 'c@gmail.com', 3);

-- ---- BAN ----
INSERT INTO BAN
(TenBan, SoChoNgoi, TrangThai)
VALUES
('Ban 1', 4, 'TRONG'),
('Ban 2', 4, 'DANGSUDUNG'),
('Ban 3', 6, 'DADAT'),
('Ban 4', 2, 'TRONG');

-- ---- DANHMUC ----
INSERT INTO DANHMUC (TenDanhMuc)
VALUES
('Ca phe'),
('Tra sua'),
('Nuoc ep'),
('Banh ngot');

-- ---- MON ----
INSERT INTO MON
(TenMon, GiaBan, TrangThai, MoTa, MaDM)
VALUES
('Ca phe sua', 30000, 'Còn bán', 'Ca phe sua da', 1),
('Bac xiu', 35000, 'Còn bán', 'Bac xiu nong', 1),
('Tra sua tran chau', 45000, 'Còn bán', 'Tra sua size M', 2),
('Nuoc cam', 40000, 'Còn bán', 'Cam tuoi', 3),
('Tiramisu', 50000, 'Còn bán', 'Banh tiramisu', 4);

-- ---- NGUYENLIEU ----
INSERT INTO NGUYENLIEU
(TenNL, DonViTinh, SoLuongTon, DinhMucTonKho, SoLuongTruTam)
VALUES
('Ca phe', 'Gram', 5000, 1000, 0),
('Sua dac', 'Lon', 50, 10, 0),
('Tran chau', 'Gram', 3000, 500, 0),
('Tra den', 'Gram', 2000, 300, 0),
('Cam tuoi', 'Kg', 20, 5, 0),
('Duong', 'Kg', 15, 3, 0);

-- ---- CONGTHUC ----
INSERT INTO CONGTHUC
(MaMon, MaNL, SoLuongSuDung)
VALUES
(1, 1, 20),
(1, 2, 1),
(2, 1, 15),
(2, 2, 2),
(3, 3, 50),
(3, 4, 10),
(4, 5, 2);

-- ---- KHUYENMAI ----
INSERT INTO KHUYENMAI
(MaCode, LoaiKM, GiaTri, NgayHetHan, TrangThai)
VALUES
('GIAM10', 'PHANTRAM', 10, '2026-12-31', 'HOATDONG'),
('GIAM50K', 'TIENMAT', 50000, '2026-12-31', 'HOATDONG');

-- ---- DONHANG ----
INSERT INTO DONHANG
(NgayTao, TrangThai, TongTien, GiamGia, ThanhTien, MaBan, MaNV)
VALUES
(NOW(), 'DATHANHTOAN', 75000, 5000, 70000, 1, 2),
(NOW(), 'DANGPHUCVU', 90000, 0, 90000, 2, 2),
(NOW(), 'CHOTHANHTOAN', 50000, 0, 50000, 3, 3);

-- ---- CHITIETDONHANG ----
INSERT INTO CHITIETDONHANG
(MaDon, MaMon, SoLuong, DonGia, GhiChu, TrangThaiMon)
VALUES
(1, 1, 1, 30000, 'It da', 'DAPHUCVU'),
(1, 5, 1, 50000, NULL, 'DAPHUCVU'),
(2, 3, 2, 45000, 'Them tran chau', 'DANGLAM'),
(3, 5, 1, 50000, NULL, 'CHOLAM');

-- ---- THANHTOAN ----
INSERT INTO THANHTOAN
(MaDon, MaKM, PhuongThuc, SoTienVao, TienThoi, VAT, NgayThanhToan)
VALUES
(1, 1, 'TIENMAT', 100000, 30000, 7000, NOW());

-- ---- LICHSUDONHANG ----
INSERT INTO LICHSUDONHANG
(MaDon, MaNV, HanhDong, NoiDung)
VALUES
(1, 2, 'TAODON', 'Tao don hang moi'),
(1, 2, 'THANHTOAN', 'Thanh toan tien mat'),
(2, 2, 'CAPNHAT', 'Them mon vao don');

-- ---- PHIEUNHAP ----
INSERT INTO PHIEUNHAP
(MaNL, MaNV, SoLuong, GiaNhap, NhaCungCap, NgayNhap)
VALUES
(1, 1, 2000, 150000, 'Highlands Supplier', NOW()),
(2, 1, 20, 300000, 'Vinamilk', NOW()),
(5, 1, 10, 250000, 'Fresh Farm', NOW());

-- ---- DATBAN ----
INSERT INTO DATBAN
(MaBan, TenKhach, SDT, GioDen, SoNguoi)
VALUES
(3, 'Pham Van D', '0911111111', '2026-05-30 18:00:00', 4),
(4, 'Hoang Thi E', '0922222222', '2026-05-30 19:30:00', 2);