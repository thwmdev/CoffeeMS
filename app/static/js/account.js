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

                <button
                    class="btn btn-danger btn-sm"
                    onclick="deleteAccount(${acc.MaTK})">
                    Xóa
                </button>

                <button
                    class="btn btn-danger btn-sm"
                    onclick="resetPassword(${acc.MaTK})">
                    Reset MK
                </button>

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

    const res = await fetch("/account/create", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
    });

    const result = await res.json();

    alert(result.message);

    loadAccounts();
}
async function activateAccount(id) {

    await fetch(`/account/activate/${id}`, {
        method: "PUT"
    });

    loadAccounts();
}
async function resetPassword(id) {

    const password = prompt("Nhập mật khẩu mới:");

    if (!password) return;

    await fetch(`/account/reset-password/${id}`, {

        method: "PUT",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            password
        })
    });

    alert("Đặt lại mật khẩu thành công");
}
async function deleteAccount(id) {

    const ok = confirm("Bạn có chắc muốn xóa tài khoản này không?");

    if (!ok) return;

    const res = await fetch(`/account/delete/${id}`, {
        method: "DELETE"
    });

    const result = await res.json();

    alert(result.message);

    loadAccounts();
}
function logout() {
 localStorage.removeItem("token");
    window.location.href = "/";
}