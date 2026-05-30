"""
order_manage.py
---------------
Blueprint: /order
Chức năng:
  - Gọi món & Tạo đơn hàng
      POST   /order/create              Tạo đơn hàng mới cho bàn
      GET    /order/<ma_don>            Lấy chi tiết đơn
      POST   /order/<ma_don>/add-item   Thêm món vào đơn
      PUT    /order/item/<ma_ctdh>/qty  Cập nhật số lượng
      PUT    /order/item/<ma_ctdh>/note Thêm/sửa ghi chú
      DELETE /order/item/<ma_ctdh>      Xóa món khỏi đơn
      POST   /order/<ma_don>/send       Gửi order xuống bếp/bar
      POST   /order/<ma_don>/cancel     Hủy đơn hàng

  - Quản lý trạng thái bàn
      GET    /order/tables              Lấy danh sách bàn + trạng thái
      PUT    /order/table/<ma_ban>/status   Cập nhật trạng thái bàn
      POST   /order/table/transfer      Chuyển bàn
      POST   /order/table/merge         Gộp bàn
"""

from flask import Blueprint, request, jsonify, render_template
from app.database.db import get_connection
import datetime

order_manage_bp = Blueprint("order_manage", __name__, url_prefix="/order")


# ─────────────────────────────────────────────
# TRANG GIAO DIỆN
# ─────────────────────────────────────────────
@order_manage_bp.route("/", methods=["GET"])
def order_page():
    return render_template("order.html")


# ═══════════════════════════════════════════════════
#  GỌI MÓN & TẠO ĐƠN HÀNG
# ═══════════════════════════════════════════════════

# ─────────────────────────────────────────────
# TẠO ĐƠN HÀNG MỚI
# ─────────────────────────────────────────────
@order_manage_bp.route("/create", methods=["POST"])
def create_order():
    """
    Tạo đơn hàng mới cho một bàn.
    Body JSON: { "MaBan": int, "MaNV": int }
    """
    data = request.json or {}
    ma_ban = data.get("MaBan")
    ma_nv  = data.get("MaNV", 1)   # default nv đầu tiên nếu chưa có auth

    if not ma_ban:
        return jsonify({"success": False, "message": "Thiếu mã bàn"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Kiểm tra bàn tồn tại
        cursor.execute("SELECT * FROM BAN WHERE MaBan = %s", (ma_ban,))
        ban = cursor.fetchone()
        if not ban:
            return jsonify({"success": False, "message": "Bàn không tồn tại"}), 404

        # Kiểm tra bàn đã có đơn đang hoạt động chưa
        cursor.execute(
            """
            SELECT MaDon FROM DONHANG
            WHERE MaBan = %s
              AND TrangThai IN ('XACNHAN','DANGPHUCVU','CHOTHANHTOAN')
            LIMIT 1
            """,
            (ma_ban,)
        )
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                "success": False,
                "message": "Bàn này đã có đơn hàng đang hoạt động",
                "MaDon": existing["MaDon"]
            }), 400

        # Tạo đơn
        now = datetime.datetime.now()
        cursor.execute(
            """
            INSERT INTO DONHANG (NgayTao, TrangThai, TongTien, GiamGia, ThanhTien, MaBan, MaNV)
            VALUES (%s, 'XACNHAN', 0, 0, 0, %s, %s)
            """,
            (now, ma_ban, ma_nv)
        )
        ma_don = cursor.lastrowid

        # Cập nhật trạng thái bàn → DANGSUDUNG
        cursor.execute(
            "UPDATE BAN SET TrangThai = 'DANGSUDUNG' WHERE MaBan = %s",
            (ma_ban,)
        )

        # Ghi lịch sử
        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'TAODON', %s, %s)
            """,
            (ma_don, ma_nv, f"Tạo đơn hàng mới cho {ban['TenBan']}", now)
        )

        conn.commit()
        return jsonify({
            "success": True,
            "message": "Tạo đơn hàng thành công",
            "MaDon": ma_don
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# LẤY CHI TIẾT ĐƠN HÀNG
# ─────────────────────────────────────────────
@order_manage_bp.route("/<int:ma_don>", methods=["GET"])
def get_order(ma_don):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT DH.*, B.TenBan, NV.HoTen AS TenNhanVien
            FROM DONHANG DH
            JOIN BAN B ON DH.MaBan = B.MaBan
            LEFT JOIN NHANVIEN NV ON DH.MaNV = NV.MaNV
            WHERE DH.MaDon = %s
            """,
            (ma_don,)
        )
        order = cursor.fetchone()
        if not order:
            return jsonify({"success": False, "message": "Không tìm thấy đơn hàng"}), 404

        cursor.execute(
            """
            SELECT CTDH.*, M.TenMon, M.MaDM, DC.TenDanhMuc
            FROM CHITIETDONHANG CTDH
            JOIN MON M ON CTDH.MaMon = M.MaMon
            LEFT JOIN DANHMUC DC ON M.MaDM = DC.MaDM
            WHERE CTDH.MaDon = %s
            ORDER BY CTDH.MaCTDH ASC
            """,
            (ma_don,)
        )
        items = cursor.fetchall()

        if order.get("NgayTao") and hasattr(order["NgayTao"], "strftime"):
            order["NgayTao"] = order["NgayTao"].strftime("%Y-%m-%d %H:%M:%S")

        # Chuyển Decimal sang float
        for key in ("TongTien", "GiamGia", "ThanhTien"):
            if order.get(key) is not None:
                order[key] = float(order[key])

        for item in items:
            for key in ("DonGia",):
                if item.get(key) is not None:
                    item[key] = float(item[key])

        order["ChiTiet"] = items
        return jsonify({"success": True, "data": order})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# TÌM KIẾM MÓN (dùng cho autocomplete khi gọi món)
