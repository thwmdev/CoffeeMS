from flask import Blueprint, make_response, request, jsonify, render_template
from app.database.db import get_connection
from app.security.roles import role_required
import datetime

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")


# =========================
# GIAO DIỆN
# =========================
@payment_bp.route("/", methods=["GET"])
def payment_page():
    return render_template("payment.html")


# =========================
# LẤY ĐƠN HÀNG THEO BÀN
# =========================
@payment_bp.route("/order/table/<int:ma_ban>", methods=["GET"])
def get_order_by_table(ma_ban):
    """
    UC02 – Bước 1: Hiển thị đơn hàng của bàn đang chờ thanh toán.
    Chỉ lấy đơn ở trạng thái XACNHAN / DANGPHUCVU / HOANTHANH.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                DH.MaDon,
                DH.NgayTao,
                DH.TrangThai,
                DH.TongTien,
                DH.GiamGia,
                DH.ThanhTien,
                DH.MaBan,
                DH.MaNV,
                B.TenBan,
                NV.HoTen AS TenNhanVien
            FROM DONHANG DH
            JOIN BAN B ON DH.MaBan = B.MaBan
            LEFT JOIN NHANVIEN NV ON DH.MaNV = NV.MaNV
            WHERE DH.MaBan = %s
              AND DH.TrangThai IN ('XACNHAN','DANGPHUCVU','HOANTHANH')
            ORDER BY DH.NgayTao DESC
            LIMIT 1
            """,
            (ma_ban,)
        )
        order = cursor.fetchone()

        if not order:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy đơn hàng cho bàn này"
            }), 404

        # Lấy chi tiết từng món
        cursor.execute(
            """
            SELECT
                CTDH.MaCTDH,
                CTDH.MaMon,
                CTDH.SoLuong,
                CTDH.DonGia,
                CTDH.GhiChu,
                CTDH.TrangThaiMon,
                MON.TenMon
            FROM CHITIETDONHANG CTDH
            JOIN MON ON CTDH.MaMon = MON.MaMon
            WHERE CTDH.MaDon = %s
            """,
            (order["MaDon"],)
        )
        items = cursor.fetchall()

        # Chuyển datetime sang string
        if order.get("NgayTao") and hasattr(order["NgayTao"], "strftime"):
            order["NgayTao"] = order["NgayTao"].strftime("%Y-%m-%d %H:%M:%S")

        order["ChiTiet"] = items

        return jsonify({"success": True, "data": order})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# LẤY ĐƠN HÀNG THEO MÃ ĐƠN
