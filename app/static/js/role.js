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
        
        document.cookie = `role=${userRole}; path=/; max-age=86400`;
        document.cookie = `token=${data.token}; path=/; max-age=86400`;
        // alert("Đăng nhập thành công!");

        if (userRole === "NHANVIEN") {
            window.location.href = "/menu"; 
        } else if (userRole === "ADMIN") {
            window.location.href = "/inventory"; 
        }
    })
    .catch(err => {
        if (msgField) msgField.innerText = err.message;
    });
}


document.addEventListener("DOMContentLoaded", () => {
    const rawRole = getCookie("role");
    const role = rawRole ? rawRole.toUpperCase() : "";

    const adminModules = ["inventoryModule", "recipeModule", "reportModule"];
    const staffModules = ["paymentModule"];

    if (role === "NHANVIEN") {



        adminModules.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = "none";
        });
        staffModules.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = "block";
        });
    } else if (role === "ADMIN") {


        adminModules.concat(staffModules).forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = "block";
        });
    } else {
        adminModules.concat(staffModules).forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = "none";
        });
    }
});

function logout() {
    if (confirm("Bạn có chắc chắn muốn đăng xuất không?")) {


        document.cookie = "role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        
        
        
        window.location.href = "/";
    }
}