# ─────────────────────────────────────────────
@order_manage_bp.route("/menu/search", methods=["GET"])
def search_menu():
    """
    GET /order/menu/search?q=ca+phe&dm=1
    Trả danh sách món đang bán, hỗ trợ lọc theo tên & danh mục.
    """
    q    = request.args.get("q", "").strip()
    ma_dm = request.args.get("dm")

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sql    = """
            SELECT M.MaMon, M.TenMon, M.GiaBan, M.MoTa, DC.TenDanhMuc, M.MaDM
            FROM MON M
            JOIN DANHMUC DC ON M.MaDM = DC.MaDM
            WHERE M.TrangThai = 'CONBAN'
        """
        params = []

        if q:
            sql += " AND M.TenMon LIKE %s"
            params.append(f"%{q}%")

        if ma_dm:
            sql += " AND M.MaDM = %s"
            params.append(int(ma_dm))

        sql += " ORDER BY DC.MaDM, M.TenMon LIMIT 60"
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        for r in rows:
            r["GiaBan"] = float(r["GiaBan"])

        return jsonify({"success": True, "data": rows})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# LẤY DANH MỤC (cho filter)
# ─────────────────────────────────────────────
@order_manage_bp.route("/menu/categories", methods=["GET"])
def get_categories():
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM DANHMUC ORDER BY MaDM")
        rows = cursor.fetchall()
        return jsonify({"success": True, "data": rows})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# THÊM MÓN VÀO ĐƠN
