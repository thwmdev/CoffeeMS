/* ===================================================
   payment.js  –  UC02: Thanh toán & In hóa đơn
   =================================================== */

// ── State ─────────────────────────────────────────
let lastPaidOrderId = null; // Lưu lại mã hóa đơn vừa thanh toán thành công
let currentOrder   = null;   // đơn hàng đang xử lý
let appliedVoucher = null;   // { MaKM, GiamGia, ThanhTien }
let phuongThuc     = "TIENMAT";
const VAT_RATE     = 0.1;

// ── Khởi động ─────────────────────────────────────
loadTables();


// =========================
// TẢI DANH SÁCH BÀN
// =========================
function loadTables() {
    fetch("/payment/tables")
        .then(res => res.json())
        .then(res => {
            if (!res.success) {
                console.error("Lỗi tải danh sách bàn:", res.message);
                return;
            }
            renderTableGrid(res.data);
        })
        .catch(err => console.error("Lỗi:", err));
}


function renderTableGrid(tables) {
    let html = "";

    tables.forEach(t => {
        const hasPending = t.MaDon && t.TrangThai !== "DATHANHTOAN";
        const statusLabel = hasPending ? "Có đơn" : (t.TrangThai || "Trống");
        const statusClass = hasPending ? "status-COKHACH" : "status-TRONG";

        html += `
        <div class="table-card" onclick="loadOrderByTable(${t.MaBan}, this)">
            <div class="t-name">${t.TenBan}</div>
            <div class="t-status ${statusClass}">${statusLabel}</div>
            ${t.TongTien ? `<div style="font-size:13px;color:#6b7280;margin-top:6px;">${formatMoney(t.TongTien)}</div>` : ""}
        </div>`;
    });

    document.getElementById("tableGrid").innerHTML = html;
}


// =========================
// TẢI ĐƠN THEO BÀN
// =========================
function loadOrderByTable(maBan, cardEl) {
    // Highlight bàn được chọn
    document.querySelectorAll(".table-card").forEach(c => c.classList.remove("selected"));
    cardEl.classList.add("selected");

    fetch(`/payment/order/table/${maBan}`)
        .then(async res => {
            const result = await res.json();
            if (!res.ok) {
                alert(result.message || "Bàn này không có đơn hàng đang chờ thanh toán");
                return;
            }
            displayOrder(result.data);
        })
        .catch(err => {
            console.error(err);
            alert("Bàn này không có đơn hàng đang chờ thanh toán.");
        });
}


// =========================
// TẢI ĐƠN THEO MÃ ĐƠN
// =========================
function loadOrderById() {
    const maDon = document.getElementById("inputMaDon").value.trim();
    if (!maDon) { alert("Vui lòng nhập mã đơn hàng"); return; }

    fetch(`/payment/order/${maDon}`)
        .then(async res => {
            const result = await res.json();
            if (!res.ok) {
                alert(result.message || "Không tìm thấy đơn hàng");
                return;
            }
            displayOrder(result.data);
        })
        .catch(err => { console.error(err); alert("Lỗi tải đơn hàng"); });
}


// =========================
// HIỂN THỊ CHI TIẾT ĐƠN
// =========================
function displayOrder(order) {
    currentOrder  = order;
    appliedVoucher = null;

    document.getElementById("tenBan").innerText     = order.TenBan || "–";
    document.getElementById("maDonLabel").innerText = `#${order.MaDon}`;

    // Render danh sách món
    let itemsHtml = "";
    order.ChiTiet.forEach(item => {
        const thanhTien = item.SoLuong * item.DonGia;
        itemsHtml += `
        <tr>
            <td>${item.TenMon}</td>
            <td>${formatMoney(item.DonGia)}</td>
            <td>${item.SoLuong}</td>
            <td><small class="text-muted">${item.GhiChu || ""}</small></td>
            <td><strong>${formatMoney(thanhTien)}</strong></td>
        </tr>`;
    });
    document.getElementById("orderItems").innerHTML = itemsHtml;

    // Reset voucher UI
    document.getElementById("voucherCode").value = "";
    document.getElementById("voucherMsg").innerHTML  = "";

    updatePriceSummary();

    document.getElementById("orderBox").style.display = "block";
    document.getElementById("invoiceBox").classList.remove("show");
    document.getElementById("soTienVao").value = "";
    document.getElementById("tienThoi").innerText = "–";

    // Scroll đến form
    document.getElementById("orderBox").scrollIntoView({ behavior: "smooth" });
}