# =========================
@payment_bp.route("/order/<int:ma_don>", methods=["GET"])
def get_order_by_id(ma_don):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                DH.MaDon,
                DH.NgayTao,
                DH.TrangThai,
                DH.TongTien,
                DH.GiamGia,
                DH.ThanhTien,
                DH.MaBan,
                DH.MaNV,
                B.TenBan,
                NV.HoTen AS TenNhanVien
            FROM DONHANG DH
            JOIN BAN B ON DH.MaBan = B.MaBan
            LEFT JOIN NHANVIEN NV ON DH.MaNV = NV.MaNV
            WHERE DH.MaDon = %s
              AND DH.TrangThai IN ('XACNHAN','DANGPHUCVU','HOANTHANH')
            """,
            (ma_don,)
        )
        order = cursor.fetchone()

        if not order:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy đơn hàng"
            }), 404

        cursor.execute(
            """
            SELECT CTDH.*, MON.TenMon
            FROM CHITIETDONHANG CTDH
            JOIN MON ON CTDH.MaMon = MON.MaMon
            WHERE CTDH.MaDon = %s
            """,
            (ma_don,)
        )
        items = cursor.fetchall()

        if order.get("NgayTao") and hasattr(order["NgayTao"], "strftime"):
            order["NgayTao"] = order["NgayTao"].strftime("%Y-%m-%d %H:%M:%S")

        order["ChiTiet"] = items
        return jsonify({"success": True, "data": order})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# LẤY DANH SÁCH BÀN CÓ ĐƠN ĐANG CHỜ
# =========================
@payment_bp.route("/tables", methods=["GET"])
def get_tables_with_orders():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                B.MaBan,
                B.TenBan,
                B.TrangThai,
                DH.MaDon,
                DH.TongTien,
                DH.NgayTao
            FROM BAN B
            LEFT JOIN DONHANG DH
                ON B.MaBan = DH.MaBan
                AND DH.TrangThai IN ('XACNHAN','DANGPHUCVU','HOANTHANH')
            ORDER BY B.MaBan
            """
        )
        tables = cursor.fetchall()

        for t in tables:
            if t.get("NgayTao") and hasattr(t["NgayTao"], "strftime"):
                t["NgayTao"] = t["NgayTao"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({"success": True, "data": tables})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# ÁP DỤNG MÃ GIẢM GIÁ (UC02.1)
# =========================
@payment_bp.route("/apply-voucher", methods=["POST"])
def apply_voucher():
    """
    UC02.1 – Kiểm tra và tính giá trị giảm giá của voucher.
    Trả về số tiền giảm và tổng thanh toán mới.
    """
    data = request.json
    ma_code  = (data.get("MaCode") or "").strip()
    tong_tien = float(data.get("TongTien", 0))

    if not ma_code:
        return jsonify({
            "success": False,
            "message": "Vui lòng nhập mã giảm giá"
        }), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM KHUYENMAI
            WHERE MaCode = %s
              AND TrangThai = 'HOATDONG'
              AND (NgayHetHan IS NULL OR NgayHetHan >= NOW())
            """,
            (ma_code,)
        )
        voucher = cursor.fetchone()

        if not voucher:
            return jsonify({
                "success": False,
                "message": "Mã giảm giá không hợp lệ hoặc đã hết hạn"
            }), 400

        # Tính số tiền giảm
        if voucher["LoaiKM"] == "PHANTRAM":
            giam_gia = tong_tien * float(voucher["GiaTri"]) / 100
        else:
            # SOTIEN – giảm cố định, không vượt tổng tiền
            giam_gia = min(float(voucher["GiaTri"]), tong_tien)

        thanh_tien = tong_tien - giam_gia

        return jsonify({
            "success": True,
            "MaKM": voucher["MaKM"],
            "GiamGia": round(giam_gia, 2),
            "ThanhTien": round(thanh_tien, 2),
            "message": f"Áp dụng thành công – Giảm {giam_gia:,.0f}đ"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# HOÀN TẤT THANH TOÁN (UC02 – Bước 4)
# =========================
@payment_bp.route("/checkout", methods=["POST"])
def checkout():
    """
    UC02 – Bước 4:
      1. Ghi bản ghi THANHTOAN
      2. Cập nhật DONHANG.TrangThai = 'DATHANHTOAN', GiamGia, ThanhTien
      3. Giải phóng bàn (BAN.TrangThai = 'TRONG')
      4. Trừ nguyên liệu thực tế khỏi tồn kho (SoLuongTon), giải phóng SoLuongTruTam
      5. Đánh dấu voucher đã dùng (nếu có)
    """
    data = request.json

    ma_don      = data.get("MaDon")
    phuong_thuc = data.get("PhuongThuc", "TIENMAT")   # TIENMAT | CHUYENKHOAN | QR
    so_tien_vao = float(data.get("SoTienVao", 0))
    ma_km       = data.get("MaKM")                    # optional
    giam_gia    = float(data.get("GiamGia", 0))
    vat_rate    = float(data.get("VATRate", 0.1))      # mặc định 10%

    if not ma_don:
        return jsonify({"success": False, "message": "Thiếu mã đơn hàng"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Lấy đơn hàng
        cursor.execute(
            "SELECT * FROM DONHANG WHERE MaDon = %s",
            (ma_don,)
        )
        order = cursor.fetchone()

        if not order:
            return jsonify({"success": False, "message": "Không tìm thấy đơn hàng"}), 404

        if order["TrangThai"] == "DATHANHTOAN":
            return jsonify({
                "success": False,
                "message": "Đơn hàng này đã được thanh toán"
            }), 400

        tong_tien  = float(order["TongTien"])
        vat        = round(tong_tien * vat_rate, 2)
        thanh_tien = round(tong_tien + vat - giam_gia, 2)
        tien_thoi  = round(so_tien_vao - thanh_tien, 2) if phuong_thuc == "TIENMAT" else 0

        # UC02 TT02: tiền mặt không đủ
        if phuong_thuc == "TIENMAT" and so_tien_vao < thanh_tien:
            return jsonify({
                "success": False,
                "message": f"Số tiền khách đưa ({so_tien_vao:,.0f}đ) không đủ thanh toán ({thanh_tien:,.0f}đ)"
            }), 400

        now = datetime.datetime.now()

        # 1. Ghi THANHTOAN
        cursor.execute(
            """
            INSERT INTO THANHTOAN
                (MaDon, MaKM, PhuongThuc, SoTienVao, TienThoi, VAT, NgayThanhToan)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (ma_don, ma_km, phuong_thuc, so_tien_vao, tien_thoi, vat, now)
        )

        # 2. Cập nhật DONHANG
        cursor.execute(
            """
            UPDATE DONHANG
            SET TrangThai = 'DATHANHTOAN',
                GiamGia   = %s,
                ThanhTien = %s
            WHERE MaDon = %s
            """,
            (giam_gia, thanh_tien, ma_don)
        )

        # 3. Giải phóng bàn
        cursor.execute(
            "UPDATE BAN SET TrangThai = 'TRONG' WHERE MaBan = %s",
            (order["MaBan"],)
        )

        # 4. Trừ tồn kho thực tế theo công thức
        cursor.execute(
            """
            SELECT CTDH.MaMon, CTDH.SoLuong,
                   CT.MaNL, CT.SoLuongSuDung
            FROM CHITIETDONHANG CTDH
            JOIN CONGTHUC CT ON CTDH.MaMon = CT.MaMon
            WHERE CTDH.MaDon = %s
            """,
            (ma_don,)
        )
        recipe_rows = cursor.fetchall()

        for row in recipe_rows:
            tru_thuc = float(row["SoLuongSuDung"]) * int(row["SoLuong"])
            cursor.execute(
                """
                UPDATE NGUYENLIEU
                SET SoLuongTon    = SoLuongTon    - %s,
                    SoLuongTruTam = GREATEST(SoLuongTruTam - %s, 0)
                WHERE MaNL = %s
                """,
                (tru_thuc, tru_thuc, row["MaNL"])
            )

        # 5. Đánh dấu voucher đã dùng
        if ma_km:
            cursor.execute(
                "UPDATE KHUYENMAI SET TrangThai = 'DADUNG' WHERE MaKM = %s",
                (ma_km,)
            )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Thanh toán thành công",
            "MaDon": ma_don,
            "TongTien": tong_tien,
            "GiamGia": giam_gia,
            "VAT": vat,
            "ThanhTien": thanh_tien,
            "TienThoi": tien_thoi,
            "NgayThanhToan": now.strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# XEM HÓA ĐƠN SAU THANH TOÁN (UC02.2)
