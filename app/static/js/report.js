/* ===================================================
   report.js  –  UC06: Báo cáo Doanh thu & Hiệu suất
   =================================================== */

// ── Chart instances (cần destroy trước khi re-render) ──
let chartRevenue  = null;
let chartPayment  = null;
let chartTopItems = null;

// ── Khởi động: đặt ngày mặc định là tháng này ────────
(function init() {
    const today = new Date();
    const y = today.getFullYear();
    const m = String(today.getMonth() + 1).padStart(2, "0");
    document.getElementById("tuNgay").value  = `${y}-${m}-01`;
    document.getElementById("denNgay").value = `${y}-${m}-${String(today.getDate()).padStart(2, "0")}`;
})();


// =========================
// SHORTCUT NGÀY
// =========================
function setQuickDate(preset) {
    const today = new Date();
    let from = new Date(today);
    let to   = new Date(today);

    if (preset === "today") {
        // giữ nguyên
    } else if (preset === "week") {
        from.setDate(today.getDate() - 6);
    } else if (preset === "month") {
        from = new Date(today.getFullYear(), today.getMonth(), 1);
    } else if (preset === "lastmonth") {
        from = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        to   = new Date(today.getFullYear(), today.getMonth(), 0);
    }

    document.getElementById("tuNgay").value  = formatDate(from);
    document.getElementById("denNgay").value = formatDate(to);

    loadReport();
}


// =========================
// TẢI BÁO CÁO (UC06 – Bước 1 & 2)
// =========================
function loadReport() {
    const tuNgay  = document.getElementById("tuNgay").value;
    const denNgay = document.getElementById("denNgay").value;

    if (!tuNgay || !denNgay) {
        alert("Vui lòng chọn khoảng thời gian");
        return;
    }

    // UC06 TT02
    if (tuNgay > denNgay) {
        alert("Khoảng thời gian không hợp lệ: ngày bắt đầu phải ≤ ngày kết thúc");
        return;
    }

    showLoading(true);

    // Gọi song song revenue + history
    Promise.all([
        fetch(`/report/revenue?tu_ngay=${tuNgay}&den_ngay=${denNgay}`).then(r => r.json()),
        fetch(`/report/history?tu_ngay=${tuNgay}&den_ngay=${denNgay}`).then(r => r.json())
    ])
    .then(([revRes, histRes]) => {
        showLoading(false);

        if (!revRes.success) {
            alert("Lỗi: " + revRes.message);
            return;
        }

        // UC06 TT01: không có dữ liệu
        if (revRes.empty) {
            document.getElementById("emptyState").style.display = "block";
            document.getElementById("dashboard").style.display  = "none";
            return;
        }

        document.getElementById("emptyState").style.display = "none";
        document.getElementById("dashboard").style.display  = "block";

        renderKPIs(revRes.TomTat);
        renderRevenueChart(revRes.TheoNgay);
        renderPaymentChart(revRes.PhuongThucTT);
        renderTopItems(revRes.TopMon);

        if (histRes.success) {
            renderHistory(histRes.LichSu);
            renderAnomalies(histRes.BatThuong);
        }
    })
    .catch(err => {
        showLoading(false);
        console.error(err);
        alert("Lỗi kết nối máy chủ");
    });
}


// =========================
// KPI CARDS (UC06 – Bước 2)
// =========================
function renderKPIs(data) {
    document.getElementById("kpiDoanhThu").innerText = formatMoney(data.TongDoanhThu);
    document.getElementById("kpiTongDon").innerText  = data.TongDon.toLocaleString("vi-VN");
    document.getElementById("kpiTBDon").innerText    = formatMoney(data.GiaTriTBDon);
    document.getElementById("kpiGiam").innerText     = formatMoney(data.TongGiamGia);
    document.getElementById("kpiMonBan").innerText   = Number(data.TongMonBan || 0).toLocaleString("vi-VN");
}


