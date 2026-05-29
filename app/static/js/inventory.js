let editingId = null;
let inventoryData = [];


// =========================
// LOAD INVENTORY
// =========================
function loadInventory() {

    fetch("/inventory/api")
        .then(res => {
            if (!res.ok) throw new Error("Không thể tải kho");
            return res.json();
        })
        .then(data => {

            inventoryData = data;

            document.getElementById("totalInventory").innerText = data.length;

            renderInventory(data);
        })
        .catch(err => {
            console.log(err);
            alert("Lỗi tải kho nguyên liệu");
        });
}

loadInventory();


// =========================
// PHÂN LOẠI TỒN KHO
// =========================
function getStockStatus(item) {

    const ton = Number(item.SoLuongTon);
    const dinhMuc = Number(item.DinhMucTonKho);

    if (ton <= 0) {
        return {
            text: "Hết hàng",
            class: "out-stock"
        };
    }

    if (ton <= dinhMuc) {
        return {
            text: "Sắp hết",
            class: "low-stock"
        };
    }

    return {
        text: "Bình thường",
        class: "normal-stock"
    };
}


// =========================
// RENDER TABLE
// =========================
function renderInventory(data) {

    let html = "";

    data.forEach(item => {

        const stock = getStockStatus(item);

        html += `
        <tr>
            <td>${item.MaNL}</td>
            <td>${item.TenNL}</td>
            <td>${item.DonViTinh}</td>
            <td>${Number(item.SoLuongTon).toLocaleString()}</td>
            <td>${Number(item.DinhMucTonKho).toLocaleString()}</td>

            <td>
                <span class="${stock.class}">
                    ${stock.text}
                </span>
            </td>

            <td class="d-flex gap-2">
                <button class="btn btn-warning btn-sm"
                    onclick="editIngredient(${item.MaNL})">
                    Sửa
                </button>

                <button class="btn btn-danger btn-sm"
                    onclick="deleteIngredient(${item.MaNL})">
                    Xóa
                </button>
            </td>
        </tr>
        `;
    });

    document.getElementById("inventoryTable").innerHTML = html;
}


// =========================
// GET FORM DATA
// =========================
function getFormData() {

    return {
        TenNL: document.getElementById("TenNL").value.trim(),
        DonViTinh: document.getElementById("DonViTinh").value.trim(),
        SoLuongTon: Number(document.getElementById("SoLuongTon").value),
        DinhMucTonKho: Number(document.getElementById("DinhMucTonKho").value)
    };
}


// =========================
// RESET FORM
// =========================
function resetForm() {

    document.getElementById("TenNL").value = "";
    document.getElementById("DonViTinh").value = "";
    document.getElementById("SoLuongTon").value = "";
    document.getElementById("DinhMucTonKho").value = "";

    editingId = null;

    const oldError = document.getElementById("formError");
    if (oldError) oldError.remove();

    document.querySelectorAll(".input-error")
        .forEach(el => el.classList.remove("input-error"));
}


// =========================
// VALIDATE
// =========================
function validateForm() {

    let ok = true;

    const ten = document.getElementById("TenNL");
    const dv = document.getElementById("DonViTinh");
    const sl = document.getElementById("SoLuongTon");

    [ten, dv, sl].forEach(el => el.classList.remove("input-error"));

    const old = document.getElementById("formError");
    if (old) old.remove();

    if (ten.value.trim() === "") {
        ten.classList.add("input-error");
        ok = false;
    }

    if (dv.value.trim() === "") {
        dv.classList.add("input-error");
        ok = false;
    }

    if (sl.value === "" || Number(sl.value) < 0) {
        sl.classList.add("input-error");
        ok = false;
    }

    if (!ok) {
        const err = document.createElement("div");
        err.id = "formError";
        err.className = "text-danger fw-bold mt-3";
        err.innerText = "Vui lòng nhập thông tin hợp lệ";
        document.querySelector(".form-box").appendChild(err);
    }

    return ok;
}


// =========================
// ADD
// =========================
function addIngredient() {

    if (!validateForm()) return;
    if (!confirm("Thêm nguyên liệu?")) return;

    fetch("/inventory/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(getFormData())
    })
    .then(r => r.json().then(data => ({ ok: r.ok, data })))
    .then(res => {

        if (!res.ok) throw new Error(res.data.message);

        alert(res.data.message);
        loadInventory();
        resetForm();
    })
    .catch(err => alert(err.message));
}


// =========================
// EDIT
// =========================
function editIngredient(id) {

    fetch("/inventory/" + id)
        .then(r => r.json())
        .then(data => {

            document.getElementById("TenNL").value = data.TenNL;
            document.getElementById("DonViTinh").value = data.DonViTinh;
            document.getElementById("SoLuongTon").value = data.SoLuongTon;
            document.getElementById("DinhMucTonKho").value = data.DinhMucTonKho;

            editingId = id;
        });
}


// =========================
// UPDATE
// =========================
function updateIngredient() {

    if (!validateForm()) return;

    if (!editingId) {
        alert("Chọn nguyên liệu cần sửa");
        return;
    }

    if (!confirm("Cập nhật?")) return;

    fetch("/inventory/update/" + editingId, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(getFormData())
    })
    .then(r => r.json().then(data => ({ ok: r.ok, data })))
    .then(res => {

        if (!res.ok) throw new Error(res.data.message);

        alert(res.data.message);
        loadInventory();
        resetForm();
    })
    .catch(err => alert(err.message));
}


