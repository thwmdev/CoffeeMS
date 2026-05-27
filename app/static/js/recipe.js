/* Biến toàn cục quản lý trạng thái ứng dụng */
let editingMaMon = null; /* Lưu Mã Món gốc khi người dùng ấn "Sửa" */
let editingMaNL = null;  /* Lưu Mã Nguyên liệu gốc khi người dùng ấn "Sửa" */
let allRecipes = [];    /* Lưu trữ danh sách gốc phục vụ cho việc tìm kiếm bộ lọc nhanh */

// Tự động tải danh sách công thức khi trang được load xong
document.addEventListener("DOMContentLoaded", () => {
    loadRecipes();
});

// ==========================================
// 1. TẢI TOÀN BỘ DANH SÁCH CÔNG THỨC (GET /recipe/recipes)
// ==========================================
function loadRecipes() {
    fetch("/recipe/recipes")
        .then(response => response.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            allRecipes = data;
            
            const totalBadge = document.getElementById("totalRecipes");
            if (totalBadge) totalBadge.innerText = data.length;
            
            renderRecipeTable(data);
        })
        .catch(error => {
            console.error("Lỗi khi tải danh sách công thức:", error);
            alert("Không thể tải danh sách công thức từ máy chủ.");
        });
}

// ==========================================
// 2. HIỂN THỊ DỮ LIỆU LÊN BẢNG HTML
// ==========================================
// ==========================================
// 2. HIỂN THỊ DỮ LIỆU LÊN BẢNG HTML
// ==========================================
function renderRecipeTable(recipes) {
    const tableBody = document.getElementById("recipeTable");
    if (!tableBody) return;

    let html = "";
    if (recipes.length === 0) {
        html = `<tr><td colspan="9" class="text-center text-muted">Không tìm thấy công thức nào.</td></tr>`;
    } else {
        recipes.forEach((item, index) => {
            // Tính số lượng phần ăn có thể phục vụ dựa trên Nguyên Liệu này
            const soPhan = Math.floor(item.SoLuongTon / item.SoLuongSuDung);
            
            // Trang trí màu sắc: Hết hàng hiện đỏ, còn hàng hiện xanh lá
            const khaDungBadge = soPhan > 0 
                ? `<span class="text-success fw-bold">${soPhan} phần</span>`
                : `<span class="text-danger fw-bold">Hết hàng</span>`;

            html += `
            <tr>
                <td><strong>${index + 1}</strong></td>
                <td><span class="badge bg-secondary">#${item.MaMon}</span></td>
                <td class="fw-bold text-dark">${item.TenMon}</td>
                <td>${item.MaNL}</td>
                <td>${item.TenNL}</td>
                <td class="text-primary fw-bold">${item.SoLuongSuDung}</td>
                <td>${item.DonViTinh}</td>
                <td>${khaDungBadge}</td> <td>
                    <div class="d-flex gap-2">
                        <button class="btn btn-warning btn-sm" onclick="editRecipe(${item.MaMon}, ${item.MaNL}, ${item.SoLuongSuDung})">Sửa</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteRecipe(${item.MaMon}, ${item.MaNL})">Xóa</button>
                    </div>
                </td>
            </tr>
            `;
        });
    }
    tableBody.innerHTML = html;
}

// ==========================================
// 3. THÊM CÔNG THỨC MỚI (POST /recipe/recipes)
// ==========================================
function addRecipe() {
    const maMon = document.getElementById("MaMon").value.trim();
    const maNL = document.getElementById("MaNL").value.trim();
    const soLuong = document.getElementById("SoLuongSuDung").value.trim();

    if (!maMon || !maNL || !soLuong) {
        alert("Vui lòng điền đầy đủ thông tin: Mã Món, Mã NL và Số lượng sử dụng!");
        return;
    }

    const payload = {
        MaMon: parseInt(maMon),
        ingredients: [
            {
                MaNL: parseInt(maNL),
                SoLuongSuDung: parseFloat(soLuong)
            }
        ]
    };

    fetch("/recipe/recipes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Lỗi: Không thể thêm do trùng lặp hoặc sai dữ liệu!");
        } else {
            alert(data.message);
            resetForm();
            loadRecipes();
        }
    })
    .catch(error => {
        console.error("Lỗi khi thêm công thức:", error);
        alert("Đã xảy ra lỗi trong quá trình thêm công thức mới.");
    });
}

