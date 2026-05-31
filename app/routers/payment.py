from flask import Blueprint, request, jsonify, render_template, session
from app.database.db import get_connection
import datetime

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")

# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def _row_to_dict(cursor, row):
    """Chuyển một row thành dict dựa vào tên cột."""
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def _rows_to_list(cursor, rows):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


def _serialize(obj):
    """JSON-serialize các kiểu dữ liệu đặc biệt (Decimal, datetime)."""
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def success(data=None, message="Thành công", status=200):
    return jsonify({"success": True, "message": message, "data": data}), status


def error(message="Có lỗi xảy ra", status=400):
    return jsonify({"success": False, "message": message, "data": None}), status


# ─────────────────────────────────────────────
# RENDER PAGE
# ─────────────────────────────────────────────

@payment_bp.route("/")
def index():
    return render_template("payment.html")


# ─────────────────────────────────────────────
# [1] DANH SÁCH BÀN
# GET /payment/tables
# Trả về tất cả bàn kèm trạng thái.
# ─────────────────────────────────────────────

@payment_bp.route("/tables", methods=["GET"])
def get_tables():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    b.MaBan,
                    b.TenBan,
                    b.SoChoNgoi,
                    b.TrangThai,
                    d.MaDon,
                    d.TrangThai   AS TrangThaiDon,
                    d.TongTien,
                    d.GiamGia,
                    d.ThanhTien
                FROM BAN b
                LEFT JOIN DONHANG d
                    ON d.MaBan = b.MaBan
                    AND d.TrangThai NOT IN ('DATHANHTOAN', 'HUY')
                ORDER BY b.MaBan
            """)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            tables = [dict(zip(cols, r)) for r in rows]

        import json
        return jsonify({
            "success": True,
            "message": "Thành công",
            "data": json.loads(
                json.dumps(tables, default=_serialize)
            )
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# [2] CHI TIẾT ĐƠN HÀNG THEO BÀN
# GET /payment/tables/<ma_ban>/order
# Trả về đơn hàng đang hoạt động của bàn + chi tiết từng món.
# ─────────────────────────────────────────────

@payment_bp.route("/tables/<int:ma_ban>/order", methods=["GET"])
def get_order_by_table(ma_ban):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Lấy đơn hàng đang hoạt động
            cur.execute("""
                SELECT d.*, nv.HoTen AS TenNhanVien
                FROM DONHANG d
                JOIN NHANVIEN nv ON nv.MaNV = d.MaNV
                WHERE d.MaBan = %s
                  AND d.TrangThai NOT IN ('DATHANHTOAN', 'HUY')
                ORDER BY d.NgayTao DESC
                LIMIT 1
            """, (ma_ban,))
            row = cur.fetchone()

            if not row:
                return success(None, "Bàn đang trống")

            cols = [d[0] for d in cur.description]
            order = dict(zip(cols, row))

            # Lấy chi tiết các món trong đơn
            cur.execute("""
                SELECT
                    ct.MaCTDH,
                    ct.MaMon,
                    m.TenMon,
                    ct.SoLuong,
                    ct.DonGia,
                    ct.GhiChu,
                    ct.TrangThaiMon
                FROM CHITIETDONHANG ct
                JOIN MON m ON m.MaMon = ct.MaMon
                WHERE ct.MaDon = %s
                ORDER BY ct.MaCTDH
            """, (order["MaDon"],))
            items = _rows_to_list(cur, cur.fetchall())
            order["ChiTiet"] = items

        import json
        return jsonify({
            "success": True,
            "message": "Thành công",
            "data": json.loads(json.dumps(order, default=_serialize))
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# [3] DANH SÁCH VOUCHER ĐANG HOẠT ĐỘNG
# GET /payment/vouchers
# Trả về các mã khuyến mãi còn hiệu lực.
# ─────────────────────────────────────────────

@payment_bp.route("/vouchers", methods=["GET"])
def get_vouchers():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MaKM, MaCode, LoaiKM, GiaTri, NgayHetHan, TrangThai
                FROM KHUYENMAI
                WHERE TrangThai = 'HOATDONG'
                  AND (NgayHetHan IS NULL OR NgayHetHan >= NOW())
                ORDER BY MaKM
            """)
            rows = _rows_to_list(cur, cur.fetchall())

        import json
        return jsonify({
            "success": True,
            "message": "Thành công",
            "data": json.loads(json.dumps(rows, default=_serialize))
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# [4] KIỂM TRA & ÁP DỤNG VOUCHER
# POST /payment/vouchers/apply
# Body: { "ma_code": "GIAM10", "tong_tien": 90000 }
# Trả về số tiền giảm thực tế.
# ─────────────────────────────────────────────

@payment_bp.route("/vouchers/apply", methods=["POST"])
def apply_voucher():
    data = request.get_json()
    ma_code  = (data or {}).get("ma_code", "").strip().upper()
    tong_tien = float((data or {}).get("tong_tien", 0))

    if not ma_code:
        return error("Vui lòng nhập mã voucher")
    if tong_tien <= 0:
        return error("Tổng tiền không hợp lệ")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MaKM, MaCode, LoaiKM, GiaTri, NgayHetHan, TrangThai
                FROM KHUYENMAI
                WHERE MaCode = %s
            """, (ma_code,))
            row = cur.fetchone()

            if not row:
                return error("Mã voucher không tồn tại")

            cols = [d[0] for d in cur.description]
            km = dict(zip(cols, row))

            if km["TrangThai"] != "HOATDONG":
                return error("Mã voucher đã hết hạn hoặc không hoạt động")
            if km["NgayHetHan"] and km["NgayHetHan"] < datetime.datetime.now():
                return error("Mã voucher đã hết hạn")

            from decimal import Decimal
            gia_tri = float(km["GiaTri"])

            if km["LoaiKM"] == "PHANTRAM":
                giam = round(tong_tien * gia_tri / 100, 2)
            else:  # TIENMAT
                giam = min(gia_tri, tong_tien)

            import json
            return jsonify({
                "success": True,
                "message": f"Áp dụng thành công voucher {ma_code}",
                "data": json.loads(json.dumps({
                    "MaKM":    km["MaKM"],
                    "MaCode":  km["MaCode"],
                    "LoaiKM":  km["LoaiKM"],
                    "GiaTri":  km["GiaTri"],
                    "GiamGia": giam,
                    "ThanhTien": round(tong_tien - giam, 2)
                }, default=_serialize))
            })
    except Exception as e:
        return error(str(e), 500)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# [5] THANH TOÁN ĐƠN HÀNG
# POST /payment/orders/<ma_don>/checkout
# Body:
# {
#   "phuong_thuc": "TIENMAT" | "CHUYENKHOAN" | "KETHOP",
#   "tien_mat": 100000,
#   "tien_chuyen_khoan": 0,
#   "ma_km": 1,          (optional)
#   "giam_gia": 5000,    (optional)
#   "vat": 0             (optional)
# }
# Logic:
#   1. Kiểm tra đơn hàng hợp lệ & chưa thanh toán
#   2. Tính tiền thối
#   3. Ghi bảng THANHTOAN
#   4. Cập nhật DONHANG: TrangThai=DATHANHTOAN, GiamGia, ThanhTien
#   5. Cập nhật BAN: TrangThai=TRONG
#   6. Ghi lịch sử đơn hàng (LICHSUDONHANG)
#   (Trừ nguyên liệu KHÔNG nằm ở đây — được xử lý ở module order khi thêm món)
# ─────────────────────────────────────────────

@payment_bp.route("/orders/<int:ma_don>/checkout", methods=["POST"])
def checkout(ma_don):
    data = request.get_json() or {}
    phuong_thuc       = data.get("phuong_thuc", "").upper()
    tien_mat          = float(data.get("tien_mat", 0))
    tien_chuyen_khoan = float(data.get("tien_chuyen_khoan", 0))
    ma_km             = data.get("ma_km")           # int hoặc None
    giam_gia          = float(data.get("giam_gia", 0))
    vat               = float(data.get("vat", 0))

    if phuong_thuc not in ("TIENMAT", "CHUYENKHOAN", "KETHOP"):
        return error("Phương thức thanh toán không hợp lệ")

    # Lấy MaNV từ session (nếu dự án có login); fallback = 1
    ma_nv = session.get("ma_nv", 1)

    conn = get_connection()
    try:
        with conn.cursor() as cur:

            # 1. Kiểm tra đơn hàng
            cur.execute("""
                SELECT MaDon, TrangThai, TongTien, MaBan, MaNV
                FROM DONHANG
                WHERE MaDon = %s
            """, (ma_don,))
            don = cur.fetchone()

            if not don:
                return error("Không tìm thấy đơn hàng")

            don_dict = dict(zip([d[0] for d in cur.description], don))

            if don_dict["TrangThai"] == "DATHANHTOAN":
                return error("Đơn hàng đã được thanh toán trước đó")
            if don_dict["TrangThai"] == "HUY":
                return error("Đơn hàng đã bị hủy")

            tong_tien  = float(don_dict["TongTien"])
            thanh_tien = round(tong_tien - giam_gia + vat, 2)
            if thanh_tien < 0:
                thanh_tien = 0.0

            # Tính tiền thối (chỉ áp dụng cho tiền mặt)
            tien_nhan  = tien_mat + tien_chuyen_khoan
            tien_thoi  = round(tien_nhan - thanh_tien, 2)
            if tien_thoi < 0:
                tien_thoi = 0.0

            # 2. Ghi bảng THANHTOAN
            cur.execute("""
                INSERT INTO THANHTOAN
                    (MaDon, MaKM, PhuongThuc, TienMat, TienChuyenKhoan,
                     TienThoi, VAT, NgayThanhToan)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                ma_don,
                ma_km if ma_km else None,
                phuong_thuc,
                tien_mat,
                tien_chuyen_khoan,
                tien_thoi,
                vat
            ))

            # 3. Cập nhật DONHANG
            cur.execute("""
                UPDATE DONHANG
                SET TrangThai = 'DATHANHTOAN',
                    GiamGia   = %s,
                    ThanhTien = %s
                WHERE MaDon = %s
            """, (giam_gia, thanh_tien, ma_don))

            # 4. Trả bàn về trạng thái TRONG
            cur.execute("""
                UPDATE BAN SET TrangThai = 'TRONG'
                WHERE MaBan = %s
            """, (don_dict["MaBan"],))

            # 5. Ghi lịch sử
            # (Trừ nguyên liệu được xử lý ở module order khi nhân viên thêm món,
            #  không liên quan đến bước thanh toán.)
            noi_dung = (
                f"Thanh toán {phuong_thuc} | "
                f"Tổng: {tong_tien:,.0f}đ | "
                f"Giảm: {giam_gia:,.0f}đ | "
                f"Thành tiền: {thanh_tien:,.0f}đ | "
                f"Tiền thối: {tien_thoi:,.0f}đ"
            )
            cur.execute("""
                INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung)
                VALUES (%s, %s, 'THANHTOAN', %s)
            """, (ma_don, ma_nv, noi_dung))

        conn.commit()
        return success({
            "MaDon":     ma_don,
            "ThanhTien": thanh_tien,
            "TienThoi":  tien_thoi,
            "TrangThai": "DATHANHTOAN"
        }, "Thanh toán thành công")

    except Exception as e:
        conn.rollback()
        return error(str(e), 500)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# [6] IN HÓA ĐƠN TẠM TÍNH (dữ liệu cho client render)
