from flask import Blueprint, request, jsonify, render_template, make_response
from app.database.db import get_connection
import datetime
import csv
import io

report_bp = Blueprint(
    "report",
    __name__,
    url_prefix="/report"
)


# =========================
# GIAO DIỆN
# =========================
from flask import Blueprint, render_template

report_bp = Blueprint("report", __name__)

@report_bp.route("/")
def home():
    return render_template("report.html")

# =========================
# TỔNG QUAN DOANH THU (UC06 – Bước 1 & 2)
# =========================
@report_bp.route("/revenue", methods=["GET"])
def get_revenue():
    """
    UC06 – Dashboard chính:
      - Tổng doanh thu, tổng đơn, giá trị TB, tổng giảm giá, tổng món bán ra
      - Doanh thu theo ngày (cho biểu đồ)
      - Top 10 món bán chạy (UC06 – Bước 3)
      - Phân bổ phương thức thanh toán
    Query params: tu_ngay (YYYY-MM-DD), den_ngay (YYYY-MM-DD)
    """
    tu_ngay  = request.args.get("tu_ngay")
    den_ngay = request.args.get("den_ngay")

    if not tu_ngay or not den_ngay:
        return jsonify({
            "success": False,
            "message": "Vui lòng chọn khoảng thời gian (tu_ngay, den_ngay)"
        }), 400

    # UC06 TT02: khoảng thời gian không hợp lệ
    if tu_ngay > den_ngay:
        return jsonify({
            "success": False,
            "message": "Khoảng thời gian không hợp lệ: ngày bắt đầu phải ≤ ngày kết thúc"
        }), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ---- Tóm tắt tổng quan ----
        cursor.execute(
            """
            SELECT
                COUNT(DH.MaDon)                        AS TongDon,
                COALESCE(SUM(DH.ThanhTien), 0)         AS TongDoanhThu,
                COALESCE(AVG(DH.ThanhTien), 0)         AS GiaTriTBDon,
                COALESCE(SUM(DH.GiamGia), 0)           AS TongGiamGia,
                COALESCE(SUM(CTDH_agg.TongMonBan), 0)  AS TongMonBan
            FROM DONHANG DH
            LEFT JOIN (
                SELECT MaDon, SUM(SoLuong) AS TongMonBan
                FROM CHITIETDONHANG
                GROUP BY MaDon
            ) CTDH_agg ON CTDH_agg.MaDon = DH.MaDon
            WHERE DH.TrangThai = 'DATHANHTOAN'
              AND DATE(DH.NgayTao) BETWEEN %s AND %s
            """,
            (tu_ngay, den_ngay)
        )
        summary = cursor.fetchone()

        # UC06 TT01: không có dữ liệu
        if not summary or summary["TongDon"] == 0:
            return jsonify({
                "success": True,
                "empty": True,
                "message": "Chưa có dữ liệu trong khoảng thời gian được chọn",
                "TomTat": {"TongDon": 0, "TongDoanhThu": 0,
                           "GiaTriTBDon": 0, "TongGiamGia": 0, "TongMonBan": 0},
                "TheoNgay": [],
                "TopMon": [],
                "PhuongThucTT": []
            })

        # ---- Doanh thu theo ngày (dùng cho biểu đồ line) ----
        cursor.execute(
            """
            SELECT
                DATE(DH.NgayTao)       AS Ngay,
                COUNT(DH.MaDon)        AS SoDon,
                SUM(DH.ThanhTien)      AS DoanhThu
            FROM DONHANG DH
            WHERE DH.TrangThai = 'DATHANHTOAN'
              AND DATE(DH.NgayTao) BETWEEN %s AND %s
            GROUP BY DATE(DH.NgayTao)
            ORDER BY Ngay
            """,
            (tu_ngay, den_ngay)
        )
        by_day = cursor.fetchall()

        for row in by_day:
            if hasattr(row.get("Ngay"), "strftime"):
                row["Ngay"] = row["Ngay"].strftime("%Y-%m-%d")

        # ---- Top 10 món bán chạy (UC06 – Bước 3) ----
        cursor.execute(
            """
            SELECT
                MON.MaMon,
                MON.TenMon,
                DM.TenDanhMuc,
                SUM(CTDH.SoLuong)                  AS TongSL,
                SUM(CTDH.SoLuong * CTDH.DonGia)   AS DoanhThu
            FROM CHITIETDONHANG CTDH
            JOIN DONHANG DH  ON CTDH.MaDon = DH.MaDon
            JOIN MON         ON CTDH.MaMon = MON.MaMon
            LEFT JOIN DANHMUC DM ON MON.MaDM = DM.MaDM
            WHERE DH.TrangThai = 'DATHANHTOAN'
              AND DATE(DH.NgayTao) BETWEEN %s AND %s
            GROUP BY MON.MaMon, MON.TenMon, DM.TenDanhMuc
            ORDER BY TongSL DESC
            LIMIT 10
            """,
            (tu_ngay, den_ngay)
        )
        top_items = cursor.fetchall()

        # ---- Phân bổ phương thức thanh toán ----
        cursor.execute(
            """
            SELECT
                TT.PhuongThuc,
                COUNT(*)              AS SoDon,
                SUM(DH.ThanhTien)     AS TongTien
            FROM THANHTOAN TT
            JOIN DONHANG DH ON TT.MaDon = DH.MaDon
            WHERE DH.TrangThai = 'DATHANHTOAN'
              AND DATE(DH.NgayTao) BETWEEN %s AND %s
            GROUP BY TT.PhuongThuc
            """,
            (tu_ngay, den_ngay)
        )
        by_payment = cursor.fetchall()

        # Serialize Decimal sang float
        def to_float(d):
            return {k: float(v) if hasattr(v, '__float__') and not isinstance(v, (int, str, type(None))) else v
                    for k, v in d.items()}

        summary     = to_float(summary)
        top_items   = [to_float(r) for r in top_items]
        by_payment  = [to_float(r) for r in by_payment]
        by_day      = [to_float(r) for r in by_day]

        return jsonify({
            "success": True,
            "TomTat": summary,
            "TheoNgay": by_day,
            "TopMon": top_items,
            "PhuongThucTT": by_payment
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# LỊCH SỬ CHỈNH SỬA ĐƠN HÀNG (UC06 – Bước 4)
# =========================
@report_bp.route("/history", methods=["GET"])
def get_edit_history():
    """
    UC06 – Bước 4:
      Trả về lịch sử chỉnh sửa đơn và danh sách đơn bất thường
      (số lần chỉnh sửa > 5 trong kỳ báo cáo – UC06 TT03).
    """
    tu_ngay  = request.args.get("tu_ngay")
    den_ngay = request.args.get("den_ngay")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        params  = []
        where   = "WHERE 1=1"

        if tu_ngay and den_ngay:
            where  += " AND DATE(LS.ThoiGian) BETWEEN %s AND %s"
            params += [tu_ngay, den_ngay]

        cursor.execute(
            f"""
            SELECT
                LS.MaLS,
                LS.MaDon,
                LS.MaNV,
                LS.HanhDong,
                LS.NoiDung,
                LS.ThoiGian,
                DH.MaBan,
                NV.HoTen AS TenNhanVien
            FROM LICHSUDONHANG LS
            JOIN DONHANG DH   ON LS.MaDon = DH.MaDon
            LEFT JOIN NHANVIEN NV ON LS.MaNV = NV.MaNV
            {where}
            ORDER BY LS.ThoiGian DESC
            LIMIT 200
            """,
            params
        )
        history = cursor.fetchall()

        for row in history:
            if row.get("ThoiGian") and hasattr(row["ThoiGian"], "strftime"):
                row["ThoiGian"] = row["ThoiGian"].strftime("%Y-%m-%d %H:%M:%S")

        # UC06 TT03: đơn bất thường – chỉnh sửa > 5 lần
        cursor.execute(
            f"""
            SELECT
                LS.MaDon,
                NV.HoTen       AS TenNhanVien,
                COUNT(*)       AS SoLanChinhSua,
                MIN(LS.ThoiGian) AS LanDau,
                MAX(LS.ThoiGian) AS LanCuoi
            FROM LICHSUDONHANG LS
            LEFT JOIN NHANVIEN NV ON LS.MaNV = NV.MaNV
            {where}
            GROUP BY LS.MaDon, NV.HoTen
            HAVING SoLanChinhSua > 5
            ORDER BY SoLanChinhSua DESC
            """,
            params
        )
        anomalies = cursor.fetchall()

        for row in anomalies:
            for k in ("LanDau", "LanCuoi"):
                if row.get(k) and hasattr(row[k], "strftime"):
                    row[k] = row[k].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({
            "success": True,
            "LichSu": history,
            "BatThuong": anomalies
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# XUẤT EXCEL / CSV (UC06.1)
# =========================
@report_bp.route("/export/excel", methods=["GET"])
def export_excel():
    """
    UC06.1 – Xuất báo cáo dạng CSV (mở được bằng Excel).
    Query params: tu_ngay, den_ngay
    """
    tu_ngay  = request.args.get("tu_ngay")
    den_ngay = request.args.get("den_ngay")

    if not tu_ngay or not den_ngay:
        return jsonify({"success": False, "message": "Thiếu khoảng thời gian"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Thông tin đơn hàng
        cursor.execute(
            """
            SELECT
                DH.MaDon          AS 'Mã đơn',
                DH.NgayTao        AS 'Ngày tạo',
                B.TenBan          AS 'Bàn',
                NV.HoTen          AS 'Nhân viên',
                DH.TongTien       AS 'Tổng tiền',
                DH.GiamGia        AS 'Giảm giá',
                TT.VAT            AS 'VAT',
                DH.ThanhTien      AS 'Thanh toán',
                TT.PhuongThuc     AS 'Phương thức TT',
                KM.MaCode         AS 'Mã voucher'
            FROM DONHANG DH
            JOIN BAN B            ON DH.MaBan = B.MaBan
            LEFT JOIN NHANVIEN NV ON DH.MaNV  = NV.MaNV
            LEFT JOIN THANHTOAN TT ON TT.MaDon = DH.MaDon
            LEFT JOIN KHUYENMAI KM ON TT.MaKM  = KM.MaKM
            WHERE DH.TrangThai = 'DATHANHTOAN'
              AND DATE(DH.NgayTao) BETWEEN %s AND %s
            ORDER BY DH.NgayTao
            """,
            (tu_ngay, den_ngay)
        )
        rows = cursor.fetchall()

        if not rows:
            return jsonify({
                "success": False,
                "message": "Không có dữ liệu để xuất"
            }), 404

        output = io.StringIO()
        # BOM cho Excel đọc UTF-8 đúng tiếng Việt
        output.write("\ufeff")

        writer = csv.DictWriter(
            output,
            fieldnames=list(rows[0].keys()),
            extrasaction="ignore"
        )
        writer.writeheader()

        for row in rows:
            serialized = {}
            for k, v in row.items():
                if hasattr(v, "strftime"):
                    serialized[k] = v.strftime("%Y-%m-%d %H:%M:%S")
                elif v is None:
                    serialized[k] = ""
                else:
                    serialized[k] = v
            writer.writerow(serialized)

        filename = f"BaoCaoDoanhThu_{tu_ngay}_{den_ngay}.csv"
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        return response

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ====================================================
# XUẤT BÁO CÁO DOANH THU CHUẨN A4 DỌC (UC06.1)
# ====================================================
@report_bp.route("/export/pdf", methods=["GET"])
def export_pdf():
    """Tạo trang báo cáo doanh thu đẹp mắt để in/xuất PDF chuẩn doanh nghiệp"""
    tu_ngay  = request.args.get("tu_ngay")
    den_ngay = request.args.get("den_ngay")

    if not tu_ngay or not den_ngay:
        return "Thiếu khoảng thời gian báo cáo (tu_ngay, den_ngay)", 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                DH.MaDon, DH.NgayTao, B.TenBan, NV.HoTen AS TenNhanVien,
                DH.TongTien, DH.GiamGia, TT.VAT, DH.ThanhTien,
                TT.PhuongThuc, KM.MaCode AS MaVoucher
            FROM DONHANG DH
            JOIN BAN B            ON DH.MaBan = B.MaBan
            LEFT JOIN NHANVIEN NV ON DH.MaNV  = NV.MaNV
            LEFT JOIN THANHTOAN TT ON TT.MaDon = DH.MaDon
            LEFT JOIN KHUYENMAI KM ON TT.MaKM  = KM.MaKM
            WHERE DH.TrangThai = 'DATHANHTOAN'
              AND DATE(DH.NgayTao) BETWEEN %s AND %s
            ORDER BY DH.NgayTao
            """,
            (tu_ngay, den_ngay)
        )
        rows = cursor.fetchall()

        # Tính các số liệu tổng quan
        total_revenue = sum(float(r["ThanhTien"] or 0) for r in rows)
        total_discount = sum(float(r["GiamGia"] or 0) for r in rows)
        total_vat = sum(float(r["VAT"] or 0) for r in rows)
        total_orders = len(rows)

        format_tu_ngay = datetime.datetime.strptime(tu_ngay, "%Y-%m-%d").strftime("%d/%m/%Y")
        format_den_ngay = datetime.datetime.strptime(den_ngay, "%Y-%m-%d").strftime("%d/%m/%Y")
        ngay_lap_bc = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        rows_html = ""
        for i, r in enumerate(rows, 1):
            ngay_don = r["NgayTao"].strftime("%d/%m/%Y %H:%M") if hasattr(r["NgayTao"], "strftime") else r["NgayTao"]
            rows_html += f"""
            <tr>
                <td style="text-align: center;">{i}</td>
                <td style="text-align: center;"><strong>{r['MaDon']}</strong></td>
                <td>{ngay_don}</td>
                <td>{r['TenBan']}</td>
                <td>{r['TenNhanVien'] or 'Hệ thống'}</td>
                <td style="text-align: right;">{float(r['TongTien'] or 0):,.0f}đ</td>
                <td style="text-align: right; color: red;">-{float(r['GiamGia'] or 0):,.0f}đ</td>
                <td style="text-align: right;">{float(r['VAT'] or 0):,.0f}đ</td>
                <td style="text-align: right; font-weight: bold;">{float(r['ThanhTien'] or 0):,.0f}đ</td>
                <td style="text-align: center;"><span class="badge">{r['PhuongThuc'] or ''}</span></td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Báo cáo Doanh thu ({tu_ngay} - {den_ngay})</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #333; line-height: 1.4; margin: 0; padding: 20mm 15mm; }}
  .header-table {{ width: 100%; border: none; margin-bottom: 20px; }}
  .company-title {{ font-size: 14px; text-transform: uppercase; font-weight: bold; }}
  .report-title {{ text-align: center; color: #2c3e50; margin: 25px 0 10px 0; font-size: 22px; font-weight: bold; text-transform: uppercase; }}
  .sub-title {{ text-align: center; font-style: italic; color: #555; margin-bottom: 30px; font-size: 14px; }}
  
  .summary-container {{ display: flex; justify-content: space-between; margin-bottom: 25px; gap: 15px; }}
  .summary-card {{ flex: 1; background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; text-align: center; }}
  .summary-card .card-title {{ font-size: 11px; text-transform: uppercase; color: #718096; margin-bottom: 5px; font-weight: 600; }}
  .summary-card .card-value {{ font-size: 16px; font-weight: bold; color: #1a202c; }}
  .summary-card.highlight {{ background: #ebf8ff; border-color: #bee3f8; }}
  .summary-card.highlight .card-value {{ color: #2b6cb0; }}

  .data-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
  .data-table th, .data-table td {{ border: 1px solid #cbd5e0; padding: 8px 10px; text-align: left; }}
  .data-table th {{ background: #2d3748; color: #fff; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
  .data-table tr:nth-child(even) {{ background: #f7fafc; }}
  
  .badge {{ background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 500; }}
  
  .signature-section {{ width: 100%; margin-top: 50px; border: none; page-break-inside: avoid; }}
  .signature-title {{ text-align: center; font-weight: bold; font-size: 13px; padding-bottom: 60px; }}
  
  @media print {{
    body {{ padding: 0; }}
    @page {{ size: A4; margin: 15mm; }}
  }}
</style>
</head>
<body>

<table class="header-table">
    <tr>
        <td class="company-title">☕ COFFEE MANAGEMENT SYSTEM<br><span style="font-size:11px; font-weight:normal; color:#666;">Hệ thống quản lý chuỗi quán Cafe</span></td>
        <td style="text-align: right; font-style: italic; color: #718096;">Ngày lập: {ngay_lap_bc}</td>
    </tr>
</table>

<div class="report-title">Báo cáo Doanh thu Bán hàng</div>
<div class="sub-title">Từ ngày {format_tu_ngay} đến ngày {format_den_ngay}</div>

<div class="summary-container">
    <div class="summary-card">
        <div class="card-title">Tổng số đơn hàng</div>
        <div class="card-value">{total_orders} đơn</div>
    </div>
    <div class="summary-card">
        <div class="card-title">Tổng giảm giá</div>
        <div class="card-value" style="color:#e53e3e;">-{total_discount:,.0f}đ</div>
    </div>
    <div class="summary-card">
        <div class="card-title">Tổng tiền thuế VAT</div>
        <div class="card-value">{total_vat:,.0f}đ</div>
    </div>
    <div class="summary-card highlight">
        <div class="card-title">Doanh thu thực tế</div>
        <div class="card-value">{total_revenue:,.0f}đ</div>
    </div>
</div>

<table class="data-table">
  <thead>
    <tr>
      <th style="width: 4%;">STT</th>
      <th style="width: 8%;">Mã Đơn</th>
      <th style="width: 15%;">Thời Gian Đặt</th>
      <th style="width: 8%;">Bàn</th>
      <th style="width: 15%;">Nhân Viên Lập</th>
      <th>Tiền Món</th>
      <th>Giảm Giá</th>
      <th>Thuế VAT</th>
      <th>Thực Thu</th>
      <th style="width: 10%;">Hình Thức</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>

<table class="signature-section">
    <tr>
        <td style="width: 50%; text-align: center;">
            <span style="color:#718096; font-style:italic;">Người lập báo cáo</span><br>
            <div class="signature-title">(Ký và ghi rõ họ tên)</div>
        </td>
        <td style="width: 50%; text-align: center;">
            <span style="color:#718096; font-style:italic;">Đại diện quản lý cửa hàng</span><br>
            <div class="signature-title">(Xác nhận và đóng dấu)</div>
        </td>
    </tr>
</table>

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
        return f"Lỗi xuất báo cáo: {str(e)}", 500
    finally:
        cursor.close()
        conn.close()
@report_bp.route("/")
def home():

    role = request.cookies.get("role")

    if role != "ADMIN":
        return "Không có quyền truy cập báo cáo", 403

    return render_template("report.html")