// =========================
// TÍNH & HIỂN THỊ TỔNG TIỀN
// =========================
function updatePriceSummary() {
    if (!currentOrder) return;

    const tong    = parseFloat(currentOrder.TongTien) || 0;
    const giam    = appliedVoucher ? appliedVoucher.GiamGia : 0;
    const vat     = tong * VAT_RATE;
    const thanh   = tong + vat - giam;

    document.getElementById("tongTien").innerText      = formatMoney(tong);
    document.getElementById("vatDisplay").innerText    = formatMoney(vat);
    document.getElementById("giamGiaDisplay").innerText = `–${formatMoney(giam)}`;
    document.getElementById("thanhTien").innerText     = formatMoney(thanh);

    calcChange();
}


// =========================
// TÍNH TIỀN THỐI
// =========================
function calcChange() {
    if (phuongThuc !== "TIENMAT" || !currentOrder) return;

    const tong    = parseFloat(currentOrder.TongTien) || 0;
    const giam    = appliedVoucher ? appliedVoucher.GiamGia : 0;
    const vat     = tong * VAT_RATE;
    const thanh   = tong + vat - giam;
    const soTien  = parseFloat(document.getElementById("soTienVao").value) || 0;
    const thoi    = soTien - thanh;

    document.getElementById("tienThoi").innerText = thoi >= 0
        ? formatMoney(thoi)
        : `⚠️ Thiếu ${formatMoney(Math.abs(thoi))}`;
    document.getElementById("tienThoi").style.color = thoi >= 0 ? "#ff9800" : "#dc2626";
}


// =========================
// ÁP DỤNG VOUCHER (UC02.1)
// =========================
function applyVoucher() {
    const code = document.getElementById("voucherCode").value.trim();
    if (!code) {
        document.getElementById("voucherMsg").innerHTML =
            `<span style="color:#dc2626;">Vui lòng nhập mã giảm giá</span>`;
        return;
    }

    if (!currentOrder) {
        alert("Vui lòng chọn đơn hàng trước");
        return;
    }

    const tong = parseFloat(currentOrder.TongTien) || 0;

    fetch("/payment/apply-voucher", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ MaCode: code, TongTien: tong })
    })
    .then(async res => {
        const result = await res.json();

        if (!res.ok) {
            document.getElementById("voucherMsg").innerHTML =
                `<span style="color:#dc2626;">❌ ${result.message}</span>`;
            appliedVoucher = null;
        } else {
            appliedVoucher = result;
            document.getElementById("voucherMsg").innerHTML =
                `<span style="color:#16a34a;">✅ ${result.message}</span>`;
        }
        updatePriceSummary();
    })
    .catch(err => {
        console.error(err);
        document.getElementById("voucherMsg").innerHTML =
            `<span style="color:#dc2626;">Lỗi kết nối</span>`;
    });
}


function removeVoucher() {
    appliedVoucher = null;
    document.getElementById("voucherCode").value = "";
    document.getElementById("voucherMsg").innerHTML = "";
    updatePriceSummary();
}


// =========================
// CHỌN PHƯƠNG THỨC THANH TOÁN
// =========================
function setPT(method, btn) {
    phuongThuc = method;

    document.querySelectorAll(".pt-btn").forEach(b => {
        b.classList.remove("btn-warning");
        b.classList.add("btn-outline-dark");
    });
    btn.classList.remove("btn-outline-dark");
    btn.classList.add("btn-warning");

    // Ẩn/hiện phần nhập tiền mặt
    document.getElementById("cashSection").style.display =
        method === "TIENMAT" ? "block" : "none";
}


// =========================
// HOÀN TẤT THANH TOÁN (UC02 – Bước 4)
// =========================
function checkout() {
    if (!currentOrder) { alert("Chưa chọn đơn hàng"); return; }

    const tong    = parseFloat(currentOrder.TongTien) || 0;
    const giam    = appliedVoucher ? appliedVoucher.GiamGia : 0;
    const vat     = tong * VAT_RATE;
    const thanh   = tong + vat - giam;
    const soTien  = parseFloat(document.getElementById("soTienVao").value) || 0;

    // UC02 TT02: tiền mặt không đủ
    if (phuongThuc === "TIENMAT" && soTien < thanh) {
        alert(`Số tiền khách đưa (${formatMoney(soTien)}) chưa đủ!\nCần thanh toán: ${formatMoney(thanh)}`);
        return;
    }

    if (!confirm(`Xác nhận thanh toán ${formatMoney(thanh)}?`)) return;

    const payload = {
        MaDon:      currentOrder.MaDon,
        PhuongThuc: phuongThuc,
        SoTienVao:  soTien,
        GiamGia:    giam,
        VATRate:    VAT_RATE,
        MaKM:       appliedVoucher ? appliedVoucher.MaKM : null
    };

    fetch("/payment/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(async res => {
        const result = await res.json();
        if (!res.ok) {
            alert("Lỗi thanh toán: " + result.message);
            return;
        }
        // Thanh toán thành công → hiển thị hóa đơn
        loadInvoice(currentOrder.MaDon, result);
        loadTables(); // cập nhật trạng thái bàn
    })
    .catch(err => {
        console.error(err);
        alert("Lỗi kết nối máy chủ");
    });
}


