<?php
$page_title = "客戶管理";
require __DIR__ . "/../includes/header.php";
require __DIR__ . "/../includes/sidebar.php";
?>
<main class="main">
    <div class="page-header">
        <h1>客戶管理</h1>
        <button class="btn" onclick="openCreateModal()">+ 新增客戶</button>
    </div>
    <div class="error-box" id="errBox"></div>

    <div class="card">
        <table>
            <thead><tr>
                <th>客戶編號</th>
                <th>公司名稱</th>
                <th>聯絡人</th>
                <th>電話</th>
                <th>負責職員編號</th>
                <th>操作</th></tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <div class="card" id="formCard" style="display:none;">
        <h3 id="formTitle">新增客戶</h3>
        <form id="dataForm">
            <input type="hidden" name="cust_id">
            <div class="form-grid">
                <div class="form-group"><label>公司名稱</label><input type="text" name="co_name" required></div>
                <div class="form-group"><label>聯絡人（選填）</label><input type="text" name="contact_name"></div>
                <div class="form-group"><label>電話</label><input type="text" name="phone" required></div>
                <div class="form-group"><label>負責職員編號 (CS-XXXXXX)</label><input type="text" name="staff_no" id="StaffNotInput" required></div>
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
const is_admin = <?= ($_SESSION["role"] ?? "") === "admin"?"true":"false" ?>;

function showError(msg){ 
    errBox.textContent = msg; 
    errBox.style.display = "block"; 
}

async function loadList() {
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/cust`, { 
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
        rows.forEach(c => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${c.cust_no}</td>
                <td>${c.co_name}</td>
                <td>${c.contact_name ?? "-"}</td>
                <td>${c.phone}</td>
                <td>${c.staff_no}</td>
                <td><button class="btn btn-outline" onclick='openEditModal(${JSON.stringify(c)})'>編輯</button></td>`;
            tbody.appendChild(tr);
        });
    } catch (e) { showError("無法載入客戶清單"); }
}

function openCreateModal() {
    document.getElementById("formTitle").textContent = "新增客戶";
    document.getElementById("dataForm").reset();
    document.querySelector('[name="cust_id"]').value = "";
    document.getElementById("StaffNotInput").disabled = false;
    document.getElementById("formCard").style.display = "block";
}

function openEditModal(c) {
    document.getElementById("formTitle").textContent = `編輯客戶 ${c.cust_no}`;
    document.querySelector('[name="cust_id"]').value = c.cust_id;
    document.querySelector('[name="co_name"]').value = c.co_name;
    document.querySelector('[name="contact_name"]').value = c.contact_name ?? "";
    document.querySelector('[name="phone"]').value = c.phone;
    document.querySelector('[name="staff_no"]').value = c.staff_no;
    document.getElementById("StaffNotInput").disabled = !is_admin;
    document.getElementById("formCard").style.display = "block";
}

function closeFormModal() { 
    document.getElementById("formCard").style.display = "none"; 
}

document.getElementById("dataForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    errBox.style.display = "none";
    const form_data = new FormData(e.target);
    const cust_id = form_data.get("cust_id");
    const info = { 
        co_name: form_data.get("co_name"), 
        phone: form_data.get("phone"),
        staff_no: form_data.get("staff_no")
    };
    if (cust_id) {
        info.contact_name = form_data.get("contact_name");
    } else if (form_data.get("contact_name")) {
        info.contact_name = form_data.get("contact_name");
    }
    
    const url = cust_id ? `${API_BASE}/cust/${cust_id}` : `${API_BASE}/cust`;
    const method = cust_id ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method, 
            headers: { "Content-Type": "application/json" },
            credentials: "include", 
            body: JSON.stringify(info)
        });
        const data = await res.json();

        if (!res.ok) { 
            showError(data.error || "操作失敗"); 
            return; }
            
        closeFormModal();
        loadList();
    } catch (err) { showError("無法連線到伺服器"); }
});

loadList();
</script>
<?php require __DIR__ . "/../includes/footer.php"; ?>