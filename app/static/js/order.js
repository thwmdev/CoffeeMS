/**
 * order.js  –  Gọi Món & Quản Lý Bàn
 * ─────────────────────────────────────
async function loadTables() {
    try {
        const res  = await fetch("/order/tables");
        const json = await res.json();
        if (!json.success) throw new Error(json.message);
        tables = json.data;
        renderTables();
    } catch (e) {
        showToast("Lỗi tải bàn: " + e.message, "error");
    }
    
    showToast("Áp dụng giảm giá thành công", "success");
    closeModal("modalDiscount");
    
    // Cập nhật lại UI đơn hàng hiện tại
    await loadOrder(currentOrder.MaDon);
    
    // Cập nhật lại UI danh sách bàn bên trái để hiển thị đúng giá mới
    await loadTables();
}
 * State:
 *   tables[]           – danh sách bàn từ API
 *   selectedTable      – bàn đang chọn
 *   currentOrder       – đơn hàng đang xem
 *   currentReservation – đặt bàn của bàn đang chọn (nếu có)
 *   categories[]       – danh mục món
 *   searchTimer        – debounce timer
 *   discountType       – 'amount' | 'percent'
 *   MA_NV              – mock nhân viên
 */

const MA_NV = 2;  // TODO: lấy từ session / localStorage

let tables             = [];
let selectedTable      = null;
let currentOrder       = null;
let currentReservation = null;   // ← MỚI
let categories         = [];
let searchTimer        = null;
let discountType       = 'amount';  // ← MỚI


// ═══════════════════════════════════════════════════
//  KHỞI TẠO
// ═══════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    loadTables();
    loadCategories();
    // Set default datetime-local cho modal đặt bàn
    setDefaultReserveDatetime();
});


// ═══════════════════════════════════════════════════
//  BÀN
// ═══════════════════════════════════════════════════
async function loadTables() {
    try {
        const res  = await fetch("/order/tables");
        
        if (!res.ok) throw new Error(`Lỗi kết nối máy chủ (HTTP ${res.status})`);
        
        const json = await res.json();
        if (!json.success) throw new Error(json.message);
        
        tables = json.data;
        
        // Cập nhật lại dữ liệu cho selectedTable để không bị kẹt data cũ
        if (selectedTable) {
            selectedTable = tables.find(t => t.MaBan === selectedTable.MaBan) || null;
        }

        renderTables();
    } catch (e) {
        showToast("Lỗi tải bàn: " + e.message, "error");
    }
}

function renderTables() {
    const grid = document.getElementById("tableGrid");

    if (!tables.length) {
        grid.innerHTML = `<div class="loading-pulse">Không có bàn nào</div>`;
        return;
    }

    grid.innerHTML = tables.map(t => {
        const css    = mapStatusCss(t.TrangThai);
        const icon   = mapStatusIcon(t.TrangThai);
        const label  = mapStatusLabel(t.TrangThai);
        const sel    = selectedTable && selectedTable.MaBan === t.MaBan ? "selected" : "";
        
        const displayAmount = t.ThanhTien ?? t.TongTien;
        
        const amount = displayAmount
            ? `<div class="tc-amount">${fmtMoney(displayAmount)}</div>`
            : "";

        return `
        <div class="table-card ${css} ${sel}" onclick="selectTable(${t.MaBan})">
            <div class="tc-icon">${icon}</div>
            <div class="tc-name">${t.TenBan}</div>
            <div class="tc-seats">${t.SoChoNgoi} chỗ</div>
            <div class="tc-status">${label}</div>
            ${amount}
        </div>`;
    }).join("");
}

async function selectTable(maBan) {
    selectedTable = tables.find(t => t.MaBan === maBan) || null;
    renderTables();

    if (!selectedTable) return;

    if (selectedTable.TrangThai === "TRONG") {
        showPanel("new");
        document.getElementById("panelNewOrderText").textContent =
            `${selectedTable.TenBan} đang trống. Tạo đơn mới?`;

    } else if (selectedTable.TrangThai === "DADAT") {
        // Bàn đã đặt – load thông tin đặt bàn
        await loadReservedPanel(selectedTable.MaBan);

    } else if (selectedTable.MaDon) {
        loadOrder(selectedTable.MaDon);

    } else {
        showPanel("empty");
    }
}

function mapStatusCss(s) {
    return { TRONG: "empty", DANGSUDUNG: "busy", DADAT: "reserved" }[s] || "empty";
}

function mapStatusIcon(s) {
    return { TRONG: "✅", DANGSUDUNG: "🔶", DADAT: "📅" }[s] || "❓";
}

function mapStatusLabel(s) {
    return { TRONG: "Trống", DANGSUDUNG: "Đang dùng", DADAT: "Đã đặt" }[s] || s;
}


