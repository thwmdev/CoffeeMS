let editingId = null;
let menuData = [];


// =========================
// LOAD MENU
// =========================
function loadMenu() {

    fetch("/menu/api")

        .then(res => {

            if (!res.ok) {
                throw new Error("Không thể tải menu");
            }

            return res.json();
        })

        .then(data => {

            menuData = data;

            // THỐNG KÊ
            const total = data.length;

            const active = data.filter(
                item => item.TrangThai === "ACTIVE"
            ).length;

            const inactive = data.filter(
                item => item.TrangThai === "INACTIVE"
            ).length;

            // UPDATE CARD
            document.getElementById("totalMenu").innerText = total;

            document.getElementById("activeMenu").innerText = active;

            document.getElementById("inactiveMenu").innerText = inactive;

            // RENDER TABLE
            renderMenu(data);
        })

        .catch(error => {

            console.log(error);

            alert("Lỗi tải menu");
        });
}


// AUTO LOAD
loadMenu();


// =========================
// RENDER TABLE
// =========================
function renderMenu(data) {

    let html = "";

    data.forEach(item => {

        html += `
        <tr>

            <td>${item.MaMon}</td>

            <td>${item.TenMon}</td>

            <td>${Number(item.GiaBan).toLocaleString()} đ</td>

            <td>${item.MoTa || ""}</td>

            <td>${item.TenDanhMuc}</td>

            <td>

                <span class="${
                    item.TrangThai === "ACTIVE"
                    ? "active"
                    : "inactive"
                }">

                    ${item.TrangThai}

                </span>

            </td>

            <td class="d-flex gap-2">

                <button
                    class="btn btn-warning btn-sm"
                    onclick="editMenu(${item.MaMon})"
                >
                    Sửa
                </button>

                <button
                    class="btn btn-danger btn-sm"
                    onclick="deleteMenu(${item.MaMon})"
                >
                    Xóa
                </button>

                <button
                    class="btn btn-dark btn-sm"
                    onclick="
                        toggleStatus(
                            ${item.MaMon},
                            '${item.TrangThai}'
                        )
                    "
                >
                    Bật/Tắt
                </button>

            </td>

        </tr>
        `;
    });

    document.getElementById("menuTable").innerHTML = html;
}


// =========================
// LẤY DỮ LIỆU FORM
// =========================
function getFormData() {

    return {

        TenMon: document
            .getElementById("TenMon")
            .value
            .trim(),

        GiaBan: parseFloat(
            document.getElementById("GiaBan").value
        ),

        MoTa: document
            .getElementById("MoTa")
            .value
            .trim(),

        TrangThai: document
            .getElementById("TrangThai")
            .value,

        MaDM: parseInt(
            document.getElementById("MaDM").value
        )
    };
}


// =========================
// RESET FORM
// =========================
function resetForm() {

    document.getElementById("TenMon").value = "";

    document.getElementById("GiaBan").value = "";

    document.getElementById("MoTa").value = "";

    document.getElementById("TrangThai").value = "ACTIVE";

    document.getElementById("MaDM").value = "";

    editingId = null;

    // REMOVE ERROR
    const oldError = document.getElementById("formError");

    if (oldError) {
        oldError.remove();
    }

    document
        .querySelectorAll(".input-error")
        .forEach(el => {
            el.classList.remove("input-error");
        });
}


// =========================
// VALIDATE FORM
// =========================
function validateForm() {

    let isValid = true;

    const tenMon =
        document.getElementById("TenMon");

    const giaBan =
        document.getElementById("GiaBan");

    // RESET ERROR
    tenMon.classList.remove("input-error");

    giaBan.classList.remove("input-error");

    // XÓA ERROR CŨ
    const oldError =
        document.getElementById("formError");

    if (oldError) {
        oldError.remove();
    }

    // VALIDATE TÊN
    if (tenMon.value.trim() === "") {

        tenMon.classList.add("input-error");

        isValid = false;
    }

    // VALIDATE GIÁ
    if (
        giaBan.value.trim() === "" ||
        Number(giaBan.value) <= 0
    ) {

        giaBan.classList.add("input-error");

        isValid = false;
    }

    // SHOW ERROR
    if (!isValid) {

        const error =
            document.createElement("div");

        error.id = "formError";

        error.className =
            "error-text mt-3 text-danger fw-bold";

        error.innerText =
            "Tên món không được để trống và giá bán phải lớn hơn 0";

        document
            .querySelector(".form-box")
            .appendChild(error);
    }

    return isValid;
}