// ==========================================
// 4. CHUẨN BỊ DỮ LIỆU ĐỂ SỬA
// ==========================================
function editRecipe(maMon, maNL, soLuong) {
    editingMaMon = maMon;
    editingMaNL = maNL;
    
    document.getElementById("MaMon").value = maMon;
    document.getElementById("MaNL").value = maNL;
    document.getElementById("SoLuongSuDung").value = soLuong;

    document.getElementById("MaMon").disabled = true;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==========================================
// 5. CẬP NHẬT CÔNG THỨC (PUT /recipe/recipes/<ma_mon>/<ma_nl_cu>)
// ==========================================
function updateRecipe() {
    if (!editingMaMon || !editingMaNL) {
        alert("Vui lòng chọn một công thức từ danh sách bên dưới bằng nút 'Sửa' trước.");
        return;
    }

    const maNL = document.getElementById("MaNL").value.trim();
    const soLuong = document.getElementById("SoLuongSuDung").value.trim();

    if (!maNL || !soLuong) {
        alert("Không được để trống Mã nguyên liệu và Số lượng tiêu hao!");
        return;
    }

    const payload = {
        MaNL: parseInt(maNL),
        SoLuongSuDung: parseFloat(soLuong)
    };

    fetch(`/recipe/recipes/${editingMaMon}/${editingMaNL}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if(data.error) {
            alert("Lỗi cập nhật: " + data.error);
        } else {
            alert(data.message);
            resetForm();
            loadRecipes();
        }
    })
    .catch(error => {
        console.error("Lỗi khi cập nhật công thức:", error);
        alert("Không thể cập nhật thông tin thay đổi.");
    });
}

// ==========================================
// 6. XÓA CÔNG THỨC (DELETE /recipe/recipes/<ma_mon>/<ma_nl>)
// ==========================================
function deleteRecipe(maMon, maNL) {
    if (!confirm(`Bạn có chắc chắn muốn xóa nguyên liệu #${maNL} khỏi món #${maMon} không?`)) return;

    fetch(`/recipe/recipes/${maMon}/${maNL}`, {
        method: "DELETE"
    })
    .then(response => response.json())
    .then(data => {
        if(data.error) {
            alert("Lỗi xóa: " + data.error);
        } else {
            alert(data.message);
            loadRecipes();
        }
    })
    .catch(error => {
        console.error("Lỗi khi xóa công thức:", error);
        alert("Xảy ra lỗi hệ thống khi thực hiện lệnh xóa.");
    });
}

// ==========================================
// 7. KIỂM TRA KHẢ NĂNG PHỤC VỤ (GET /recipe/menu/<ma_mon>/availability)
// ==========================================
function checkAvailability() {
    const checkMaMon = document.getElementById("CheckMaMon").value.trim();
    if (!checkMaMon) {
        alert("Vui lòng điền mã món cần tính toán tính khả dụng kho!");
        return;
    }

    const resultDiv = document.getElementById("availabilityResult");
    if (!resultDiv) return;

    fetch(`/recipe/menu/${checkMaMon}/availability`)
        .then(response => response.json())
        .then(data => {
            resultDiv.style.display = "block";

            if (data.message && !data.ChiTiet) {
                resultDiv.innerHTML = `<h5 class="text-danger mb-0">${data.message}</h5>`;
                return;
            }

            const isAvailable = data.TrangThai === "CONBAN";
            const badgeClass = isAvailable ? "bg-success" : "bg-danger";
            const textClass = isAvailable ? "text-success" : "text-danger";

            let htmlOutput = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h4 class="text-dark mb-0">Món: <span class="text-primary">${data.TenMon}</span></h4>
                    <span class="badge ${badgeClass} fs-6">${data.TrangThai}</span>
                </div>
                <p class="fs-5 mb-3">Khả năng cung ứng tối đa: <strong class="${textClass}">${data.SoPhanConLai} suất</strong></p>
                
                <h6 class="fw-bold text-secondary mb-2">Phân tích tồn kho nguyên liệu:</h6>
                <div class="table-responsive border rounded">
                    <table class="table table-sm table-hover text-center align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th class="text-start">Nguyên Liệu</th>
                                <th>Tồn Kho</th>
                                <th>Định Mức / Suất</th>
                                <th>Khả Dụng</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            data.ChiTiet.forEach(item => {
                const isLimitFactor = item.PhucVuDuoc === data.SoPhanConLai;
                const rowHighlight = isLimitFactor ? "text-danger fw-bold" : "fw-medium";
                
                htmlOutput += `
                    <tr>
                        <td class="text-start fw-bold text-secondary">${item.NguyenLieu}</td>
                        <td>${Number(item.TonKho).toLocaleString()}</td>
                        <td>${item.CanDung}</td>
                        <td class="${rowHighlight}">${item.PhucVuDuoc} phần</td>
                    </tr>
                `;
            });

            htmlOutput += `
                        </tbody>
                    </table>
                </div>
            `;

            resultDiv.innerHTML = htmlOutput;
        })
        .catch(error => {
            console.error("Lỗi tính toán khả năng phục vụ:", error);
            alert("Đã xảy ra lỗi trong quá trình kết nối và phân tích dữ liệu tồn kho.");
        });
}

// ==========================================
// 8. TÌM KIẾM VÀ LỌC DỮ LIỆU TẠI CHỖ (OFFLINE)
// ==========================================
function searchRecipe() {
    const keyword = document.getElementById("searchKeyword").value.toLowerCase().trim();
    const filterMaMon = document.getElementById("searchMaMon").value.trim();

    const filtered = allRecipes.filter(item => {
        const matchesKeyword = item.TenMon.toLowerCase().includes(keyword) || 
                               item.TenNL.toLowerCase().includes(keyword);
        const matchesMaMon = filterMaMon === "" || item.MaMon == filterMaMon;
        return matchesKeyword && matchesMaMon;
    });

    renderRecipeTable(filtered);
}

// ==========================================
// 9. LÀM SẠCH FORM TRẠNG THÁI KHỞI TẠO
// ==========================================
function resetForm() {
    editingMaMon = null;
    editingMaNL = null;
    document.getElementById("MaMon").value = "";
    document.getElementById("MaNL").value = "";
    document.getElementById("SoLuongSuDung").value = "";
    document.getElementById("MaMon").disabled = false;
}