# =========================
@payment_bp.route("/invoice/<int:ma_don>", methods=["GET"])
def get_invoice(ma_don):
    """UC02.2 – Lấy toàn bộ thông tin hóa đơn để hiển thị/in."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                DH.MaDon,
                DH.NgayTao,
                DH.TongTien,
                DH.GiamGia,
                DH.ThanhTien,
                B.TenBan,
                NV.HoTen           AS TenNhanVien,
                TT.PhuongThuc,
                TT.SoTienVao,
                TT.TienThoi,
                TT.VAT,
                TT.NgayThanhToan,
                KM.MaCode          AS MaVoucher
            FROM DONHANG DH
            JOIN BAN B            ON DH.MaBan = B.MaBan
            LEFT JOIN NHANVIEN NV ON DH.MaNV  = NV.MaNV
            LEFT JOIN THANHTOAN TT ON TT.MaDon = DH.MaDon
            LEFT JOIN KHUYENMAI KM ON TT.MaKM  = KM.MaKM
            WHERE DH.MaDon = %s
              AND DH.TrangThai = 'DATHANHTOAN'
            """,
            (ma_don,)
        )
        order = cursor.fetchone()

        if not order:
            return jsonify({
                "success": False,
                "message": "Không tìm thấy hóa đơn hoặc đơn chưa thanh toán"
            }), 404

        cursor.execute(
            """
            SELECT CTDH.MaCTDH, CTDH.MaMon, CTDH.SoLuong,
                   CTDH.DonGia, CTDH.GhiChu,
                   MON.TenMon
            FROM CHITIETDONHANG CTDH
            JOIN MON ON CTDH.MaMon = MON.MaMon
            WHERE CTDH.MaDon = %s
            """,
            (ma_don,)
        )
        items = cursor.fetchall()

        # Serialize datetime
        for key in ("NgayTao", "NgayThanhToan"):
            if order.get(key) and hasattr(order[key], "strftime"):
                order[key] = order[key].strftime("%Y-%m-%d %H:%M:%S")

        order["ChiTiet"] = items
        return jsonify({"success": True, "data": order})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ====================================================