// =========================
// THÊM MÓN
// =========================
function addMenu() {

    if (!validateForm()) {
        return;
    }

    if (!confirm("Bạn có chắc muốn thêm món này?")) {
        return;
    }

    const data = getFormData();

    fetch("/menu/add", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(data)
    })

    .then(async res => {

        const result = await res.json();

        if (!res.ok) {
            throw new Error(result.message);
        }

        return result;
    })

    .then(result => {

        alert(result.message);

        loadMenu();

        resetForm();
    })

    .catch(error => {

        console.log(error);

        alert(error.message);
    });
}


// =========================
// CHỌN MÓN ĐỂ SỬA
// =========================
function editMenu(id) {

    fetch("/menu/" + id)

        .then(res => {

            if (!res.ok) {
                throw new Error("Không tìm thấy món");
            }

            return res.json();
        })

        .then(data => {

            document.getElementById("TenMon").value =
                data.TenMon;

            document.getElementById("GiaBan").value =
                data.GiaBan;

            document.getElementById("MoTa").value =
                data.MoTa || "";

            document.getElementById("TrangThai").value =
                data.TrangThai;

            document.getElementById("MaDM").value =
                data.MaDM;

            editingId = Number(data.MaMon);

            console.log("Editing ID =", editingId);
        })

        .catch(error => {

            console.log(error);

            alert("Lỗi lấy dữ liệu món");
        });
}


// =========================
// CẬP NHẬT MÓN
// =========================
function updateMenu() {

    if (!validateForm()) {
        return;
    }

    if (editingId === null) {

        alert("Vui lòng chọn món cần sửa");

        return;
    }

    if (!confirm("Bạn có chắc muốn cập nhật món này?")) {
        return;
    }

    const data = getFormData();

    console.log("UPDATE ID =", editingId);

    console.log("DATA =", data);

    fetch("/menu/update/" + editingId, {

        method: "PUT",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(data)
    })

    .then(async res => {

        const result = await res.json();

        if (!res.ok) {
            throw new Error(result.message);
        }

        return result;
    })

    .then(result => {

        alert(result.message);

        loadMenu();

        resetForm();
    })

    .catch(error => {

        console.log(error);

        alert(error.message);
    });
}


// =========================
// XÓA MÓN
// =========================
function deleteMenu(id) {

    if (!confirm("Bạn có chắc muốn xóa món này?")) {
        return;
    }

    fetch("/menu/delete/" + id, {

        method: "DELETE"
    })

    .then(async res => {

        const result = await res.json();

        if (!res.ok) {
            throw new Error(result.message);
        }

        return result;
    })

    .then(result => {

        alert(result.message);

        loadMenu();
    })

    .catch(error => {

        console.log(error);

        alert(error.message);
    });
}


// =========================
// BẬT/TẮT TRẠNG THÁI
// =========================
function toggleStatus(id, currentStatus) {

    const newStatus =
        currentStatus === "ACTIVE"
        ? "INACTIVE"
        : "ACTIVE";

    fetch("/menu/" + id)

        .then(res => res.json())

        .then(oldData => {

            const updatedData = {

                TenMon: oldData.TenMon,

                GiaBan: oldData.GiaBan,

                MoTa: oldData.MoTa,

                MaDM: oldData.MaDM,

                TrangThai: newStatus
            };

            return fetch("/menu/update/" + id, {

                method: "PUT",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(updatedData)
            });
        })

        .then(async res => {

            const result = await res.json();

            if (!res.ok) {
                throw new Error(result.message);
            }

            return result;
        })

        .then(result => {

            alert(result.message);

            loadMenu();
        })

        .catch(error => {

            console.log(error);

            alert(error.message);
        });
}


// =========================
// TÌM KIẾM / LỌC
// =========================
function searchMenu() {

    const keyword = document
        .getElementById("searchKeyword")
        .value
        .toLowerCase();

    const category = document
        .getElementById("searchCategory")
        .value
        .toLowerCase();

    const status = document
        .getElementById("searchStatus")
        .value;

    const minPrice = parseFloat(
        document.getElementById("minPrice").value
    ) || 0;

    const maxPrice = parseFloat(
        document.getElementById("maxPrice").value
    ) || Infinity;

    const filtered = menuData.filter(item => {

        const matchKeyword =

            item.TenMon
                .toLowerCase()
                .includes(keyword)

            ||

            item.MaMon
                .toString()
                .includes(keyword);

        const matchCategory =

            item.TenDanhMuc
                .toLowerCase()
                .includes(category);

        const matchStatus =

            status === ""
            ||
            item.TrangThai === status;

        const matchPrice =

            item.GiaBan >= minPrice
            &&
            item.GiaBan <= maxPrice;

        return (

            matchKeyword
            &&
            matchCategory
            &&
            matchStatus
            &&
            matchPrice
        );
    });

    renderMenu(filtered);
}