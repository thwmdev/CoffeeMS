function loadUserInfo() {

    const user = JSON.parse(localStorage.getItem("user"));

    if (!user) return;

    document.getElementById("sidebarUsername").textContent =
        user.username;

    document.getElementById("sidebarRole").textContent =
        user.role === "ADMIN"
            ? "Quản trị viên"
            : "Nhân viên";

    document.getElementById("sidebarAvatar").textContent =
        user.username.charAt(0).toUpperCase();
}

document.addEventListener("DOMContentLoaded", () => {
    loadUserInfo();
});

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("username");
    window.location.href = "/";
}