// =========================
// BIỂU ĐỒ DOANH THU THEO NGÀY
// =========================
function renderRevenueChart(byDay) {
    const labels = byDay.map(r => r.Ngay);
    const values = byDay.map(r => r.DoanhThu);

    if (chartRevenue) { chartRevenue.destroy(); }

    const ctx = document.getElementById("chartRevenue").getContext("2d");
    chartRevenue = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Doanh thu (đ)",
                data: values,
                borderColor: "#ff9800",
                backgroundColor: "rgba(255,152,0,0.12)",
                borderWidth: 2.5,
                pointRadius: 4,
                tension: 0.35,
                fill: true
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    ticks: {
                        callback: v => (v / 1000000).toFixed(1) + "tr"
                    }
                }
            }
        }
    });
}


// =========================
// BIỂU ĐỒ PHƯƠNG THỨC THANH TOÁN
// =========================
function renderPaymentChart(byPT) {
    const labels = byPT.map(r => r.PhuongThuc || "Khác");
    const values = byPT.map(r => r.TongTien);
    const COLORS = ["#ff9800", "#3b82f6", "#22c55e", "#a855f7", "#ef4444"];

    if (chartPayment) { chartPayment.destroy(); }

    const ctx = document.getElementById("chartPayment").getContext("2d");
    chartPayment = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: COLORS.slice(0, labels.length),
                borderWidth: 2,
                borderColor: "#fff"
            }]
        },
        options: {
            plugins: {
                legend: { display: false }
            },
            cutout: "60%"
        }
    });

    // Custom legend
    let legendHtml = "";
    labels.forEach((l, i) => {
        legendHtml += `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <span style="width:12px;height:12px;border-radius:50%;background:${COLORS[i]};display:inline-block;"></span>
            <span>${l}: <strong>${formatMoney(values[i])}</strong></span>
        </div>`;
    });
    document.getElementById("ptLegend").innerHTML = legendHtml;
}


