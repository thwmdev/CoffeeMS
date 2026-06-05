let accounts = [];

window.onload = () => {
    loadAccounts();
};

async function loadAccounts() {
    const res = await fetch("/account/list");
    accounts = await res.json();
    renderAccounts();
}

function renderAccounts() {
    let html = "";
    accounts.forEach(acc => {
        html += `
        <tr>
            <td>${acc.MaNV}</td>
            <td>${acc.HoTen}</td>
            <td>${acc.SDT}</td>
            <td>${acc.Email}</td>
            <td>${acc.TenDangNhap}</td>
            <td>${acc.VaiTro}</td>
            <td>${acc.TrangThai}</td>
            <td>
                <div class="table-actions">
                    <button class="btn-table btn-edit" onclick="updateAccountInfo(${acc.MaTK})" title="Chỉnh sửa">
                        <i class="bi bi-pencil-square"></i>
                    </button>
                    <button class="btn-table btn-lock" onclick="toggleLock(${acc.MaTK})" title="Khóa/Mở khóa">
                        <i class="bi bi-lock-fill"></i>
                    </button>
                </div>
            </td>
        </tr>
        `;
    });
    document.getElementById("accountTable").innerHTML = html;
}

async function createAccount() {
    const body = {
        HoTen: document.getElementById("HoTen").value,
        SDT: document.getElementById("SDT").value,
        Email: document.getElementById("Email").value,
        TenDangNhap: document.getElementById("TenDangNhap").value,
        MatKhau: document.getElementById("MatKhau").value,
        VaiTro: document.getElementById("VaiTro").value
    };

    try {
        const res = await fetch("/account/create", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const result = await res.json();

        if (res.ok) {
            alert(result.message);
            loadAccounts();
            
            document.getElementById("HoTen").value = "";
            document.getElementById("SDT").value = "";
            document.getElementById("Email").value = "";
            document.getElementById("TenDangNhap").value = "";
            document.getElementById("MatKhau").value = "";
        } else {
            alert("Lỗi: " + result.message);
        }
    } catch (error) {
        console.error("Lỗi tạo tài khoản:", error);
        alert("Không thể kết nối tới máy chủ!");
    }
}

async function activateAccount(id) {
    await fetch(`/account/activate/${id}`, {
        method: "PUT"
    });
    loadAccounts();
}

function updateAccountInfo(id) {
    const acc = accounts.find(a => a.MaTK === id);

    document.getElementById("updateMaTK").value = acc.MaTK;
    document.getElementById("updateTenDangNhap").value = acc.TenDangNhap;
    document.getElementById("updateSDT").value = acc.SDT;
    document.getElementById("updateEmail").value = acc.Email;
    document.getElementById("updateMatKhau").value = "";

    const modal = new bootstrap.Modal(
        document.getElementById("updateModal")
    );
    modal.show();
}

async function saveAccountUpdate() {
    const id = document.getElementById("updateMaTK").value;

    const body = {
        TenDangNhap: document.getElementById("updateTenDangNhap").value,
        SDT: document.getElementById("updateSDT").value,
        Email: document.getElementById("updateEmail").value,
        VaiTro: accounts.find(a => a.MaTK == id)?.VaiTro || ""
    };

    const password = document.getElementById("updateMatKhau").value.trim();
    if (password !== "") {
        body.MatKhau = password;
    }

    try {
        const res = await fetch(`/account/update/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const result = await res.json();

        if (res.ok) {
            alert(result.message);
            bootstrap.Modal.getInstance(document.getElementById("updateModal")).hide();
            loadAccounts();
        } else {
            alert("Lỗi: " + result.message);
        }
    } catch (error) {
        console.error("Lỗi cập nhật tài khoản:", error);
        alert("Không thể kết nối tới máy chủ!");
    }
}

async function toggleLock(id) {
    const user = accounts.find(a => a.MaTK === id);

    let textConfirm = "";
    if (user.TrangThai === "HOATDONG") {
        textConfirm = "Bạn có chắc muốn khóa tài khoản này không?";
    } else {
        textConfirm = "Bạn có chắc muốn mở khóa tài khoản này không?";
    }
    const ok = confirm(textConfirm);
    if (!ok) return;

    try {
        const res = await fetch(`/account/toggle-status/${id}`, {
            method: "PUT"
        });
        const result = await res.json();
        alert(result.message);
        loadAccounts();
    } catch (error) {
        console.error("Lỗi khi thay đổi trạng thái tài khoản:", error);
        alert("Có lỗi xảy ra, vui lòng thử lại!");
    }
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}