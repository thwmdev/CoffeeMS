/**
 * order.js  –  Gọi Món & Quản Lý Bàn
 * ─────────────────────────────────────
 * State:
 *   tables[]       – danh sách bàn từ API
 *   selectedTable  – bàn đang chọn { MaBan, TenBan, TrangThai, MaDon }
 *   currentOrder   – đơn hàng đang xem { MaDon, TrangThai, ChiTiet[], TongTien, ... }
 *   categories[]   – danh mục món
 *   searchTimer    – debounce timer
 *   MA_NV          – mock nhân viên (thay bằng session thực tế)
 */

const MA_NV = 2;  // TODO: lấy từ session / localStorage

let tables         = [];
let selectedTable  = null;
let currentOrder   = null;
let categories     = [];
let searchTimer    = null;


// ═══════════════════════════════════════════════════
//  KHỞI TẠO
// ═══════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    loadTables();
    loadCategories();
});


// ═══════════════════════════════════════════════════
//  BÀN
// ═══════════════════════════════════════════════════

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
        const amount = t.TongTien
            ? `<div class="tc-amount">${fmtMoney(t.TongTien)}</div>`
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

function selectTable(maBan) {
    selectedTable = tables.find(t => t.MaBan === maBan) || null;
    renderTables();  // re-render để highlight

    if (!selectedTable) return;

    if (selectedTable.TrangThai === "TRONG") {
        // Bàn trống – hiện panel tạo đơn
        showPanel("new");
        document.getElementById("panelNewOrderText").textContent =
            `${selectedTable.TenBan} đang trống. Tạo đơn mới?`;

    } else if (selectedTable.MaDon) {
        // Bàn đang dùng – load đơn
        loadOrder(selectedTable.MaDon);

    } else {
        showPanel("empty");
    }
}

function mapStatusCss(s) {
    return { TRONG: "empty", DANGSUDUNG: "busy", DADAT: "reserved" }[s] || "empty";
}

function mapStatusIcon(s) {
    return { TRONG: "✅", DANGSUDUNG: "🔶", DADAT: "🔵" }[s] || "❓";
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

    // Header
    document.getElementById("orderTitle").textContent   = currentOrder.TenBan;
    const badge = document.getElementById("orderStatus");
    badge.textContent  = mapOrderStatus(currentOrder.TrangThai);
    badge.className    = `status-badge status-${currentOrder.TrangThai}`;

    // Items
    const items = currentOrder.ChiTiet || [];
    const container = document.getElementById("orderItems");
    document.getElementById("orderItemCount").textContent = `${items.length} món`;

    if (!items.length) {
        container.innerHTML = `<div class="empty-order"><p>Chưa có món nào trong đơn</p></div>`;
    } else {
        container.innerHTML = items.map(item => renderOrderItem(item)).join("");
    }

    // Total
    document.getElementById("orderTotal").textContent = fmtMoney(currentOrder.TongTien || 0);

    // Send btn
    const btnSend = document.getElementById("btnSend");
    const hasCholam = items.some(i => i.TrangThaiMon === "CHOLAM");
    btnSend.disabled = !hasCholam || currentOrder.TrangThai === "CHOTHANHTOAN";
}

function renderOrderItem(item) {
    const isSent = item.TrangThaiMon !== "CHOLAM";
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
async function cancelOrder() {
    if (!currentOrder) return;

    const lydo = prompt("Lý do hủy đơn (không bắt buộc):", "");
    if (lydo === null) return;  // bấm Cancel

    try {
        const res = await fetch(`/order/${currentOrder.MaDon}/cancel`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ LyDo: lydo || "Hủy theo yêu cầu", MaNV: MA_NV })
        });
        const json = await res.json();
        if (!json.success) throw new Error(json.message);

        showToast("🗑️ Đơn hàng đã hủy", "info");
        currentOrder  = null;
        selectedTable = null;
        showPanel("empty");
        await loadTables();

    } catch (e) {
        showToast(e.message, "error");
    }
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
    const maCTDH  = document.getElementById("noteMaCTDH").value;
    const ghiChu  = document.getElementById("noteContent").value.trim();

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
//  UI HELPERS
// ═══════════════════════════════════════════════════

function showPanel(panel) {
    document.getElementById("panelEmpty").style.display    = "none";
    document.getElementById("panelOrder").style.display    = "none";
    document.getElementById("panelNewOrder").style.display = "none";
    clearSearch();

    if (panel === "empty")  document.getElementById("panelEmpty").style.display    = "block";
    if (panel === "order")  document.getElementById("panelOrder").style.display    = "flex";
    if (panel === "new")    document.getElementById("panelNewOrder").style.display = "block";
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
    t.className = `toast toast-${type}`;
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
