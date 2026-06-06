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
      PUT    /order/<ma_don>/discount   Cập nhật giảm giá & ghi chú đơn
      GET    /order/<ma_don>/history    Lịch sử thao tác đơn

  - Quản lý trạng thái bàn
      GET    /order/tables              Lấy danh sách bàn + trạng thái
      PUT    /order/table/<ma_ban>/status   Cập nhật trạng thái bàn
      POST   /order/table/transfer      Chuyển bàn
      POST   /order/table/merge         Gộp bàn

  - Đặt bàn (Reservation)
      GET    /order/reservations        Danh sách đặt bàn
      POST   /order/reservations        Tạo đặt bàn mới
      GET    /order/reservations/<id>   Chi tiết đặt bàn
      PUT    /order/reservations/<id>   Cập nhật đặt bàn
      DELETE /order/reservations/<id>   Hủy đặt bàn
      POST   /order/reservations/<id>/checkin  Nhận bàn (DADAT → DANGSUDUNG)

LOGIC KHO NGUYÊN LIỆU:
  - Thêm món (add-item / update qty):  KHÔNG trừ kho, chỉ lưu vào CHITIETDONHANG
  - Gửi bếp (send):                   TRỪ KHO TẠM – trừ kho cho các món CHOLAM → DANGLAM
  - Hủy đơn (cancel):                 HOÀN KHO – chỉ hoàn những món đã gửi bếp (DANGLAM/DAPHUCVU)
  - Thanh toán (checkout - payment.py): TRỪ KHO CHÍNH THỨC đã được xử lý ở payment.py
    NOTE: Vì kho đã được trừ tạm lúc gửi bếp, payment.py KHÔNG cần trừ thêm.
    Việc trừ tạm lúc gửi bếp chính là trừ chính thức – hủy đơn sẽ hoàn lại nếu cần.
