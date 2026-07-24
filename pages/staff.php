<?php
$page_title = "職員管理";
require __DIR__ . "/../includes/header.php";
if (($_SESSION["role"] ?? "") !== "admin") {
    echo "<main class='main'><div class='error-box' style='display:block;'>只有管理員可以存取此頁面</div></main>";
    require __DIR__ . "/../includes/footer.php";
    exit;
}
require __DIR__ . "/../includes/sidebar.php";
?>

<main class="main">
    <div class="page-header">
        <h1>職員管理</h1>
        <button class="btn" onclick="openCreateModal()">+ 新增職員</button>
    </div>
    <div class="error-box" id="errBox"></div>

    <div class="card">
        <table>
            <thead>
                <tr>
                    <th>職員編號</th>
                    <th>姓名</th>
                    <th>部門</th>
                    <th>電話</th>
                    <th>在職</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <div class="card" id="formCard" style="display:none;">
        <h3 id="formTitle">新增職員</h3>
        <form id="dataForm">
            <input type="hidden" name="staff_id">
            <div class="form-grid">
                <div class="form-group"><label>姓名</label><input type="text" name="name" required></div>
                <div class="form-group">
                    <label>部門</label>
                    <select name="dept" required>
                        <option value="CS">CS</option>
                        <option value="管理層">管理層</option>
                        <option value="清潔部門">清潔部門</option>
                    </select>
                </div>
                <div class="form-group"><label>電話（選填）</label><input type="text" name="phone"></div>
                <div class="form-group">
                    <label>在職狀態</label>
                    <select name="is_active" id="CreateNoNeed" required>
                        <option value="true">在職</option>
                        <option value="false">離職</option>
                    </select>
                </div>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn">送出</button>
                <button type="button" class="btn btn-outline" onclick="closeFormModal()">取消</button>
            </div>
        </form>
    </div>
</main>

<script>
const API_BASE = "<?= $API_BASE ?>";
const errBox = document.getElementById("errBox");
function showError(msg){ errBox.textContent = msg; errBox.style.display = "block"; }

async function loadList() {
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/staff`, { 
            method: "GET",
            credentials: "include" 
        });
        
        if (res.status === 401) { 
            window.location.href = "/pages/login.php"; 
            return; 
        }
        
        const rows = await res.json();
        const tbody = document.getElementById("tableBody");
        tbody.innerHTML = "";
        rows.forEach(s => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${s.staff_no}</td>
                <td>${s.name}</td>
                <td>${s.dept}</td>
                <td>${s.phone ?? "-"}</td>
                <td>${s.is_active ? "在職" : "離職"}</td>
                <td>
                    <button class="btn btn-outline" onclick='openEditModal(${JSON.stringify(s)})'>編輯</button>
                    <button class="btn btn-outline" onclick="createAccount(${s.staff_id})">建立帳號</button>
                </td>`;
            tbody.appendChild(tr);
        });
    } catch (e) { 
        showError("無法載入職員清單"); 
    }
}

async function createAccount(staff_id) {
    const role = prompt("請輸入角色（admin 或 staff）：", "staff");
    if (!role) return;
    errBox.style.display = "none";
    
    try {
        const res = await fetch(`${API_BASE}/staff/${staff_id}/account`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include", 
            body: JSON.stringify({role})
        });
        const data = await res.json();
        
        if (!res.ok) { 
            showError(data.error || "建立失敗"); 
            return; 
        }
        
        alert(`帳號建立成功，請提醒職員修改密碼\n職員編號：${data.staff_no}\n初始密碼：${data.password}`);
    } catch (e) { 
        showError("無法連線到伺服器"); 
    }
}

function openCreateModal() {
    document.getElementById("formTitle").textContent = "新增職員";
    document.getElementById("dataForm").reset();
    document.querySelector('[name="staff_id"]').value = "";
    document.getElementById("CreateNoNeed").closest(".form-group").style.display = "none";
    document.getElementById("formCard").style.display = "block";
}

function openEditModal(s) {
    document.getElementById("formTitle").textContent = `編輯職員 ${s.staff_no}`;
    document.querySelector('[name="staff_id"]').value = s.staff_id;
    document.querySelector('[name="name"]').value = s.name;
    document.querySelector('[name="dept"]').value = s.dept;
    document.querySelector('[name="phone"]').value = s.phone ?? "";
    document.getElementById("CreateNoNeed").closest(".form-group").style.display = "";
    document.querySelector('[name="is_active"]').value = s.is_active ? "true" : "false";
    document.getElementById("formCard").style.display = "block";
}

function closeFormModal() { 
    document.getElementById("formCard").style.display = "none"; 
}

document.getElementById("dataForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    errBox.style.display = "none";
    const fd = new FormData(e.target);
    const staff_id = fd.get("staff_id");
    const payload = { 
        name: fd.get("name"), 
        dept: fd.get("dept"), 
        is_active: fd.get("is_active") === "true" };
    if (staff_id) {
        payload.phone = fd.get("phone");
    }
    else if (fd.get("phone")) {
        payload.phone = fd.get("phone");
    }

    const url = staff_id ? `${API_BASE}/staff/${staff_id}` : `${API_BASE}/staff`;
    const method = staff_id ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method, 
            headers: { "Content-Type": "application/json" },
            credentials: "include", 
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        
        if (!res.ok) { 
            showError(data.error || "操作失敗"); 
            return; 
        }

        closeFormModal();
        loadList();
    } catch (e) { 
        showError("無法連線到伺服器"); 
    }
});

loadList();
</script>
<?php require __DIR__ . "/../includes/footer.php"; ?>