// ═══════════════════════════════════════════════════
//  ĐƠN HÀNG
// ═══════════════════════════════════════════════════

async function loadOrder(maDon) {
    try {
        const res  = await fetch(`/order/${maDon}`);
        const json = await res.json();
        if (!json.success) throw new Error(json.message);
        currentOrder = json.data;
        showPanel("order");
        renderOrder();
    } catch (e) {
        showToast("Lỗi tải đơn: " + e.message, "error");
    }
}

function renderOrder() {
    if (!currentOrder) return;

    document.getElementById("orderTitle").textContent  = currentOrder.TenBan;
    const badge = document.getElementById("orderStatus");
    badge.textContent = mapOrderStatus(currentOrder.TrangThai);
    badge.className   = `status-badge status-${currentOrder.TrangThai}`;

    const items     = currentOrder.ChiTiet || [];
    const container = document.getElementById("orderItems");
    document.getElementById("orderItemCount").textContent = `${items.length} món`;

    if (!items.length) {
        container.innerHTML = `<div class="empty-order"><p>Chưa có món nào trong đơn</p></div>`;
    } else {
        container.innerHTML = items.map(item => renderOrderItem(item)).join("");
    }

    // Tổng tiền + giảm giá
    const tongTien  = currentOrder.TongTien  || 0;
    const giamGia   = currentOrder.GiamGia   || 0;
    const thanhTien = currentOrder.ThanhTien || 0;

    document.getElementById("orderTotal").textContent = fmtMoney(thanhTien);

    const discountRow  = document.getElementById("discountRow");
    const discountLine = document.getElementById("discountLine");

    if (giamGia > 0) {
        discountRow.style.display  = "flex";
        discountLine.style.display = "flex";
        document.getElementById("orderSubtotal").textContent  = fmtMoney(tongTien);
        document.getElementById("discountAmount").textContent = `– ${fmtMoney(giamGia)}`;
    } else {
        discountRow.style.display  = "none";
        discountLine.style.display = "none";
    }

    const btnSend    = document.getElementById("btnSend");
    const hasCholam  = items.some(i => i.TrangThaiMon === "CHOLAM");
    btnSend.disabled = !hasCholam || currentOrder.TrangThai === "CHOTHANHTOAN";
}

function renderOrderItem(item) {
    const isSent  = item.TrangThaiMon !== "CHOLAM";
    const noteHtml = item.GhiChu
        ? `<div class="oi-note">📝 ${escHtml(item.GhiChu)}</div>`
        : "";

    const qtyHtml = isSent
        ? `<span class="qty-val">${item.SoLuong}</span>`
        : `
        <div class="oi-qty">
            <button class="qty-btn" onclick="changeQty(${item.MaCTDH}, ${item.SoLuong}, -1)">−</button>
            <span class="qty-val">${item.SoLuong}</span>
            <button class="qty-btn" onclick="changeQty(${item.MaCTDH}, ${item.SoLuong}, +1)">+</button>
        </div>`;

    const actionsHtml = isSent
        ? ""
        : `
        <button class="oi-btn-note" onclick="openNoteModal(${item.MaCTDH}, '${escHtml(item.GhiChu || '')}')">📝</button>
        <button class="oi-btn-del"  onclick="deleteItem(${item.MaCTDH})">🗑</button>`;

    return `
    <div class="order-item" id="item-${item.MaCTDH}">
        <div class="oi-main">
            <div class="oi-name">${escHtml(item.TenMon)}</div>
            ${noteHtml}
            <span class="oi-status st-${item.TrangThaiMon}">${mapItemStatus(item.TrangThaiMon)}</span>
            ${qtyHtml}
        </div>
        <div class="oi-actions">
            <span class="oi-price">${fmtMoney(item.SoLuong * item.DonGia)}</span>
            ${actionsHtml}
        </div>
    </div>`;
}

function mapOrderStatus(s) {
    return {
        XACNHAN:      "Xác nhận",
        DANGPHUCVU:   "Đang phục vụ",
        CHOTHANHTOAN: "Chờ thanh toán",
        DATHANHTOAN:  "Đã thanh toán",
        HUY:          "Đã hủy"
    }[s] || s;
}

function mapItemStatus(s) {
    return { CHOLAM: "Chờ gửi", DANGLAM: "Đang làm", DAPHUCVU: "Đã phục vụ" }[s] || s;
}