// =========================
// TOP MÓN BÁN CHẠY (UC06 – Bước 3)
// =========================
function renderTopItems(items) {
    let rows = "";
    items.forEach((item, i) => {
        rows += `
        <tr>
            <td><strong>${i + 1}</strong></td>
            <td>${item.TenMon}</td>
            <td><span class="badge bg-warning text-dark">${item.TenDanhMuc || "–"}</span></td>
            <td>${Number(item.TongSL).toLocaleString("vi-VN")}</td>
            <td>${formatMoney(item.DoanhThu)}</td>
        </tr>`;
    });
    document.getElementById("topItemsTable").innerHTML = rows || `
    <tr><td colspan="5" class="text-center text-muted">Không có dữ liệu</td></tr>`;

    // Bar chart Top món
    if (chartTopItems) { chartTopItems.destroy(); }
    const ctx = document.getElementById("chartTopItems").getContext("2d");
    chartTopItems = new Chart(ctx, {
        type: "bar",
        data: {
            labels: items.map(r => r.TenMon),
            datasets: [{
                label: "Số lượng bán",
                data: items.map(r => r.TongSL),
                backgroundColor: "rgba(255,152,0,0.7)",
                borderColor: "#ff9800",
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}


// =========================
// LỊCH SỬ CHỈNH SỬA (UC06 – Bước 4)
// =========================
function renderHistory(history) {
    if (!history || history.length === 0) {
        document.getElementById("historyTable").innerHTML = `
        <div class="empty-state">
            <div class="emoji">📂</div>
            <div>Không có lịch sử chỉnh sửa trong khoảng thời gian này</div>
        </div>`;
        return;
    }

    let rows = "";
    history.forEach(r => {
        rows += `
        <tr>
            <td>${r.MaDon}</td>
            <td>${r.TenNhanVien || "–"}</td>
            <td><span class="badge bg-secondary">${r.HanhDong || "–"}</span></td>
            <td style="font-size:13px;">${r.NoiDung || ""}</td>
            <td style="font-size:13px;">${r.ThoiGian || ""}</td>
        </tr>`;
    });

    document.getElementById("historyTable").innerHTML = `
    <table class="table table-hover align-middle">
        <thead>
            <tr>
                <th>Mã đơn</th>
                <th>Nhân viên</th>
                <th>Hành động</th>
                <th>Nội dung</th>
                <th>Thời gian</th>
            </tr>
        </thead>
        <tbody>${rows}</tbody>
    </table>`;
}


// =========================
// ĐƠN BẤT THƯỜNG (UC06 – TT03)
// =========================
function renderAnomalies(anomalies) {
    const btn = document.getElementById("tabAnomalyBtn");

    if (!anomalies || anomalies.length === 0) {
        btn.textContent = "⚠️ Đơn bất thường";
        document.getElementById("anomalyContent").innerHTML = `
        <div class="empty-state">
            <div class="emoji">✅</div>
            <div>Không phát hiện đơn hàng bất thường trong kỳ này</div>
        </div>`;
        return;
    }

    // Cảnh báo trên nút tab
    btn.textContent = `⚠️ Đơn bất thường (${anomalies.length})`;
    btn.style.background = "#fef9c3";
    btn.style.color = "#a16207";

    let rows = "";
    anomalies.forEach(r => {
        rows += `
        <tr>
            <td><strong>${r.MaDon}</strong></td>
            <td>${r.TenNhanVien || "–"}</td>
            <td>
                <span class="warning-badge">⚠️ ${r.SoLanChinhSua} lần</span>
            </td>
            <td style="font-size:13px;">${r.LanDau || ""}</td>
            <td style="font-size:13px;">${r.LanCuoi || ""}</td>
        </tr>`;
    });

    document.getElementById("anomalyContent").innerHTML = `
    <div style="margin-bottom:16px;padding:14px 18px;background:#fef9c3;border-radius:14px;
                color:#a16207;font-size:14px;font-weight:500;">
        ⚠️ Phát hiện <strong>${anomalies.length}</strong> đơn hàng có số lần chỉnh sửa bất thường (> 5 lần).
        Hệ thống không tự khóa – vui lòng xem xét thủ công.
    </div>
    <table class="table table-hover align-middle">
        <thead>
            <tr>
                <th>Mã đơn</th>
                <th>Nhân viên</th>
                <th>Số lần chỉnh sửa</th>
                <th>Lần đầu</th>
                <th>Lần cuối</th>
            </tr>
        </thead>
        <tbody>${rows}</tbody>
    </table>`;
}


// =========================
// CHUYỂN TAB
// =========================
function switchTab(name) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab-nav button").forEach(btn => btn.classList.remove("active"));

    document.getElementById(`tab${name.charAt(0).toUpperCase() + name.slice(1)}`).classList.add("active");
    event.target.classList.add("active");
}


// =========================
// XUẤT EXCEL (UC06.1)
// =========================
function exportExcel() {
    const tuNgay  = document.getElementById("tuNgay").value;
    const denNgay = document.getElementById("denNgay").value;
    if (!tuNgay || !denNgay) { alert("Chọn khoảng thời gian trước"); return; }
    window.open(`/report/export/excel?tu_ngay=${tuNgay}&den_ngay=${denNgay}`, "_blank");
}


// =========================
// XUẤT PDF (UC06.1)
// =========================
function exportPDF() {
    const tuNgay  = document.getElementById("tuNgay").value;
    const denNgay = document.getElementById("denNgay").value;
    if (!tuNgay || !denNgay) { alert("Chọn khoảng thời gian trước"); return; }
    window.open(`/report/export/pdf?tu_ngay=${tuNgay}&den_ngay=${denNgay}`, "_blank");
}


// =========================
// HELPERS
// =========================
function formatMoney(n) {
    if (!n && n !== 0) return "–";
    return Number(n).toLocaleString("vi-VN") + "đ";
}

function formatDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

function showLoading(show) {
    document.getElementById("loadingState").style.display = show ? "block" : "none";
    if (show) {
        document.getElementById("dashboard").style.display = "none";
        document.getElementById("emptyState").style.display = "none";
    }
}