# GET /payment/orders/<ma_don>/receipt
# Trả về toàn bộ thông tin cần thiết để frontend render hóa đơn.
# ─────────────────────────────────────────────

@payment_bp.route("/orders/<int:ma_don>/receipt", methods=["GET"])
def get_receipt(ma_don):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Thông tin đơn hàng
            cur.execute("""
                SELECT
                    d.MaDon, d.NgayTao, d.TrangThai,
                    d.TongTien, d.GiamGia, d.ThanhTien,
                    b.TenBan,
                    nv.HoTen AS TenNhanVien
                FROM DONHANG d
                JOIN BAN b ON b.MaBan = d.MaBan
                JOIN NHANVIEN nv ON nv.MaNV = d.MaNV
                WHERE d.MaDon = %s
            """, (ma_don,))
            row = cur.fetchone()

            if not row:
                return error("Không tìm thấy đơn hàng", 404)

            cols   = [d[0] for d in cur.description]
            order  = dict(zip(cols, row))

            # Chi tiết món
            cur.execute("""
                SELECT
                    m.TenMon,
                    ct.SoLuong,
                    ct.DonGia,
                    ct.GhiChu,
                    ct.TrangThaiMon,
                    (ct.SoLuong * ct.DonGia) AS ThanhTienMon
                FROM CHITIETDONHANG ct
                JOIN MON m ON m.MaMon = ct.MaMon
                WHERE ct.MaDon = %s
                ORDER BY ct.MaCTDH
            """, (ma_don,))
            items = _rows_to_list(cur, cur.fetchall())
            order["ChiTiet"] = items

        import json
        return jsonify({
            "success": True,
            "message": "Thành công",
            "data": json.loads(json.dumps(order, default=_serialize))
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        conn.close()