// ─────────────────────────────────────────────
// TẠO ĐƠN HÀNG MỚI
// ─────────────────────────────────────────────
async function createOrder() {
    if (!selectedTable) return;

    try {
        const res = await fetch("/order/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ MaBan: selectedTable.MaBan, MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("✅ " + json.message, "success");
        await loadTables();
        await loadOrder(json.MaDon);

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ─────────────────────────────────────────────
// GỬI BẾP / BAR
// ─────────────────────────────────────────────
async function sendToKitchen() {
    if (!currentOrder) return;
    if (!confirm("Gửi tất cả món đang chờ xuống bếp/bar?")) return;

    try {
        const res = await fetch(`/order/${currentOrder.MaDon}/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("🚀 " + json.message, "success");
        await loadOrder(currentOrder.MaDon);
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ─────────────────────────────────────────────
// HỦY ĐƠN
// ─────────────────────────────────────────────
function cancelOrder() {
    if (!currentOrder) return;
 
    // Không cho hủy đơn đang chờ thanh toán
    if (currentOrder.TrangThai === "CHOTHANHTOAN") {
        showToast("Đơn đang chờ thanh toán, vui lòng thanh toán hoặc liên hệ quản lý", "error");
        return;
    }
 
    // Điền thông tin vào modal
    const tenBan = currentOrder.TenBan || `Đơn #${currentOrder.MaDon}`;
    document.getElementById("cancelOrderDesc").textContent =
        `Hủy đơn hàng tại ${tenBan}?`;
    document.getElementById("cancelOrderReason").value = "";
 
    document.getElementById("modalCancelOrder").style.display = "flex";
    setTimeout(() => document.getElementById("cancelOrderReason").focus(), 100);
}
 
async function confirmCancelOrder() {
    if (!currentOrder) return;
 
    const lyDo = document.getElementById("cancelOrderReason").value.trim()
                 || "Hủy theo yêu cầu";
 
    // Disable nút để tránh double-click
    const btn = document.querySelector(".btn-cancel-confirm");
    if (btn) btn.disabled = true;

    const token = getCookie("token");
 
    try {
        const res = await fetch(`/order/${currentOrder.MaDon}/cancel`, {
            method: "POST",
            headers: {
                 "Content-Type": "application/json",
                 "Authorization": `Bearer ${token}` 
                },

            body: JSON.stringify({ LyDo: lyDo, MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);
 
        showToast("❌ " + json.message, "info");
        closeModal("modalCancelOrder");
        currentOrder  = null;
        selectedTable = null;
        showPanel("empty");
        await loadTables();
 
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        if (btn) btn.disabled = false;
    }
}


// ═══════════════════════════════════════════════════
//  CHỈNH SỬA ĐƠN – GIẢM GIÁ  ← MỚI
// ═══════════════════════════════════════════════════

function openDiscountModal() {
    if (!currentOrder) return;
    if (currentOrder.TrangThai === "CHOTHANHTOAN") {
        showToast("Đơn đang chờ thanh toán, không thể chỉnh sửa", "error");
        return;
    }

    // Reset form
    discountType = "amount";
    switchDiscountType("amount");
    document.getElementById("discountValue").value   = "";
    document.getElementById("discountPercent").value = "";
    document.getElementById("orderNoteContent").value = "";
    document.getElementById("discountPreview").style.display = "none";

    // Điền giá trị hiện tại
    const tongTien = currentOrder.TongTien || 0;
    const giamGia  = currentOrder.GiamGia  || 0;
    document.getElementById("dsTongTien").textContent = fmtMoney(tongTien);

    if (giamGia > 0) {
        document.getElementById("discountValue").value = giamGia;
        previewDiscount();
    }

    document.getElementById("modalDiscount").style.display = "flex";
    setTimeout(() => document.getElementById("discountValue").focus(), 100);
}

function switchDiscountType(type) {
    discountType = type;
    document.getElementById("tabAmount").classList.toggle("active", type === "amount");
    document.getElementById("tabPercent").classList.toggle("active", type === "percent");
    document.getElementById("discountAmountInput").style.display  = type === "amount"  ? "block" : "none";
    document.getElementById("discountPercentInput").style.display = type === "percent" ? "block" : "none";
    document.getElementById("discountPreview").style.display = "none";
    previewDiscount();
}

function setPercent(val) {
    document.getElementById("discountPercent").value = val;
    previewDiscount();
}

function previewDiscount() {
    const tongTien = currentOrder ? (currentOrder.TongTien || 0) : 0;
    if (!tongTien) return;

    let giamGia = 0;
    if (discountType === "amount") {
        giamGia = parseFloat(document.getElementById("discountValue").value) || 0;
    } else {
        const pct = parseFloat(document.getElementById("discountPercent").value) || 0;
        giamGia = Math.round(tongTien * pct / 100);
    }

    giamGia = Math.max(0, Math.min(giamGia, tongTien));
    const thanhTien = tongTien - giamGia;

    const preview = document.getElementById("discountPreview");
    if (giamGia > 0) {
        preview.style.display = "block";
        document.getElementById("dpGiamGia").textContent   = `– ${fmtMoney(giamGia)}`;
        document.getElementById("dpThanhTien").textContent = fmtMoney(thanhTien);
    } else {
        preview.style.display = "none";
    }
}

async function confirmDiscount() {
    if (!currentOrder) return;

    const tongTien = currentOrder.TongTien || 0;
    let giamGia = 0;

    if (discountType === "amount") {
        giamGia = parseFloat(document.getElementById("discountValue").value) || 0;
    } else {
        const pct = parseFloat(document.getElementById("discountPercent").value) || 0;
        giamGia = Math.round(tongTien * pct / 100);
    }

    giamGia = Math.max(0, Math.min(giamGia, tongTien));
    const ghiChu = document.getElementById("orderNoteContent").value.trim();

    try {
        const res = await fetch(`/order/${currentOrder.MaDon}/discount`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ GiamGia: giamGia, GhiChu: ghiChu || null, MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("🏷️ Đã cập nhật giảm giá", "success");
        closeModal("modalDiscount");
        
        // Cập nhật lại UI đơn hàng
        await loadOrder(currentOrder.MaDon);
        
        // ✅ CẬP NHẬT: Load lại danh sách bàn để làm mới giá tiền trên card bàn
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}
async function removeDiscount() {
    if (!currentOrder) return;
    if (!confirm("Bỏ giảm giá khỏi đơn này?")) return;

    try {
        const res = await fetch(`/order/${currentOrder.MaDon}/discount`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ GiamGia: 0, MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("Đã bỏ giảm giá", "info");
        
        // Cập nhật lại UI đơn hàng hiện tại
        await loadOrder(currentOrder.MaDon);
        
        // ✅ THÊM DÒNG NÀY: Cập nhật lại danh sách bàn để giá trên card quay về giá gốc
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}

// ═══════════════════════════════════════════════════
//  LỊCH SỬ ĐƠN  ← MỚI
// ═══════════════════════════════════════════════════

async function openHistoryModal() {
    if (!currentOrder) return;
    document.getElementById("historyList").innerHTML = `<div class="loading-pulse">Đang tải...</div>`;
    document.getElementById("modalHistory").style.display = "flex";

    try {
        const res  = await fetch(`/order/${currentOrder.MaDon}/history`);
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        const list  = json.data;
        const listEl = document.getElementById("historyList");

        if (!list.length) {
            listEl.innerHTML = `<div class="history-empty">Chưa có lịch sử thao tác</div>`;
            return;
        }

        listEl.innerHTML = list.map(item => {
            const icon = mapHistoryIcon(item.HanhDong);
            const time = item.ThoiGian ? item.ThoiGian.slice(11, 16) : "";
            const date = item.ThoiGian ? item.ThoiGian.slice(0, 10) : "";
            return `
            <div class="history-item">
                <div class="hi-icon">${icon}</div>
                <div class="hi-main">
                    <div class="hi-action">${mapHistoryAction(item.HanhDong)}</div>
                    <div class="hi-note">${escHtml(item.NoiDung || "")}</div>
                    <div class="hi-meta">${escHtml(item.TenNhanVien || "NV")} · ${date} ${time}</div>
                </div>
            </div>`;
        }).join("");

    } catch (e) {
        document.getElementById("historyList").innerHTML =
            `<div class="history-empty">Lỗi: ${escHtml(e.message)}</div>`;
    }
}

function mapHistoryIcon(action) {
    const m = {
        TAODON: "🆕", THEMMON: "➕", CAPNHAT: "✏️", XOAMON: "🗑️",
        GUIBEP: "🚀", HUYDON: "❌", CHUYENBAN: "🔀", GOPBAN: "🔗",
        GHICHU: "📝", GIAMGIA: "🏷️", THANHTOAN: "💰"
    };
    return m[action] || "📌";
}

function mapHistoryAction(action) {
    const m = {
        TAODON: "Tạo đơn", THEMMON: "Thêm món", CAPNHAT: "Cập nhật",
        XOAMON: "Xóa món", GUIBEP: "Gửi bếp", HUYDON: "Hủy đơn",
        CHUYENBAN: "Chuyển bàn", GOPBAN: "Gộp bàn",
        GHICHU: "Ghi chú", GIAMGIA: "Giảm giá", THANHTOAN: "Thanh toán"
    };
    return m[action] || action;
}


// ═══════════════════════════════════════════════════
//  TÌM KIẾM MÓN
// ═══════════════════════════════════════════════════

async function loadCategories() {
    try {
        const res  = await fetch("/order/menu/categories");
        const json = await res.json();
        if (!json.success) return;
        categories = json.data;
        const sel = document.getElementById("filterCat");
        categories.forEach(c => {
            const opt = document.createElement("option");
            opt.value = c.MaDM;
            opt.textContent = c.TenDanhMuc;
            sel.appendChild(opt);
        });
    } catch (_) {}
}

function handleSearch() {
    const q = document.getElementById("searchInput").value.trim();
    document.getElementById("btnClearSearch").style.display = q ? "block" : "none";
    clearTimeout(searchTimer);
    searchTimer = setTimeout(doSearch, 260);
}

async function doSearch() {
    const q  = document.getElementById("searchInput").value.trim();
    const dm = document.getElementById("filterCat").value;

    const panel = document.getElementById("searchResults");


    // SỬA: Hiện/ẩn nút X dựa trên cả q VÀ dm
function handleSearch() {
    const q  = document.getElementById("searchInput").value.trim();
    const dm = document.getElementById("filterCat").value;
    // Hiện nút X nếu có q hoặc dm
    document.getElementById("btnClearSearch").style.display = (q || dm) ? "block" : "none";
    clearTimeout(searchTimer);
    searchTimer = setTimeout(doSearch, 260);
}

    if (!q && !dm) {
        panel.style.display = "none";
        panel.innerHTML = "";
        return;
    }

    try {
        const url  = `/order/menu/search?q=${encodeURIComponent(q)}&dm=${dm}`;
        const res  = await fetch(url);
        const json = await res.json();
        if (!json.success) return;

        const items = json.data;
        panel.style.display = "block";

        if (!items.length) {
            panel.innerHTML = `<div class="search-empty">Không tìm thấy món nào</div>`;
            return;
        }

        panel.innerHTML = items.map(m => `
            <div class="search-item" onclick="addItemToOrder(${m.MaMon}, '${escHtml(m.TenMon)}')">
                <div class="si-info">
                    <div class="si-name">${escHtml(m.TenMon)}</div>
                    <div class="si-cat">${escHtml(m.TenDanhMuc)}</div>
                </div>
                <span class="si-price">${fmtMoney(m.GiaBan)}</span>
                <button class="si-add" title="Thêm vào đơn">+</button>
            </div>
        `).join("");

    } catch (e) {
        console.error(e);
    }
}

function clearSearch() {
    document.getElementById("searchInput").value = "";
    document.getElementById("btnClearSearch").style.display = "none";
    document.getElementById("searchResults").style.display = "none";
    document.getElementById("searchResults").innerHTML = "";
}


// ─────────────────────────────────────────────
// THÊM MÓN VÀO ĐƠN
// ─────────────────────────────────────────────
async function addItemToOrder(maMon, tenMon) {
    if (!currentOrder) {
        showToast("Vui lòng chọn bàn và tạo đơn trước", "error");
        return;
    }
    if (currentOrder.TrangThai === "CHOTHANHTOAN") {
        showToast("Đơn đang chờ thanh toán, không thể thêm món", "error");
        return;
    }

    try {
        const res = await fetch(`/order/${currentOrder.MaDon}/add-item`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ MaMon: maMon, SoLuong: 1, MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast(`✅ Đã thêm ${tenMon}`, "success");
        await loadOrder(currentOrder.MaDon);

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ─────────────────────────────────────────────
// CẬP NHẬT SỐ LƯỢNG
// ─────────────────────────────────────────────
async function changeQty(maCTDH, currentQty, delta) {
    const newQty = currentQty + delta;
    if (newQty < 0) return;

    if (newQty === 0 && !confirm("Xóa món này khỏi đơn?")) return;

    try {
        const res = await fetch(`/order/item/${maCTDH}/qty`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ SoLuong: newQty, MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        await loadOrder(currentOrder.MaDon);

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ─────────────────────────────────────────────
// XÓA MÓN
// ─────────────────────────────────────────────
async function deleteItem(maCTDH) {
    if (!confirm("Xóa món này khỏi đơn?")) return;

    try {
        const res = await fetch(`/order/item/${maCTDH}?MaNV=${MA_NV}`, {
            method: "DELETE"
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("🗑️ Đã xóa món", "info");
        await loadOrder(currentOrder.MaDon);

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ═══════════════════════════════════════════════════
//  GHI CHÚ MÓN
// ═══════════════════════════════════════════════════

function openNoteModal(maCTDH, currentNote) {
    document.getElementById("noteMaCTDH").value   = maCTDH;
    document.getElementById("noteContent").value  = currentNote || "";
    document.getElementById("modalNote").style.display = "flex";
    setTimeout(() => document.getElementById("noteContent").focus(), 100);
}

async function confirmNote() {
    const maCTDH = document.getElementById("noteMaCTDH").value;
    const ghiChu = document.getElementById("noteContent").value.trim();

    try {
        const res = await fetch(`/order/item/${maCTDH}/note`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ GhiChu: ghiChu, MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("📝 Đã lưu ghi chú", "success");
        closeModal("modalNote");
        await loadOrder(currentOrder.MaDon);

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ═══════════════════════════════════════════════════
//  CHUYỂN BÀN
// ═══════════════════════════════════════════════════

function openTransferModal() {
    if (!currentOrder) return;

    const sel = document.getElementById("transferTarget");
    sel.innerHTML = `<option value="">-- Chọn bàn trống --</option>`;

    tables
        .filter(t => t.TrangThai === "TRONG")
        .forEach(t => {
            const opt = document.createElement("option");
            opt.value = t.MaBan;
            opt.textContent = `${t.TenBan} (${t.SoChoNgoi} chỗ)`;
            sel.appendChild(opt);
        });

    document.getElementById("modalTransfer").style.display = "flex";
}

async function confirmTransfer() {
    const maBanMoi = document.getElementById("transferTarget").value;
    if (!maBanMoi) { showToast("Vui lòng chọn bàn đích", "error"); return; }

    try {
        const res = await fetch("/order/table/transfer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                MaDon:    currentOrder.MaDon,
                MaBanMoi: parseInt(maBanMoi),
                MaNV:     MA_NV
            })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("🔀 " + json.message, "success");
        closeModal("modalTransfer");
        selectedTable = null;
        currentOrder  = null;
        showPanel("empty");
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ═══════════════════════════════════════════════════
//  GỘP BÀN
// ═══════════════════════════════════════════════════

function openMergeModal() {
    if (!currentOrder) return;

    const sel = document.getElementById("mergeTarget");
    sel.innerHTML = `<option value="">-- Chọn bàn đang dùng --</option>`;

    tables
        .filter(t =>
            t.TrangThai === "DANGSUDUNG" &&
            t.MaDon &&
            t.MaDon !== currentOrder.MaDon
        )
        .forEach(t => {
            const opt = document.createElement("option");
            opt.value = t.MaDon;
            opt.textContent = `${t.TenBan} (Đơn #${t.MaDon})`;
            sel.appendChild(opt);
        });

    document.getElementById("modalMerge").style.display = "flex";
}

async function confirmMerge() {
    const maDonPhu = document.getElementById("mergeTarget").value;
    if (!maDonPhu) { showToast("Vui lòng chọn bàn cần gộp", "error"); return; }

    if (!confirm("Gộp bàn này vào đơn hiện tại? Hành động không thể hoàn tác!")) return;

    try {
        const res = await fetch("/order/table/merge", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                MaDonChinh: currentOrder.MaDon,
                MaDonPhu:   parseInt(maDonPhu),
                MaNV:       MA_NV
            })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("🔗 " + json.message, "success");
        closeModal("modalMerge");
        await loadOrder(currentOrder.MaDon);
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ═══════════════════════════════════════════════════
//  ĐẶT BÀN (RESERVATION)  ← MỚI
// ═══════════════════════════════════════════════════

// ── Thiết lập datetime-local mặc định (1 giờ sau thời điểm hiện tại)
function setDefaultReserveDatetime() {
    const now = new Date();
    now.setHours(now.getHours() + 1, 0, 0, 0);
    const iso = now.toISOString().slice(0, 16);
    document.getElementById("reserveGioDen").value = iso;
    document.getElementById("reserveGioDen").min   = new Date().toISOString().slice(0, 16);
}

// ── Mở modal đặt bàn (từ panel bàn trống)
function openReserveModal() {
    if (!selectedTable) return;

    setDefaultReserveDatetime();
    document.getElementById("reserveTenKhach").value = "";
    document.getElementById("reserveSDT").value      = "";
    document.getElementById("reserveSoNguoi").value  = Math.min(2, selectedTable.SoChoNgoi);

    document.getElementById("reserveTableInfo").innerHTML = `
        <div class="reserve-table-badge">
            <span class="rtb-icon">🪑</span>
            <span class="rtb-name">${escHtml(selectedTable.TenBan)}</span>
            <span class="rtb-seats">${selectedTable.SoChoNgoi} chỗ ngồi</span>
        </div>`;

    document.getElementById("modalReserve").style.display = "flex";
    setTimeout(() => document.getElementById("reserveTenKhach").focus(), 100);
}

// ── Xác nhận đặt bàn
async function confirmReserve() {
    const tenKhach = document.getElementById("reserveTenKhach").value.trim();
    const sdt      = document.getElementById("reserveSDT").value.trim();
    const gioDen   = document.getElementById("reserveGioDen").value;
    const soNguoi  = parseInt(document.getElementById("reserveSoNguoi").value) || 0;

    if (!tenKhach) { showToast("Vui lòng nhập tên khách", "error"); return; }
    if (!sdt)      { showToast("Vui lòng nhập số điện thoại", "error"); return; }
    if (!gioDen)   { showToast("Vui lòng chọn giờ đến", "error"); return; }
    if (soNguoi < 1){ showToast("Số người phải ≥ 1", "error"); return; }

    // Format giờ đến → "YYYY-MM-DD HH:MM"
    const gioDenFormatted = gioDen.replace("T", " ");

    try {
        const res = await fetch("/order/reservations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                MaBan:    selectedTable.MaBan,
                TenKhach: tenKhach,
                SDT:      sdt,
                GioDen:   gioDenFormatted,
                SoNguoi:  soNguoi
            })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("📅 " + json.message, "success");
        closeModal("modalReserve");
        selectedTable = null;
        showPanel("empty");
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}

// ── Load panel bàn đã đặt
async function loadReservedPanel(maBan) {
    showPanel("reserved");
    currentReservation = null;

    try {
        const today = new Date().toISOString().slice(0, 10);
        // Lấy đặt bàn của bàn này trong ngày hôm nay (hoặc gần nhất)
        const res  = await fetch(`/order/reservations?all=1`);
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        const reservations = json.data.filter(r => r.MaBan === maBan);
        const ban = tables.find(t => t.MaBan === maBan);

        document.getElementById("panelReservedText").textContent =
            `${ban ? ban.TenBan : "Bàn"} đã được đặt trước`;

        if (reservations.length === 0) {
            document.getElementById("reservedInfo").innerHTML =
                `<p style="color:#9ca3af;text-align:center;">Không tìm thấy thông tin đặt bàn</p>`;
            document.getElementById("btnCheckin").style.display = "none";
            return;
        }

        // Lấy đặt bàn gần nhất
        const r = reservations[0];
        currentReservation = r;
        document.getElementById("btnCheckin").dataset.maDatBan = r.MaDatBan;
        document.getElementById("btnCheckin").style.display = "inline-flex";

        const gioDen = r.GioDen ? r.GioDen.slice(0, 16).replace("T", " ") : "–";
        document.getElementById("reservedInfo").innerHTML = `
            <div class="ri-row"><span class="ri-label">👤 Khách</span>   <strong>${escHtml(r.TenKhach)}</strong></div>
            <div class="ri-row"><span class="ri-label">📞 SĐT</span>     <strong>${escHtml(r.SDT)}</strong></div>
            <div class="ri-row"><span class="ri-label">🕐 Giờ đến</span> <strong>${gioDen}</strong></div>
            <div class="ri-row"><span class="ri-label">👥 Số người</span><strong>${r.SoNguoi} người</strong></div>
            ${reservations.length > 1 ? `<div class="ri-more">+${reservations.length - 1} đặt bàn khác</div>` : ""}
        `;

    } catch (e) {
        showToast("Lỗi tải đặt bàn: " + e.message, "error");
    }
}

// ── Nhận bàn (check-in)
async function checkinReservation() {
    if (!currentReservation) return;

    const r = currentReservation;
    if (!confirm(`Nhận bàn cho khách ${r.TenKhach}? Đặt bàn sẽ được xóa và đơn hàng mới sẽ được tạo.`)) return;

    try {
        const res = await fetch(`/order/reservations/${r.MaDatBan}/checkin`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("✅ " + json.message, "success");
        currentReservation = null;
        await loadTables();
        await loadOrder(json.MaDon);

    } catch (e) {
        showToast(e.message, "error");
    }
}

// ── Hủy đặt bàn hiện tại (từ panel reserved)
async function cancelCurrentReservation() {
    if (!currentReservation) return;

    const r = currentReservation;
    if (!confirm(`Hủy đặt bàn của khách ${r.TenKhach}?`)) return;

    try {
        const res = await fetch(`/order/reservations/${r.MaDatBan}`, {
            method: "DELETE"
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("🗑️ Đã hủy đặt bàn", "info");
        currentReservation = null;
        selectedTable = null;
        showPanel("empty");
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}

// ── Modal danh sách đặt bàn
async function openReservationListModal() {
    setRlToday();
    document.getElementById("modalReservationList").style.display = "flex";
    await loadReservationList();
}

function setRlToday() {
    document.getElementById("rlDate").value = new Date().toISOString().slice(0, 10);
}

async function loadReservationList() {
    const date    = document.getElementById("rlDate").value;
    const content = document.getElementById("reservationListContent");
    content.innerHTML = `<div class="loading-pulse">Đang tải...</div>`;

    try {
        const url  = date ? `/order/reservations?date=${date}` : `/order/reservations?all=1`;
        const res  = await fetch(url);
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        renderReservationList(json.data);
    } catch (e) {
        content.innerHTML = `<div class="history-empty">Lỗi: ${escHtml(e.message)}</div>`;
    }
}

async function loadAllReservations() {
    document.getElementById("rlDate").value = "";
    const content = document.getElementById("reservationListContent");
    content.innerHTML = `<div class="loading-pulse">Đang tải...</div>`;

    try {
        const res  = await fetch(`/order/reservations?all=1`);
        const json = await res.json();
        if (!json.success) throw new Error(json.message);
        renderReservationList(json.data);
    } catch (e) {
        content.innerHTML = `<div class="history-empty">Lỗi: ${escHtml(e.message)}</div>`;
    }
}

function renderReservationList(list) {
    const content = document.getElementById("reservationListContent");

    if (!list.length) {
        content.innerHTML = `<div class="rl-empty">Không có đặt bàn nào</div>`;
        return;
    }

    content.innerHTML = `
        <table class="rl-table">
            <thead>
                <tr>
                    <th>Bàn</th>
                    <th>Khách hàng</th>
                    <th>SĐT</th>
                    <th>Giờ đến</th>
                    <th>Số người</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                ${list.map(r => {
                    const gioDen = r.GioDen ? r.GioDen.slice(0, 16).replace("T", " ") : "–";
                    return `
                    <tr>
                        <td><span class="rl-table-badge">${escHtml(r.TenBan)}</span></td>
                        <td><strong>${escHtml(r.TenKhach)}</strong></td>
                        <td>${escHtml(r.SDT)}</td>
                        <td>${gioDen}</td>
                        <td>${r.SoNguoi} người</td>
                        <td class="rl-actions">
                            <button class="rl-btn-edit"   onclick="openEditReservation(${r.MaDatBan}, '${escHtml(r.TenKhach)}', '${escHtml(r.SDT)}', '${r.GioDen ? r.GioDen.slice(0,16) : ""}', ${r.SoNguoi})">✏️</button>
                            <button class="rl-btn-delete" onclick="deleteReservationFromList(${r.MaDatBan}, '${escHtml(r.TenKhach)}')">🗑️</button>
                        </td>
                    </tr>`;
                }).join("")}
            </tbody>
        </table>`;
}

function openEditReservation(maDatBan, tenKhach, sdt, gioDen, soNguoi) {
    document.getElementById("editReserveMaDatBan").value  = maDatBan;
    document.getElementById("editReserveTenKhach").value  = tenKhach;
    document.getElementById("editReserveSDT").value       = sdt;
    document.getElementById("editReserveGioDen").value    = gioDen;
    document.getElementById("editReserveSoNguoi").value   = soNguoi;
    document.getElementById("modalEditReservation").style.display = "flex";
}

async function confirmEditReservation() {
    const maDatBan = document.getElementById("editReserveMaDatBan").value;
    const tenKhach = document.getElementById("editReserveTenKhach").value.trim();
    const sdt      = document.getElementById("editReserveSDT").value.trim();
    const gioDenRaw = document.getElementById("editReserveGioDen").value;
    const soNguoi  = parseInt(document.getElementById("editReserveSoNguoi").value) || 0;

    if (!tenKhach || !sdt || !gioDenRaw) {
        showToast("Vui lòng điền đầy đủ thông tin", "error");
        return;
    }

    const gioDen = gioDenRaw.replace("T", " ");

    try {
        const res = await fetch(`/order/reservations/${maDatBan}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ TenKhach: tenKhach, SDT: sdt, GioDen: gioDen, SoNguoi: soNguoi })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("✅ Đã cập nhật đặt bàn", "success");
        closeModal("modalEditReservation");
        await loadReservationList();
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}

async function deleteReservationFromList(maDatBan, tenKhach) {
    if (!confirm(`Hủy đặt bàn của khách ${tenKhach}?`)) return;

    try {
        const res = await fetch(`/order/reservations/${maDatBan}`, { method: "DELETE" });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("🗑️ Đã hủy đặt bàn", "info");
        await loadReservationList();
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
}


// ═══════════════════════════════════════════════════
//  UI HELPERS
// ═══════════════════════════════════════════════════

function showPanel(panel) {
    document.getElementById("panelEmpty").style.display    = "none";
    document.getElementById("panelOrder").style.display    = "none";
    document.getElementById("panelNewOrder").style.display = "none";
    document.getElementById("panelReserved").style.display = "none";
    clearSearch();

    if (panel === "empty")    document.getElementById("panelEmpty").style.display    = "block";
    if (panel === "order")    document.getElementById("panelOrder").style.display    = "flex";
    if (panel === "new")      document.getElementById("panelNewOrder").style.display = "block";
    if (panel === "reserved") document.getElementById("panelReserved").style.display = "block";
}

function closeModal(id) {
    document.getElementById(id).style.display = "none";
}

// Close modal when clicking backdrop
document.querySelectorAll(".modal-overlay").forEach(el => {
    el.addEventListener("click", e => {
        if (e.target === el) el.style.display = "none";
    });
});

let toastTimer = null;
function showToast(msg, type = "info") {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.className   = `toast toast-${type}`;
    t.style.display = "block";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.style.display = "none"; }, 3000);
}

function fmtMoney(val) {
    return Number(val || 0).toLocaleString("vi-VN") + " đ";
}

function escHtml(str) {
    if (!str) return "";
    return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