// =========================
// HIỂN THỊ HÓA ĐƠN (UC02.2)
// =========================
function loadInvoice(maDon, payResult) {
    fetch(`/payment/invoice/${maDon}`)
        .then(res => res.json())
        .then(res => {
            if (!res.success) { renderInvoice(payResult, null); return; }
            renderInvoice(payResult, res.data);
        })
        .catch(() => renderInvoice(payResult, null));
}


function renderInvoice(payResult, data) {
    lastPaidOrderId = payResult.MaDon; // Lưu ID để in
    document.getElementById("orderBox").style.display = "none";

    // Header info
    document.getElementById("invDate").innerText  =
        payResult.NgayThanhToan || new Date().toLocaleString("vi-VN");
    document.getElementById("invMaDon").innerText = payResult.MaDon;
    document.getElementById("invBan").innerText   =
        data ? (data.TenBan || "–") : currentOrder.TenBan || "–";
    document.getElementById("invNV").innerText    =
        data ? (data.TenNhanVien || "–") : "–";
    document.getElementById("invPT").innerText    = payResult.PhuongThuc || phuongThuc;

    const voucher = data ? data.MaVoucher : null;
    document.getElementById("invVoucher").innerHTML =
        voucher ? `Voucher: <strong>${voucher}</strong>` : "";

    // Danh sách món
    const items = data ? data.ChiTiet : (currentOrder ? currentOrder.ChiTiet : []);
    let rowsHtml = "";
    items.forEach(item => {
        const tt = item.SoLuong * item.DonGia;
        rowsHtml += `
        <tr>
            <td>${item.TenMon}${item.GhiChu ? `<br><small class="text-muted">${item.GhiChu}</small>` : ""}</td>
            <td style="text-align:right;">${formatMoney(item.DonGia)}</td>
            <td style="text-align:center;">${item.SoLuong}</td>
            <td style="text-align:right;">${formatMoney(tt)}</td>
        </tr>`;
    });
    document.getElementById("invItems").innerHTML = rowsHtml;

    // Tổng tiền
    document.getElementById("invTong").innerText = formatMoney(payResult.TongTien);
    document.getElementById("invGiam").innerText = `–${formatMoney(payResult.GiamGia)}`;
    document.getElementById("invVAT").innerText  = formatMoney(payResult.VAT);
    document.getElementById("invTT").innerText   = formatMoney(payResult.ThanhTien);

    if (payResult.TienThoi > 0) {
        document.getElementById("invThoi").style.display  = "flex";
        document.getElementById("invThoiVal").innerText   = formatMoney(payResult.TienThoi);
    }

    document.getElementById("invoiceBox").classList.add("show");
    document.getElementById("invoiceBox").scrollIntoView({ behavior: "smooth" });
}


function printInvoiceBill() {
    if (lastPaidOrderId) {
        window.open(`/payment/invoice/print/${lastPaidOrderId}`, "_blank");
    } else {
        alert("Không tìm thấy mã hóa đơn hợp lệ để tiến hành in!");
    }
}

// =========================
// RESET VỀ TRẠNG THÁI BAN ĐẦU
// =========================
function resetPayment() {
    currentOrder   = null;
    appliedVoucher = null;
    phuongThuc     = "TIENMAT";

    document.getElementById("orderBox").style.display = "none";
    document.getElementById("invoiceBox").classList.remove("show");
    document.getElementById("inputMaDon").value = "";
    document.querySelectorAll(".table-card").forEach(c => c.classList.remove("selected"));

    loadTables();
}

// =========================
// HELPER
// =========================
function formatMoney(n) {
    return Number(n || 0).toLocaleString("vi-VN") + "đ";
}