# ─────────────────────────────────────────────
@order_manage_bp.route("/<int:ma_don>/add-item", methods=["POST"])
def add_item(ma_don):
    """
    Body JSON: { "MaMon": int, "SoLuong": int, "GhiChu": str|null }
    Nếu món đã có trong đơn (trạng thái CHOLAM) thì cộng thêm SoLuong.
    """
    data     = request.json or {}
    ma_mon   = data.get("MaMon")
    so_luong = int(data.get("SoLuong", 1))
    ghi_chu  = (data.get("GhiChu") or "").strip() or None
    ma_nv    = data.get("MaNV", 1)

    if not ma_mon or so_luong < 1:
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Kiểm tra đơn hàng
        cursor.execute(
            "SELECT * FROM DONHANG WHERE MaDon = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don,)
        )
        order = cursor.fetchone()
        if not order:
            return jsonify({"success": False, "message": "Đơn hàng không tồn tại hoặc đã không thể chỉnh sửa"}), 404

        # Lấy giá món
        cursor.execute("SELECT GiaBan, TenMon FROM MON WHERE MaMon = %s AND TrangThai = 'CONBAN'", (ma_mon,))
        mon = cursor.fetchone()
        if not mon:
            return jsonify({"success": False, "message": "Món không tồn tại hoặc đã hết bán"}), 404

        don_gia  = float(mon["GiaBan"])
        ten_mon  = mon["TenMon"]

        # Kiểm tra món đã có trong đơn và trạng thái CHOLAM chưa
        cursor.execute(
            """
            SELECT MaCTDH, SoLuong FROM CHITIETDONHANG
            WHERE MaDon = %s AND MaMon = %s AND TrangThaiMon = 'CHOLAM'
            LIMIT 1
            """,
            (ma_don, ma_mon)
        )
        existing_item = cursor.fetchone()

        if existing_item:
            # Cộng thêm số lượng
            new_qty = existing_item["SoLuong"] + so_luong
            cursor.execute(
                "UPDATE CHITIETDONHANG SET SoLuong = %s WHERE MaCTDH = %s",
                (new_qty, existing_item["MaCTDH"])
            )
        else:
            # Thêm dòng mới
            cursor.execute(
                """
                INSERT INTO CHITIETDONHANG (MaDon, MaMon, SoLuong, DonGia, GhiChu, TrangThaiMon)
                VALUES (%s, %s, %s, %s, %s, 'CHOLAM')
                """,
                (ma_don, ma_mon, so_luong, don_gia, ghi_chu)
            )

        # Tính lại TongTien
        _recalc_total(cursor, ma_don)

        # Lịch sử
        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'THEMMON', %s, %s)
            """,
            (ma_don, ma_nv, f"Thêm {so_luong}x {ten_mon}", datetime.datetime.now())
        )

        conn.commit()
        return jsonify({"success": True, "message": f"Đã thêm {ten_mon} vào đơn"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# CẬP NHẬT SỐ LƯỢNG MÓN
# ─────────────────────────────────────────────
@order_manage_bp.route("/item/<int:ma_ctdh>/qty", methods=["PUT"])
def update_item_qty(ma_ctdh):
    """
    Body JSON: { "SoLuong": int, "MaNV": int }
    SoLuong = 0 → xóa dòng.
    """
    data     = request.json or {}
    so_luong = int(data.get("SoLuong", 1))
    ma_nv    = data.get("MaNV", 1)

    if so_luong < 0:
        return jsonify({"success": False, "message": "Số lượng không hợp lệ"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT CTDH.*, M.TenMon
            FROM CHITIETDONHANG CTDH
            JOIN MON M ON CTDH.MaMon = M.MaMon
            WHERE CTDH.MaCTDH = %s AND CTDH.TrangThaiMon = 'CHOLAM'
            """,
            (ma_ctdh,)
        )
        item = cursor.fetchone()
        if not item:
            return jsonify({"success": False, "message": "Không tìm thấy món hoặc món đã được gửi bếp"}), 404

        ma_don = item["MaDon"]

        if so_luong == 0:
            cursor.execute("DELETE FROM CHITIETDONHANG WHERE MaCTDH = %s", (ma_ctdh,))
            action_note = f"Xóa {item['TenMon']} khỏi đơn"
        else:
            cursor.execute(
                "UPDATE CHITIETDONHANG SET SoLuong = %s WHERE MaCTDH = %s",
                (so_luong, ma_ctdh)
            )
            action_note = f"Cập nhật SL {item['TenMon']}: {item['SoLuong']} → {so_luong}"

        _recalc_total(cursor, ma_don)

        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'CAPNHAT', %s, %s)
            """,
            (ma_don, ma_nv, action_note, datetime.datetime.now())
        )

        conn.commit()
        return jsonify({"success": True, "message": "Cập nhật thành công"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# THÊM / SỬA GHI CHÚ MÓN
# ─────────────────────────────────────────────
@order_manage_bp.route("/item/<int:ma_ctdh>/note", methods=["PUT"])
def update_item_note(ma_ctdh):
    """
    Body JSON: { "GhiChu": str, "MaNV": int }
    """
    data    = request.json or {}
    ghi_chu = (data.get("GhiChu") or "").strip() or None
    ma_nv   = data.get("MaNV", 1)

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT MaDon, TrangThaiMon FROM CHITIETDONHANG WHERE MaCTDH = %s",
            (ma_ctdh,)
        )
        item = cursor.fetchone()
        if not item:
            return jsonify({"success": False, "message": "Không tìm thấy dòng chi tiết"}), 404

        cursor.execute(
            "UPDATE CHITIETDONHANG SET GhiChu = %s WHERE MaCTDH = %s",
            (ghi_chu, ma_ctdh)
        )

        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'GHICHU', %s, %s)
            """,
            (item["MaDon"], ma_nv, f"Cập nhật ghi chú món #{ma_ctdh}", datetime.datetime.now())
        )

        conn.commit()
        return jsonify({"success": True, "message": "Đã cập nhật ghi chú"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# XÓA MÓN KHỎI ĐƠN
# ─────────────────────────────────────────────
@order_manage_bp.route("/item/<int:ma_ctdh>", methods=["DELETE"])
def delete_item(ma_ctdh):
    ma_nv = request.args.get("MaNV", 1)

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT CTDH.MaDon, CTDH.TrangThaiMon, M.TenMon
            FROM CHITIETDONHANG CTDH
            JOIN MON M ON CTDH.MaMon = M.MaMon
            WHERE CTDH.MaCTDH = %s
            """,
            (ma_ctdh,)
        )
        item = cursor.fetchone()
        if not item:
            return jsonify({"success": False, "message": "Không tìm thấy món"}), 404

        if item["TrangThaiMon"] not in ("CHOLAM",):
            return jsonify({
                "success": False,
                "message": "Chỉ xóa được món chưa gửi bếp (trạng thái CHOLAM)"
            }), 400

        ma_don = item["MaDon"]
        cursor.execute("DELETE FROM CHITIETDONHANG WHERE MaCTDH = %s", (ma_ctdh,))
        _recalc_total(cursor, ma_don)

        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'XOAMON', %s, %s)
            """,
            (ma_don, ma_nv, f"Xóa {item['TenMon']} khỏi đơn", datetime.datetime.now())
        )

        conn.commit()
        return jsonify({"success": True, "message": "Đã xóa món khỏi đơn"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# GỬI ORDER XUỐNG BẾP / BAR
# ─────────────────────────────────────────────
@order_manage_bp.route("/<int:ma_don>/send", methods=["POST"])
def send_to_kitchen(ma_don):
    """
    Chuyển tất cả món CHOLAM → DANGLAM và đơn hàng → DANGPHUCVU.
    Body JSON: { "MaNV": int }
    """
    data  = request.json or {}
    ma_nv = data.get("MaNV", 1)

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM DONHANG WHERE MaDon = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don,)
        )
        order = cursor.fetchone()
        if not order:
            return jsonify({"success": False, "message": "Không tìm thấy đơn hoặc đơn không thể gửi"}), 404

        # Kiểm tra có món CHOLAM không
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM CHITIETDONHANG WHERE MaDon = %s AND TrangThaiMon = 'CHOLAM'",
            (ma_don,)
        )
        cnt = cursor.fetchone()["cnt"]
        if cnt == 0:
            return jsonify({"success": False, "message": "Không có món nào cần gửi bếp"}), 400

        # Cập nhật trạng thái món
        cursor.execute(
            "UPDATE CHITIETDONHANG SET TrangThaiMon = 'DANGLAM' WHERE MaDon = %s AND TrangThaiMon = 'CHOLAM'",
            (ma_don,)
        )

        # Cập nhật trạng thái đơn
        cursor.execute(
            "UPDATE DONHANG SET TrangThai = 'DANGPHUCVU' WHERE MaDon = %s",
            (ma_don,)
        )

        # Lịch sử
        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'GUIBEP', %s, %s)
            """,
            (ma_don, ma_nv, f"Gửi {cnt} món xuống bếp/bar", datetime.datetime.now())
        )

        conn.commit()
        return jsonify({"success": True, "message": f"Đã gửi {cnt} món xuống bếp/bar"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# HỦY ĐƠN HÀNG
# ─────────────────────────────────────────────
@order_manage_bp.route("/<int:ma_don>/cancel", methods=["POST"])
def cancel_order(ma_don):
    """
    Body JSON: { "LyDo": str, "MaNV": int }
    Chỉ hủy được đơn ở trạng thái XACNHAN hoặc DANGPHUCVU.
    """
    data  = request.json or {}
    ly_do = (data.get("LyDo") or "Hủy theo yêu cầu").strip()
    ma_nv = data.get("MaNV", 1)

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM DONHANG WHERE MaDon = %s", (ma_don,))
        order = cursor.fetchone()
        if not order:
            return jsonify({"success": False, "message": "Không tìm thấy đơn hàng"}), 404

        if order["TrangThai"] not in ("XACNHAN", "DANGPHUCVU"):
            return jsonify({
                "success": False,
                "message": f"Không thể hủy đơn ở trạng thái {order['TrangThai']}"
            }), 400

        # Hủy đơn
        cursor.execute(
            "UPDATE DONHANG SET TrangThai = 'HUY' WHERE MaDon = %s",
            (ma_don,)
        )

        # Giải phóng bàn nếu không còn đơn hoạt động
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt FROM DONHANG
            WHERE MaBan = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU','CHOTHANHTOAN')
            """,
            (order["MaBan"],)
        )
        remaining = cursor.fetchone()["cnt"]
        if remaining == 0:
            cursor.execute(
                "UPDATE BAN SET TrangThai = 'TRONG' WHERE MaBan = %s",
                (order["MaBan"],)
            )

        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'HUYDON', %s, %s)
            """,
            (ma_don, ma_nv, f"Hủy đơn: {ly_do}", datetime.datetime.now())
        )

        conn.commit()
        return jsonify({"success": True, "message": "Đơn hàng đã được hủy"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════
#  QUẢN LÝ TRẠNG THÁI BÀN
# ═══════════════════════════════════════════════════

# ─────────────────────────────────────────────
# DANH SÁCH BÀN + TRẠNG THÁI
# ─────────────────────────────────────────────
@order_manage_bp.route("/tables", methods=["GET"])
def get_tables():
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                B.MaBan, B.TenBan, B.SoChoNgoi, B.TrangThai,
                DH.MaDon, DH.TongTien, DH.NgayTao, DH.TrangThai AS TrangThaiDon
            FROM BAN B
            LEFT JOIN DONHANG DH
                ON B.MaBan = DH.MaBan
               AND DH.TrangThai IN ('XACNHAN','DANGPHUCVU','CHOTHANHTOAN')
            ORDER BY B.MaBan
            """
        )
        tables = cursor.fetchall()
        for t in tables:
            if t.get("NgayTao") and hasattr(t["NgayTao"], "strftime"):
                t["NgayTao"] = t["NgayTao"].strftime("%Y-%m-%d %H:%M:%S")
            if t.get("TongTien") is not None:
                t["TongTien"] = float(t["TongTien"])
        return jsonify({"success": True, "data": tables})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# CẬP NHẬT TRẠNG THÁI BÀN