# IN HÓA ĐƠN CHO KHÁCH KHỔ GIẤY K80 (BỔ SUNG CHO UC02.2)
# ====================================================
@payment_bp.route("/invoice/print/<int:ma_don>", methods=["GET"])
def print_customer_invoice(ma_don):
    """Tạo giao diện HTML hóa đơn bán lẻ K80 để trình duyệt tự động gọi lệnh in"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Lấy thông tin chung của hóa đơn
        cursor.execute(
            """
            SELECT
                DH.MaDon, DH.NgayTao, DH.TongTien, DH.GiamGia, DH.ThanhTien,
                B.TenBan, NV.HoTen AS TenNhanVien,
                TT.PhuongThuc, TT.SoTienVao, TT.TienThoi, TT.VAT, TT.NgayThanhToan,
                KM.MaCode AS MaVoucher
            FROM DONHANG DH
            JOIN BAN B            ON DH.MaBan = B.MaBan
            LEFT JOIN NHANVIEN NV ON DH.MaNV  = NV.MaNV
            LEFT JOIN THANHTOAN TT ON TT.MaDon = DH.MaDon
            LEFT JOIN KHUYENMAI KM ON TT.MaKM  = KM.MaKM
            WHERE DH.MaDon = %s AND DH.TrangThai = 'DATHANHTOAN'
            """,
            (ma_don,)
        )
        order = cursor.fetchone()

        if not order:
            return "Không tìm thấy thông tin hóa đơn hợp lệ để in.", 404

        # Lấy chi tiết các món trong đơn
        cursor.execute(
            """
            SELECT CTDH.SoLuong, CTDH.DonGia, MON.TenMon
            FROM CHITIETDONHANG CTDH
            JOIN MON ON CTDH.MaMon = MON.MaMon
            WHERE CTDH.MaDon = %s
            """,
            (ma_don,)
        )
        items = cursor.fetchall()

        ngay_tt = order["NgayThanhToan"].strftime("%d/%m/%Y %H:%M:%S") if order.get("NgayThanhToan") else ""

        items_html = ""
        for item in items:
            thanh_tien_mon = float(item['SoLuong']) * float(item['DonGia'])
            items_html += f"""
            <tr>
                <td>{item['TenMon']}</td>
                <td style="text-align: center;">{item['SoLuong']}</td>
                <td style="text-align: right;">{float(item['DonGia']):,.0f}</td>
                <td style="text-align: right;">{thanh_tien_mon:,.0f}</td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>In Hóa Đơn #{order['MaDon']}</title>