"""

from flask import Blueprint, request, jsonify, render_template
from app.database.db import get_connection
import datetime

from app.security.roles import role_required

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

@order_manage_bp.route("/create", methods=["POST"])
def create_order():
    """
    Tạo đơn hàng mới cho một bàn.
    Body JSON: { "MaBan": int, "MaNV": int }
    """
    data = request.json or {}
    ma_ban = data.get("MaBan")
    ma_nv  = data.get("MaNV", 1)

    if not ma_ban:
        return jsonify({"success": False, "message": "Thiếu mã bàn"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM BAN WHERE MaBan = %s", (ma_ban,))
        ban = cursor.fetchone()
        if not ban:
            return jsonify({"success": False, "message": "Bàn không tồn tại"}), 404

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

        now = datetime.datetime.now()
        cursor.execute(
            """
            INSERT INTO DONHANG (NgayTao, TrangThai, TongTien, GiamGia, ThanhTien, MaBan, MaNV)
            VALUES (%s, 'XACNHAN', 0, 0, 0, %s, %s)
            """,
            (now, ma_ban, ma_nv)
        )
        ma_don = cursor.lastrowid

        cursor.execute(
            "UPDATE BAN SET TrangThai = 'DANGSUDUNG' WHERE MaBan = %s",
            (ma_ban,)
        )

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


@order_manage_bp.route("/menu/search", methods=["GET"])
def search_menu():
    q     = request.args.get("q", "").strip()
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


@order_manage_bp.route("/<int:ma_don>/add-item", methods=["POST"])
def add_item(ma_don):
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
        cursor.execute(
            "SELECT * FROM DONHANG WHERE MaDon = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don,)
        )
        order = cursor.fetchone()
        if not order:
            return jsonify({"success": False, "message": "Đơn hàng không tồn tại hoặc đã không thể chỉnh sửa"}), 404

        cursor.execute("SELECT GiaBan, TenMon FROM MON WHERE MaMon = %s AND TrangThai = 'CONBAN'", (ma_mon,))
        mon = cursor.fetchone()
        if not mon:
            return jsonify({"success": False, "message": "Món không tồn tại hoặc đã hết bán"}), 404

        don_gia = float(mon["GiaBan"])
        ten_mon = mon["TenMon"]

        # ==============================================================
        # KHÔNG trừ kho khi thêm món – kho sẽ được trừ khi gửi bếp
        # Chỉ kiểm tra sơ bộ xem công thức có tồn tại không (tùy chọn)
        # ==============================================================

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
            new_qty = existing_item["SoLuong"] + so_luong
            cursor.execute(
                "UPDATE CHITIETDONHANG SET SoLuong = %s WHERE MaCTDH = %s",
                (new_qty, existing_item["MaCTDH"])
            )
        else:
            cursor.execute(
                """
                INSERT INTO CHITIETDONHANG (MaDon, MaMon, SoLuong, DonGia, GhiChu, TrangThaiMon)
                VALUES (%s, %s, %s, %s, %s, 'CHOLAM')
                """,
                (ma_don, ma_mon, so_luong, don_gia, ghi_chu)
            )

        _recalc_total(cursor, ma_don)

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

@order_manage_bp.route("/item/<int:ma_ctdh>/qty", methods=["PUT"])
def update_item_qty(ma_ctdh):
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

        # ==============================================================
        # KHÔNG điều chỉnh kho khi thay đổi số lượng món CHOLAM
        # Kho chỉ bị trừ khi gửi bếp (send)
        # ==============================================================

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


@order_manage_bp.route("/item/<int:ma_ctdh>/note", methods=["PUT"])
def update_item_note(ma_ctdh):
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


@order_manage_bp.route("/item/<int:ma_ctdh>", methods=["DELETE"])
def delete_item(ma_ctdh):
    ma_nv = request.args.get("MaNV", 1)

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT CTDH.MaDon, CTDH.TrangThaiMon, CTDH.MaMon, CTDH.SoLuong, M.TenMon
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

        # ==============================================================
        # KHÔNG hoàn kho khi xóa món CHOLAM – vì kho chưa bị trừ
        # Kho chỉ bị trừ khi gửi bếp (send), nên xóa CHOLAM không cần hoàn
        # ==============================================================

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

@order_manage_bp.route("/<int:ma_don>/send", methods=["POST"])
def send_to_kitchen(ma_don):
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

        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM CHITIETDONHANG WHERE MaDon = %s AND TrangThaiMon = 'CHOLAM'",
            (ma_don,)
        )
        cnt = cursor.fetchone()["cnt"]
        if cnt == 0:
            return jsonify({"success": False, "message": "Không có món nào cần gửi bếp"}), 400

        # ==============================================================
        # TRỪ KHO TẠM: chỉ trừ các món CHOLAM (chưa gửi bếp lần nào)
        # Đây là lần duy nhất kho bị trừ – hủy đơn sẽ hoàn lại
        # ==============================================================
        cursor.execute(
            "SELECT MaMon, SoLuong FROM CHITIETDONHANG WHERE MaDon = %s AND TrangThaiMon = 'CHOLAM'",
            (ma_don,)
        )
        mon_cho_gui = cursor.fetchall()

        for mon in mon_cho_gui:
            cursor.execute(
                "SELECT MaNL, SoLuongSuDung FROM CONGTHUC WHERE MaMon = %s",
                (mon["MaMon"],)
            )
            cong_thuc = cursor.fetchall()

            # Kiểm tra kho đủ không trước khi trừ
            for nl in cong_thuc:
                tong_tru = float(nl["SoLuongSuDung"]) * int(mon["SoLuong"])
                cursor.execute("SELECT TenNL, SoLuongTon FROM NGUYENLIEU WHERE MaNL = %s", (nl["MaNL"],))
                kho = cursor.fetchone()
                if not kho or float(kho["SoLuongTon"]) < tong_tru:
                    ten_nl = kho["TenNL"] if kho else f"NL#{nl['MaNL']}"
                    conn.rollback()
                    return jsonify({
                        "success": False,
                        "message": f"Kho không đủ nguyên liệu '{ten_nl}' để làm món"
                    }), 400

            # Trừ kho
            for nl in cong_thuc:
                tong_tru = float(nl["SoLuongSuDung"]) * int(mon["SoLuong"])
                cursor.execute(
                    "UPDATE NGUYENLIEU SET SoLuongTon = SoLuongTon - %s WHERE MaNL = %s",
                    (tong_tru, nl["MaNL"])
                )
        # ==============================================================

        # Chuyển trạng thái món CHOLAM → DANGLAM
        cursor.execute(
            "UPDATE CHITIETDONHANG SET TrangThaiMon = 'DANGLAM' WHERE MaDon = %s AND TrangThaiMon = 'CHOLAM'",
            (ma_don,)
        )

        cursor.execute(
            "UPDATE DONHANG SET TrangThai = 'DANGPHUCVU' WHERE MaDon = %s",
            (ma_don,)
        )

        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'GUIBEP', %s, %s)
            """,
            (ma_don, ma_nv, f"Gửi {cnt} món xuống bếp/bar (Đã trừ kho tạm)", datetime.datetime.now())
        )

        conn.commit()
        return jsonify({"success": True, "message": f"Đã gửi {cnt} món xuống bếp/bar"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@order_manage_bp.route("/<int:ma_don>/cancel", methods=["POST"])
@role_required("ADMIN", "THUNGAN", "NHANVIEN")

def cancel_order(ma_don):
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

        # ==============================================================
        # HOÀN KHO: Chỉ hoàn những món đã được gửi bếp (DANGLAM/DAPHUCVU)
        # Món CHOLAM chưa bị trừ kho, nên KHÔNG hoàn
        # ==============================================================
        cursor.execute(
            """
            SELECT MaMon, SoLuong, TrangThaiMon
            FROM CHITIETDONHANG
            WHERE MaDon = %s AND TrangThaiMon IN ('DANGLAM', 'DAPHUCVU')
            """,
            (ma_don,)
        )
        mon_da_gui = cursor.fetchall()

        for mon in mon_da_gui:
            cursor.execute(
                "SELECT MaNL, SoLuongSuDung FROM CONGTHUC WHERE MaMon = %s",
                (mon["MaMon"],)
            )
            cong_thuc = cursor.fetchall()

            for nl in cong_thuc:
                tong_hoan = float(nl["SoLuongSuDung"]) * int(mon["SoLuong"])
                cursor.execute(
                    """
                    UPDATE NGUYENLIEU
                    SET SoLuongTon = SoLuongTon + %s
                    WHERE MaNL = %s
                    """,
                    (tong_hoan, nl["MaNL"])
                )
        # ==============================================================

        cursor.execute(
            "UPDATE DONHANG SET TrangThai = 'HUY' WHERE MaDon = %s",
            (ma_don,)
        )

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

        so_mon_hoan = len(mon_da_gui)
        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'HUYDON', %s, %s)
            """,
            (ma_don, ma_nv,
             f"Hủy đơn: {ly_do} (Hoàn kho {so_mon_hoan} món đã gửi bếp)",
             datetime.datetime.now())
        )

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Đơn hàng đã được hủy. Đã hoàn kho {so_mon_hoan} món đã gửi bếp."
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ─────────────────────────────────────────────
# CẬP NHẬT GIẢM GIÁ & GHI CHÚ ĐƠN
# ─────────────────────────────────────────────
@order_manage_bp.route("/<int:ma_don>/discount", methods=["PUT"])
def update_order_discount(ma_don):
    """
    Cập nhật giảm giá trực tiếp trên đơn hàng (không qua bảng KHUYENMAI).
    Body JSON: { "GiamGia": float, "GhiChu": str|null, "MaNV": int }
    Chỉ áp dụng được khi đơn chưa thanh toán.
    """
    data     = request.json or {}
    giam_gia = float(data.get("GiamGia", 0))
    ghi_chu  = (data.get("GhiChu") or "").strip() or None
    ma_nv    = data.get("MaNV", 1)

    if giam_gia < 0:
        return jsonify({"success": False, "message": "Giảm giá không được âm"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM DONHANG WHERE MaDon = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU','CHOTHANHTOAN')",
            (ma_don,)
        )
        order = cursor.fetchone()
        if not order:
            return jsonify({"success": False, "message": "Không tìm thấy đơn hoặc đơn đã hoàn tất"}), 404

        tong_tien = float(order["TongTien"])
        if giam_gia > tong_tien:
            return jsonify({"success": False, "message": "Giảm giá không được lớn hơn tổng tiền"}), 400

        thanh_tien = tong_tien - giam_gia

        cursor.execute(
            "UPDATE DONHANG SET GiamGia = %s, ThanhTien = %s WHERE MaDon = %s",
            (giam_gia, thanh_tien, ma_don)
        )

        old_discount = float(order["GiamGia"])
        note = f"Cập nhật giảm giá: {int(old_discount):,}đ → {int(giam_gia):,}đ"
        if ghi_chu:
            note += f" | Ghi chú: {ghi_chu}"

        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'GIAMGIA', %s, %s)
            """,
            (ma_don, ma_nv, note, datetime.datetime.now())
        )

        conn.commit()
        return jsonify({
            "success": True,
            "message": "Đã cập nhật giảm giá",
            "TongTien":  tong_tien,
            "GiamGia":   giam_gia,
            "ThanhTien": thanh_tien
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# LỊCH SỬ THAO TÁC ĐƠN
# ─────────────────────────────────────────────
@order_manage_bp.route("/<int:ma_don>/history", methods=["GET"])
def get_order_history(ma_don):
    """
    Lấy toàn bộ lịch sử hành động của một đơn hàng.
    """
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT LS.MaLS, LS.HanhDong, LS.NoiDung, LS.ThoiGian,
                   NV.HoTen AS TenNhanVien
            FROM LICHSUDONHANG LS
            LEFT JOIN NHANVIEN NV ON LS.MaNV = NV.MaNV
            WHERE LS.MaDon = %s
            ORDER BY LS.ThoiGian DESC
            """,
            (ma_don,)
        )
        rows = cursor.fetchall()
        for r in rows:
            if r.get("ThoiGian") and hasattr(r["ThoiGian"], "strftime"):
                r["ThoiGian"] = r["ThoiGian"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"success": True, "data": rows})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════
#  QUẢN LÝ TRẠNG THÁI BÀN
# ═══════════════════════════════════════════════════

@order_manage_bp.route("/tables", methods=["GET"])
def get_tables():
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                B.MaBan, B.TenBan, B.SoChoNgoi, B.TrangThai,
                DH.MaDon, DH.TongTien, DH.GiamGia, DH.ThanhTien,
                DH.NgayTao, DH.TrangThai AS TrangThaiDon
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
                
            if t.get("GiamGia") is not None:
                t["GiamGia"] = float(t["GiamGia"])
                
            if t.get("ThanhTien") is not None:
                t["ThanhTien"] = float(t["ThanhTien"])

        return jsonify({"success": True, "data": tables})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@order_manage_bp.route("/table/<int:ma_ban>/status", methods=["PUT"])
def update_table_status(ma_ban):
    data       = request.json or {}
    trang_thai = data.get("TrangThai", "").upper()
    ma_nv      = data.get("MaNV", 1)

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


@order_manage_bp.route("/table/transfer", methods=["POST"])
def transfer_table():
    data       = request.json or {}
    ma_don     = data.get("MaDon")
    ma_ban_moi = data.get("MaBanMoi")
    ma_nv      = data.get("MaNV", 1)

    if not ma_don or not ma_ban_moi:
        return jsonify({"success": False, "message": "Thiếu MaDon hoặc MaBanMoi"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM DONHANG WHERE MaDon = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don,)
        )
        order = cursor.fetchone()
        if not order:
            return jsonify({"success": False, "message": "Đơn hàng không tồn tại hoặc không thể chuyển"}), 404

        ma_ban_cu = order["MaBan"]

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

        cursor.execute("SELECT TenBan FROM BAN WHERE MaBan = %s", (ma_ban_cu,))
        ten_ban_cu = cursor.fetchone()["TenBan"]

        cursor.execute(
            "UPDATE DONHANG SET MaBan = %s WHERE MaDon = %s",
            (ma_ban_moi, ma_don)
        )

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

        cursor.execute(
            "UPDATE BAN SET TrangThai = 'DANGSUDUNG' WHERE MaBan = %s",
            (ma_ban_moi,)
        )

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


@order_manage_bp.route("/table/merge", methods=["POST"])
def merge_tables():
    data         = request.json or {}
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
        cursor.execute(
            "SELECT DH.*, B.TenBan FROM DONHANG DH JOIN BAN B ON DH.MaBan=B.MaBan WHERE DH.MaDon = %s AND DH.TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don_chinh,)
        )
        don_chinh = cursor.fetchone()
        if not don_chinh:
            return jsonify({"success": False, "message": "Đơn chính không tồn tại hoặc không hợp lệ"}), 404

        cursor.execute(
            "SELECT DH.*, B.TenBan FROM DONHANG DH JOIN BAN B ON DH.MaBan=B.MaBan WHERE DH.MaDon = %s AND DH.TrangThai IN ('XACNHAN','DANGPHUCVU')",
            (ma_don_phu,)
        )
        don_phu = cursor.fetchone()
        if not don_phu:
            return jsonify({"success": False, "message": "Đơn phụ không tồn tại hoặc không hợp lệ"}), 404

        ma_ban_phu = don_phu["MaBan"]

        cursor.execute(
            "UPDATE CHITIETDONHANG SET MaDon = %s WHERE MaDon = %s",
            (ma_don_chinh, ma_don_phu)
        )

        _recalc_total(cursor, ma_don_chinh)

        cursor.execute(
            "UPDATE DONHANG SET TrangThai = 'HUY' WHERE MaDon = %s",
            (ma_don_phu,)
        )

        cursor.execute(
            "UPDATE BAN SET TrangThai = 'TRONG' WHERE MaBan = %s",
            (ma_ban_phu,)
        )

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
#  ĐẶT BÀN (RESERVATION)
# ═══════════════════════════════════════════════════

@order_manage_bp.route("/reservations", methods=["GET"])
def get_reservations():
    get_all  = request.args.get("all", "0") == "1"
    date_str = request.args.get("date", datetime.date.today().isoformat())

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if get_all:
            cursor.execute(
                """
                SELECT DB.*, B.TenBan, B.SoChoNgoi, B.TrangThai AS TrangThaiBan
                FROM DATBAN DB
                JOIN BAN B ON DB.MaBan = B.MaBan
                ORDER BY DB.GioDen ASC
                """
            )
        else:
            cursor.execute(
                """
                SELECT DB.*, B.TenBan, B.SoChoNgoi, B.TrangThai AS TrangThaiBan
                FROM DATBAN DB
                JOIN BAN B ON DB.MaBan = B.MaBan
                WHERE DATE(DB.GioDen) = %s
                ORDER BY DB.GioDen ASC
                """,
                (date_str,)
            )
        rows = cursor.fetchall()
        for r in rows:
            if r.get("GioDen") and hasattr(r["GioDen"], "strftime"):
                r["GioDen"] = r["GioDen"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"success": True, "data": rows})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@order_manage_bp.route("/reservations", methods=["POST"])
def create_reservation():
    data      = request.json or {}
    ma_ban    = data.get("MaBan")
    ten_khach = (data.get("TenKhach") or "").strip()
    sdt       = (data.get("SDT") or "").strip()
    gio_den   = data.get("GioDen")
    so_nguoi  = int(data.get("SoNguoi", 1))

    if not ma_ban:
        return jsonify({"success": False, "message": "Thiếu mã bàn"}), 400
    if not ten_khach:
        return jsonify({"success": False, "message": "Thiếu tên khách"}), 400
    if not sdt:
        return jsonify({"success": False, "message": "Thiếu số điện thoại"}), 400
    if not gio_den:
        return jsonify({"success": False, "message": "Thiếu giờ đến"}), 400
    if so_nguoi < 1:
        return jsonify({"success": False, "message": "Số người phải ≥ 1"}), 400

    try:
        gio_den_dt = datetime.datetime.strptime(gio_den, "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"success": False, "message": "Định dạng giờ đến không hợp lệ (YYYY-MM-DD HH:MM)"}), 400

    if gio_den_dt <= datetime.datetime.now():
        return jsonify({"success": False, "message": "Giờ đến phải là thời điểm trong tương lai"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM BAN WHERE MaBan = %s", (ma_ban,))
        ban = cursor.fetchone()
        if not ban:
            return jsonify({"success": False, "message": "Bàn không tồn tại"}), 404

        if so_nguoi > ban["SoChoNgoi"]:
            return jsonify({
                "success": False,
                "message": f"Bàn chỉ có {ban['SoChoNgoi']} chỗ, không đủ cho {so_nguoi} người"
            }), 400

        cursor.execute(
            """
            SELECT MaDatBan FROM DATBAN
            WHERE MaBan = %s
              AND ABS(TIMESTAMPDIFF(MINUTE, GioDen, %s)) < 120
            LIMIT 1
            """,
            (ma_ban, gio_den_dt)
        )
        conflict = cursor.fetchone()
        if conflict:
            return jsonify({
                "success": False,
                "message": "Bàn này đã có đặt chỗ trong khung giờ tương tự (±2 giờ)"
            }), 400

        cursor.execute(
            """
            INSERT INTO DATBAN (MaBan, TenKhach, SDT, GioDen, SoNguoi)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (ma_ban, ten_khach, sdt, gio_den_dt, so_nguoi)
        )
        ma_dat_ban = cursor.lastrowid

        if ban["TrangThai"] == "TRONG":
            cursor.execute(
                "UPDATE BAN SET TrangThai = 'DADAT' WHERE MaBan = %s",
                (ma_ban,)
            )

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Đã đặt {ban['TenBan']} cho khách {ten_khach}",
            "MaDatBan": ma_dat_ban
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@order_manage_bp.route("/reservations/<int:ma_dat_ban>", methods=["GET"])
def get_reservation(ma_dat_ban):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT DB.*, B.TenBan, B.SoChoNgoi, B.TrangThai AS TrangThaiBan
            FROM DATBAN DB
            JOIN BAN B ON DB.MaBan = B.MaBan
            WHERE DB.MaDatBan = %s
            """,
            (ma_dat_ban,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Không tìm thấy đặt bàn"}), 404

        if row.get("GioDen") and hasattr(row["GioDen"], "strftime"):
            row["GioDen"] = row["GioDen"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({"success": True, "data": row})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@order_manage_bp.route("/reservations/<int:ma_dat_ban>", methods=["PUT"])
def update_reservation(ma_dat_ban):
    data      = request.json or {}
    ten_khach = (data.get("TenKhach") or "").strip() or None
    sdt       = (data.get("SDT") or "").strip() or None
    gio_den   = data.get("GioDen")
    so_nguoi  = data.get("SoNguoi")

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT DB.*, B.SoChoNgoi
            FROM DATBAN DB
            JOIN BAN B ON DB.MaBan = B.MaBan
            WHERE DB.MaDatBan = %s
            """,
            (ma_dat_ban,)
        )
        dat_ban = cursor.fetchone()
        if not dat_ban:
            return jsonify({"success": False, "message": "Không tìm thấy đặt bàn"}), 404

        new_ten   = ten_khach or dat_ban["TenKhach"]
        new_sdt   = sdt or dat_ban["SDT"]
        new_sl    = int(so_nguoi) if so_nguoi is not None else dat_ban["SoNguoi"]

        if new_sl > dat_ban["SoChoNgoi"]:
            return jsonify({
                "success": False,
                "message": f"Bàn chỉ có {dat_ban['SoChoNgoi']} chỗ"
            }), 400

        if gio_den:
            try:
                new_gio_den = datetime.datetime.strptime(gio_den, "%Y-%m-%d %H:%M")
            except ValueError:
                return jsonify({"success": False, "message": "Định dạng giờ không hợp lệ"}), 400
        else:
            new_gio_den = dat_ban["GioDen"]

        cursor.execute(
            """
            UPDATE DATBAN
            SET TenKhach = %s, SDT = %s, GioDen = %s, SoNguoi = %s
            WHERE MaDatBan = %s
            """,
            (new_ten, new_sdt, new_gio_den, new_sl, ma_dat_ban)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Đã cập nhật đặt bàn"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@order_manage_bp.route("/reservations/<int:ma_dat_ban>", methods=["DELETE"])
def cancel_reservation(ma_dat_ban):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM DATBAN WHERE MaDatBan = %s", (ma_dat_ban,))
        dat_ban = cursor.fetchone()
        if not dat_ban:
            return jsonify({"success": False, "message": "Không tìm thấy đặt bàn"}), 404

        ma_ban = dat_ban["MaBan"]

        cursor.execute("DELETE FROM DATBAN WHERE MaDatBan = %s", (ma_dat_ban,))

        cursor2 = conn.cursor(dictionary=True)

        cursor2.execute(
            "SELECT COUNT(*) AS cnt FROM DATBAN WHERE MaBan = %s",
            (ma_ban,)
        )
        remaining = cursor2.fetchone()["cnt"]

        cursor2.execute(
            """
            SELECT COUNT(*) AS cnt FROM DONHANG
            WHERE MaBan = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU','CHOTHANHTOAN')
            """,
            (ma_ban,)
        )
        active_orders = cursor2.fetchone()["cnt"]
        cursor2.close()

        if remaining == 0 and active_orders == 0:
            cursor.execute(
                "UPDATE BAN SET TrangThai = 'TRONG' WHERE MaBan = %s",
                (ma_ban,)
            )

        conn.commit()
        return jsonify({"success": True, "message": "Đã hủy đặt bàn"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@order_manage_bp.route("/reservations/<int:ma_dat_ban>/checkin", methods=["POST"])
def checkin_reservation(ma_dat_ban):
    data  = request.json or {}
    ma_nv = data.get("MaNV", 1)

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT DB.*, B.TenBan, B.TrangThai AS TrangThaiBan
            FROM DATBAN DB
            JOIN BAN B ON DB.MaBan = B.MaBan
            WHERE DB.MaDatBan = %s
            """,
            (ma_dat_ban,)
        )
        dat_ban = cursor.fetchone()
        if not dat_ban:
            return jsonify({"success": False, "message": "Không tìm thấy đặt bàn"}), 404

        ma_ban = dat_ban["MaBan"]

        cursor.execute(
            """
            SELECT MaDon FROM DONHANG
            WHERE MaBan = %s AND TrangThai IN ('XACNHAN','DANGPHUCVU','CHOTHANHTOAN')
            LIMIT 1
            """,
            (ma_ban,)
        )
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                "success": False,
                "message": "Bàn này đã có đơn đang hoạt động",
                "MaDon": existing["MaDon"]
            }), 400

        now = datetime.datetime.now()
        cursor.execute(
            """
            INSERT INTO DONHANG (NgayTao, TrangThai, TongTien, GiamGia, ThanhTien, MaBan, MaNV)
            VALUES (%s, 'XACNHAN', 0, 0, 0, %s, %s)
            """,
            (now, ma_ban, ma_nv)
        )
        ma_don = cursor.lastrowid

        cursor.execute(
            "UPDATE BAN SET TrangThai = 'DANGSUDUNG' WHERE MaBan = %s",
            (ma_ban,)
        )

        cursor.execute("DELETE FROM DATBAN WHERE MaDatBan = %s", (ma_dat_ban,))

        cursor.execute(
            """
            INSERT INTO LICHSUDONHANG (MaDon, MaNV, HanhDong, NoiDung, ThoiGian)
            VALUES (%s, %s, 'TAODON', %s, %s)
            """,
            (
                ma_don, ma_nv,
                f"Nhận bàn đặt – {dat_ban['TenKhach']} ({dat_ban['SDT']}) – {dat_ban['TenBan']}",
                now
            )
        )

        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Đã nhận bàn cho khách {dat_ban['TenKhach']}",
            "MaDon": ma_don
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
