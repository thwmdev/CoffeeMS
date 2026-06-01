function getCookie(name) {
    let cookies = document.cookie.split(";");
    for (let c of cookies) {
        let cookie = c.trim();
        if (cookie.startsWith(name + "=")) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return null;
}

function login() {
    const userField = document.getElementById("username");
    const passField = document.getElementById("password");
    const msgField = document.getElementById("msg");

    if (!userField || !passField) return;

    const username = userField.value.trim();
    const password = passField.value.trim();

    if (!username || !password) {
        if (msgField) msgField.innerText = "Vui lòng nhập đầy đủ thông tin!";
        return;
    }

    fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => { throw new Error(err.message || "Đăng nhập thất bại"); });
        }
        return res.json();
    })
    .then(data => {
        const userRole = data.role ? data.role.toUpperCase() : "";

        localStorage.setItem("user", JSON.stringify({
            username: username,
            role: userRole
        }));

        document.cookie = `role=${userRole}; path=/; max-age=86400`;
        document.cookie = `token=${data.token}; path=/; max-age=86400`;

        if (userRole === "NHANVIEN") {
            window.location.href = "/order";
        } else if (userRole === "ADMIN") {
            window.location.href = "/menu";
        }
    })
    .catch(err => {
        if (msgField) msgField.innerText = err.message;
    });
}


document.addEventListener("DOMContentLoaded", () => {
    const rawRole = getCookie("role");
    const role = rawRole ? rawRole.toUpperCase() : "";

    // Chỉ ADMIN thấy: Kho, Công thức, Báo cáo
    const adminModules = ["inventoryModule", "recipeModule", "reportModule", 'accountModule'];

    // Cả NHANVIEN và ADMIN đều thấy: Thanh toán, Gọi Món
    const staffModules  = ["paymentModule", "orderModule"];

    if (role === "NHANVIEN") {
        adminModules.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = "none";
        });
        staffModules.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = "block";
        });

    } else if (role === "ADMIN") {
        adminModules.forEach(id => {
            document.getElementById(id)?.style.setProperty("display", "block");
        });

        staffModules.forEach(id => {
            document.getElementById(id)?.style.setProperty("display", "none");
        });

    } else {
        // Chưa đăng nhập: ẩn tất cả
        adminModules.concat(staffModules).forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = "none";
        });
    }

    document.querySelector(".sidebar-menu").style.visibility = "visible";
});

function logout() {
    if (confirm("Bạn có chắc chắn muốn đăng xuất không?")) {
        document.cookie = "role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        
        localStorage.removeItem("user");
        
        window.location.href = "/";
    }
}