<style>
  body {{ font-family: 'Courier New', Courier, monospace, Arial; font-size: 12px; width: 80mm; margin: 0 auto; padding: 5px; color: #000; }}
  .text-center {{ text-align: center; }}
  .text-right {{ text-align: right; }}
  h2 {{ margin: 5px 0; font-size: 16px; text-transform: uppercase; }}
  .info-table, .items-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  .items-table th, .items-table td {{ border-bottom: 1px dashed #000; padding: 4px 0; font-size: 11px; }}
  .total-section {{ margin-top: 10px; font-weight: bold; font-size: 12px; line-height: 1.6; }}
  .footer {{ margin-top: 15px; font-style: italic; font-size: 11px; }}
  @media print {{
    body {{ width: 100%; }}
    @page {{ margin: 0; }}
  }}
</style>
</head>
<body>
<div class="text-center">
    <h2>☕ COFFEE MANAGEMENT SYSTEM</h2>
    <p>Địa chỉ: 123 Đường Số 1, TP. HCM<br>SĐT: 0123.456.789</p>
    <hr style="border-top: 1px dashed #000;">
    <h3>HÓA ĐƠN THANH TOÁN</h3>
</div>

<table class="info-table">
    <tr><td>Mã HĐ: <strong>{order['MaDon']}</strong></td><td class="text-right">Bàn: {order['TenBan']}</td></tr>
    <tr><td colspan="2">Ngày: {ngay_tt}</td></tr>
    <tr><td colspan="2">Thu ngân: {order['TenNhanVien'] or 'Hệ thống'}</td></tr>
</table>

<table class="items-table">
    <thead>
        <tr>
            <th style="text-align: left;">Tên món</th>
            <th style="text-align: center;">SL</th>
            <th style="text-align: right;">Đơn giá</th>
            <th style="text-align: right;">T.Tiền</th>
        </tr>
    </thead>
    <tbody>
        {items_html}
    </tbody>
</table>

<div class="total-section">
    <table style="width: 100%;">
        <tr><td>Tổng cộng tiền món:</td><td class="text-right">{float(order['TongTien']):,.0f}đ</td></tr>
        <tr><td>Thuế VAT ({float(order.get('VAT', 0.1))*100 if order.get('VAT') else 10}%):</td><td class="text-right">{float(order['VAT'] or 0):,.0f}đ</td></tr>
        {f"<tr><td>Giảm giá ({order['MaVoucher']}):</td><td class='text-right'>-{float(order['GiamGia']):,.0f}đ</td></tr>" if order['GiamGia'] > 0 else ""}
        <tr style="font-size: 14px;"><td><strong>KHÁCH PHẢI TRẢ:</strong></td><td class="text-right"><strong>{float(order['ThanhTien']):,.0f}đ</strong></td></tr>
        <tr style="font-weight: normal; font-size: 11px;"><td>Hình thức: {order['PhuongThuc']}</td><td class="text-right">Khách đưa: {float(order['SoTienVao']):,.0f}đ</td></tr>
        {f"<tr style='font-weight: normal; font-size: 11px;'><td>Tiền thối lại:</td><td class='text-right'>{float(order['TienThoi']):,.0f}đ</td></tr>" if order['PhuongThuc'] == "TIENMAT" else ""}
    </table>
</div>

<div class="text-center footer">
    <p>Cảm ơn Quý khách - Hẹn gặp lại!</p>
</div>

<script>
    window.onload = function() {{
        window.print();
    }}
</script>
</body>
</html>"""
        response = make_response(html)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    except Exception as e:
        return f"Lỗi in hóa đơn: {str(e)}", 500
    finally:
        cursor.close()
        conn.close()