// =========================
// DELETE
// =========================
function deleteIngredient(id) {

    if (!confirm("Xóa nguyên liệu?")) return;

    fetch("/inventory/delete/" + id, {
        method: "DELETE"
    })
    .then(r => r.json().then(data => ({ ok: r.ok, data })))
    .then(res => {

        if (!res.ok) throw new Error(res.data.message);

        alert(res.data.message);
        loadInventory();
    })
    .catch(err => alert(err.message));
}


// =========================
// SEARCH
// =========================
function searchInventory() {

    const keyword = document.getElementById("searchKeyword").value.toLowerCase();
    const minStock = Number(document.getElementById("minStock").value) || 0;
    const maxStock = Number(document.getElementById("maxStock").value) || Infinity;

    const filtered = inventoryData.filter(item => {

        const matchKeyword =
            item.TenNL.toLowerCase().includes(keyword) ||
            String(item.MaNL).includes(keyword);

        const stock = Number(item.SoLuongTon);

        return (
            matchKeyword &&
            stock >= minStock &&
            stock <= maxStock
        );
    });

    renderInventory(filtered);
}

// =========================
// NHẬP KHO (IMPORT INVENTORY)
// =========================
function importInventory() {
    // Lấy dữ liệu từ giao diện
    const importId = document.getElementById("ImportId").value.trim();
    const soLuongNhap = document.getElementById("SoLuongNhap").value.trim();

    // Kiểm tra dữ liệu nhanh tại Client
    if (!importId) {
        alert("Vui lòng nhập Mã nguyên liệu");
        document.getElementById("ImportId").focus();
        return;
    }

    if (!soLuongNhap || Number(soLuongNhap) <= 0) {
        alert("Số lượng nhập phải lớn hơn 0");
        document.getElementById("SoLuongNhap").focus();
        return;
    }

    if (!confirm(`Bạn có chắc chắn muốn nhập kho cho nguyên liệu ID: ${importId}?`)) return;

    // Gọi API PATCH sang backend
    fetch("/inventory/import/" + importId, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            SoLuongNhap: Number(soLuongNhap)
        })
    })
    .then(r => r.json().then(data => ({ ok: r.ok, data })))
    .then(res => {
        if (!res.ok) throw new Error(res.data.message);

        alert(res.data.message);
        
        // Xóa dữ liệu cũ trên form nhập kho
        document.getElementById("ImportId").value = "";
        document.getElementById("SoLuongNhap").value = "";
        
        // Tải lại danh sách nguyên liệu để cập nhật số tồn kho mới
        loadInventory(); 
    })
    .catch(err => alert("Lỗi: " + err.message));
}

function editIngredient(id) {
    fetch("/inventory/" + id)
        .then(r => r.json())
        .then(data => {
            document.getElementById("TenNL").value = data.TenNL;
            document.getElementById("DonViTinh").value = data.DonViTinh;
            document.getElementById("SoLuongTon").value = data.SoLuongTon;
            document.getElementById("DinhMucTonKho").value = data.DinhMucTonKho;

            editingId = id;
            
            // TỰ ĐỘNG ĐIỀN XUỐNG CẢ FORM NHẬP KHO CHO TIỆN
            document.getElementById("ImportId").value = id; 
        });
}

function loadIngredientStock() {

    const id = document.getElementById("ImportId").value;

    if (!id) return;

    fetch("/inventory/" + id)
        .then(r => r.json())
        .then(data => {

            document.getElementById("CurrentStock").value =
                data.SoLuongTon;
        });
}

function importInventory() {

    const maNL = document.getElementById("ImportId").value;
    const soLuong = Number(document.getElementById("SoLuongNhap").value);
    const giaNhap = Number(document.getElementById("GiaNhap").value);

    const nhaCungCap =
        document.getElementById("NhaCungCap").value;

    const ngayNhap =
        document.getElementById("NgayNhap").value;

    const ghiChu =
        document.getElementById("GhiChuNhap").value;

    if (!maNL) {
        alert("Chưa chọn nguyên liệu");
        return;
    }

    if (soLuong <= 0) {
        alert("Số lượng nhập phải lớn hơn 0");
        return;
    }

    if (giaNhap <= 0) {
        alert("Giá nhập phải lớn hơn 0");
        return;
    }

    fetch("/inventory/import/" + maNL, {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            SoLuong: soLuong,
            GiaNhap: giaNhap,
            NhaCungCap: nhaCungCap,
            NgayNhap: ngayNhap,
            GhiChu: ghiChu
        })
    })
    .then(r => r.json().then(data => ({
        ok: r.ok,
        data
    })))
    .then(res => {

        if (!res.ok)
            throw new Error(res.data.message);

        alert(res.data.message);

        loadInventory();
    })
    .catch(err => alert(err.message));
}

function loadCheckInventory() {

    const id =
        document.getElementById("CheckMaNL").value;

    fetch("/inventory/" + id)
        .then(r => r.json())
        .then(data => {

            document.getElementById("HeThongTon").value =
                data.SoLuongTon;
        });
}

function kiemKho() {

    const maNL =
        document.getElementById("CheckMaNL").value;

    const soLuongThucTe =
        Number(document.getElementById("SoLuongThucTe").value);

    fetch("/inventory/check/" + maNL, {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            SoLuongThucTe: soLuongThucTe
        })
    })
    .then(r => r.json().then(data => ({
        ok: r.ok,
        data
    })))
    .then(res => {

        if (!res.ok)
            throw new Error(res.data.message);

        alert(res.data.message);

        loadInventory();
    })
    .catch(err => alert(err.message));
}