# ─────────────────────────────────────────────
@order_manage_bp.route("/table/<int:ma_ban>/status", methods=["PUT"])
def update_table_status(ma_ban):
    """
    Body JSON: { "TrangThai": "TRONG"|"DANGSUDUNG"|"DADAT", "MaNV": int }
    """
    data      = request.json or {}
    trang_thai = data.get("TrangThai", "").upper()
    ma_nv     = data.get("MaNV", 1)

    VALID_STATUS = ("TRONG", "DANGSUDUNG", "DADAT")
    if trang_thai not in VALID_STATUS:
        return jsonify({
            "success": False,
            "message": f"Trạng thái không hợp lệ. Cho phép: {', '.join(VALID_STATUS)}"
        }), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM BAN WHERE MaBan = %s", (ma_ban,))
        ban = cursor.fetchone()
        if not ban:
            return jsonify({"success": False, "message": "Bàn không tồn tại"}), 404

        old_status = ban["TrangThai"]
        cursor.execute(
            "UPDATE BAN SET TrangThai = %s WHERE MaBan = %s",
            (trang_thai, ma_ban)
        )

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Cập nhật {ban['TenBan']}: {old_status} → {trang_thai}"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# CHUYỂN BÀN
# ─────────────────────────────────────────────
@order_manage_bp.route("/table/transfer", methods=["POST"])
def transfer_table():
    """
    Body JSON: { "MaDon": int, "MaBanMoi": int, "MaNV": int }
    Chuyển toàn bộ đơn hàng đang hoạt động từ bàn cũ sang bàn mới.
    Điều kiện: bàn mới phải TRONG.
    """
    data      = request.json or {}
    ma_don    = data.get("MaDon")
    ma_ban_moi = data.get("MaBanMoi")
    ma_nv     = data.get("MaNV", 1)

    if not ma_don or not ma_ban_moi:
        return jsonify({"success": False, "message": "Thiếu MaDon hoặc MaBanMoi"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Lấy đơn hàng
        cursor.execute(
            "SELECT * FROM DONHANG WHERE MaDon = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don,)
        )
        order = cursor.fetchone()
        if not order:
            return jsonify({"success": False, "message": "Đơn hàng không tồn tại hoặc không thể chuyển"}), 404

        ma_ban_cu = order["MaBan"]

        # Kiểm tra bàn mới
        cursor.execute("SELECT * FROM BAN WHERE MaBan = %s", (ma_ban_moi,))
        ban_moi = cursor.fetchone()
        if not ban_moi:
            return jsonify({"success": False, "message": "Bàn mới không tồn tại"}), 404

        if ban_moi["TrangThai"] != "TRONG":
            return jsonify({
                "success": False,
                "message": f"Bàn {ban_moi['TenBan']} hiện đang {ban_moi['TrangThai']}, không thể chuyển"
            }), 400

        if ma_ban_cu == ma_ban_moi:
            return jsonify({"success": False, "message": "Bàn mới phải khác bàn cũ"}), 400

        # Lấy tên bàn cũ
        cursor.execute("SELECT TenBan FROM BAN WHERE MaBan = %s", (ma_ban_cu,))
        ten_ban_cu = cursor.fetchone()["TenBan"]

        # Cập nhật đơn hàng
        cursor.execute(
            "UPDATE DONHANG SET MaBan = %s WHERE MaDon = %s",
            (ma_ban_moi, ma_don)
        )

        # Trạng thái bàn cũ: kiểm tra xem còn đơn không
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt FROM DONHANG
            WHERE MaBan = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU','CHOTHANHTOAN')
            """,
            (ma_ban_cu,)
        )
        remaining = cursor.fetchone()["cnt"]
        if remaining == 0:
            cursor.execute(
                "UPDATE BAN SET TrangThai = 'TRONG' WHERE MaBan = %s",
                (ma_ban_cu,)
            )

        # Bàn mới → DANGSUDUNG
        cursor.execute(
            "UPDATE BAN SET TrangThai = 'DANGSUDUNG' WHERE MaBan = %s",
            (ma_ban_moi,)
        )

        # Lịch sử
        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'CHUYENBAN', %s, %s)
            """,
            (
                ma_don, ma_nv,
                f"Chuyển từ {ten_ban_cu} → {ban_moi['TenBan']}",
                datetime.datetime.now()
            )
        )

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Đã chuyển đơn từ {ten_ban_cu} sang {ban_moi['TenBan']}"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# GỘP BÀN
# ─────────────────────────────────────────────
@order_manage_bp.route("/table/merge", methods=["POST"])
def merge_tables():
    """
    Body JSON: { "MaDonChinh": int, "MaDonPhu": int, "MaNV": int }
    Gộp đơn phụ vào đơn chính: chuyển toàn bộ CHITIETDONHANG của đơn phụ sang đơn chính,
    hủy đơn phụ và giải phóng bàn phụ.
    """
    data       = request.json or {}
    ma_don_chinh = data.get("MaDonChinh")
    ma_don_phu   = data.get("MaDonPhu")
    ma_nv        = data.get("MaNV", 1)

    if not ma_don_chinh or not ma_don_phu:
        return jsonify({"success": False, "message": "Thiếu MaDonChinh hoặc MaDonPhu"}), 400

    if ma_don_chinh == ma_don_phu:
        return jsonify({"success": False, "message": "Đơn chính và đơn phụ phải khác nhau"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Lấy đơn chính
        cursor.execute(
            "SELECT DH.*, B.TenBan FROM DONHANG DH JOIN BAN B ON DH.MaBan=B.MaBan WHERE DH.MaDon = %s AND DH.TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don_chinh,)
        )
        don_chinh = cursor.fetchone()
        if not don_chinh:
            return jsonify({"success": False, "message": "Đơn chính không tồn tại hoặc không hợp lệ"}), 404

        # Lấy đơn phụ
        cursor.execute(
            "SELECT DH.*, B.TenBan FROM DONHANG DH JOIN BAN B ON DH.MaBan=B.MaBan WHERE DH.MaDon = %s AND DH.TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don_phu,)
        )
        don_phu = cursor.fetchone()
        if not don_phu:
            return jsonify({"success": False, "message": "Đơn phụ không tồn tại hoặc không hợp lệ"}), 404

        ma_ban_phu = don_phu["MaBan"]

        # Chuyển tất cả CHITIETDONHANG của đơn phụ sang đơn chính
        cursor.execute(
            "UPDATE CHITIETDONHANG SET MaDon = %s WHERE MaDon = %s",
            (ma_don_chinh, ma_don_phu)
        )

        # Tính lại tổng tiền đơn chính
        _recalc_total(cursor, ma_don_chinh)

        # Hủy đơn phụ
        cursor.execute(
            "UPDATE DONHANG SET TrangThai = 'HUY' WHERE MaDon = %s",
            (ma_don_phu,)
        )

        # Giải phóng bàn phụ
        cursor.execute(
            "UPDATE BAN SET TrangThai = 'TRONG' WHERE MaBan = %s",
            (ma_ban_phu,)
        )

        # Lịch sử
        now = datetime.datetime.now()
        noi_dung = f"Gộp {don_phu['TenBan']} vào {don_chinh['TenBan']}"
        for ma_don_log in (ma_don_chinh, ma_don_phu):
            cursor.execute(
                """
                INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
                VALUES (%s, %s, 'GOPBAN', %s, %s)
                """,
                (ma_don_log, ma_nv, noi_dung, now)
            )

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Đã gộp {don_phu['TenBan']} vào {don_chinh['TenBan']}"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════

def _recalc_total(cursor, ma_don):
    """Tính lại TongTien và ThanhTien cho đơn hàng (không commit)."""
    cursor.execute(
        """
        SELECT COALESCE(SUM(SoLuong * DonGia), 0) AS total
        FROM CHITIETDONHANG
        WHERE MaDon = %s
        """,
        (ma_don,)
    )
    total = float(cursor.fetchone()["total"])
    cursor.execute(
        """
        UPDATE DONHANG
        SET TongTien = %s, ThanhTien = %s - GiamGia
        WHERE MaDon = %s
        """,
        (total, total, ma_don)
    )
