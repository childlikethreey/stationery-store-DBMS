<?php
$page_title = "供應商管理";
require __DIR__ . "/../includes/header.php";
require __DIR__ . "/../includes/sidebar.php";
?>
<main class="main">
    <div class="page-header">
        <h1>供應商管理</h1>
        <button class="btn" onclick="openCreateModal()">+ 新增供應商</button>
    </div>
    <div class="error-box" id="errBox"></div>

    <div class="card">
        <table>
            <thead>
                <tr>
                    <th>供應商編號</th>
                    <th>公司名稱</th>
                    <th>聯絡人</th>
                    <th>電話</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <div class="card" id="formCard" style="display:none;">
        <h3 id="formTitle">新增供應商</h3>
        <form id="dataForm">
            <input type="hidden" name="sup_id">
            <div class="form-grid">
                <div class="form-group"><label>公司名稱</label><input type="text" name="co_name" required></div>
                <div class="form-group"><label>聯絡人（選填）</label><input type="text" name="contact_name"></div>
                <div class="form-group"><label>電話</label><input type="text" name="phone" required></div>
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
function showError(msg){ 
    errBox.textContent = msg; 
    errBox.style.display = "block"; 
}

async function loadList() {
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/sup`, { 
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
                <td>${s.sup_id}</td>
                <td>${s.co_name}</td>
                <td>${s.contact_name ?? "-"}</td>
                <td>${s.phone}</td>
                <td><button class="btn btn-outline" onclick='openEditModal(${JSON.stringify(s)})'>編輯</button></td>`;
            tbody.appendChild(tr);
        });
    } catch (e) { 
        showError("無法載入供應商清單"); 
    }
}

function openCreateModal() {
    document.getElementById("formTitle").textContent = "新增供應商";
    document.getElementById("dataForm").reset();
    document.querySelector('[name="sup_id"]').value = "";
    document.getElementById("formCard").style.display = "block";
}

function openEditModal(s) {
    document.getElementById("formTitle").textContent = `編輯供應商 #${s.sup_id}`;
    document.querySelector('[name="sup_id"]').value = s.sup_id;
    document.querySelector('[name="co_name"]').value = s.co_name;
    document.querySelector('[name="contact_name"]').value = s.contact_name ?? "";
    document.querySelector('[name="phone"]').value = s.phone;
    document.getElementById("formCard").style.display = "block";
}

function closeFormModal() { 
    document.getElementById("formCard").style.display = "none"; 
}

document.getElementById("dataForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    errBox.style.display = "none";
    const fd = new FormData(e.target);
    const sup_id = fd.get("sup_id");
    const payload = { 
        co_name: fd.get("co_name"), 
        phone: fd.get("phone") 
    };
    if (sup_id) {
        payload.contact_name = fd.get("contact_name");
    }
    else if (fd.get("contact_name")) {
        payload.contact_name = fd.get("contact_name");
    }

    const url = sup_id ? `${API_BASE}/sup/${sup_id}` : `${API_BASE}/sup`;
    const method = sup_id ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method, 
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) { 
            showError(data.eror || "操作失敗"); 
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