<?php
$page_title = "貨存管理";
require __DIR__ . "/../includes/header.php";
require __DIR__ . "/../includes/sidebar.php";
$is_admin = ($_SESSION["role"] ?? "") === "admin";
?>
<main class="main">
    <div class="page-header">
        <h1>貨存管理</h1>
        <button class="btn" onclick="openCreateModal()">+ 新增貨品</button>
    </div>
    <div class="error-box" id="errBox"></div>

    <div class="card">
        <table>
            <thead><tr>
                <th>貨品編號</th>
                <th>名稱</th>
                <th>數量</th>
                <th>定價</th>
                <th>供應商</th>
                <th>停止入貨</th>
                <?php if ($is_admin): ?><th>操作</th><?php endif; ?></tr></thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <?php if ($is_admin): ?>
    <div class="card" id="formCard" style="display:none;">
        <h3 id="formTitle">新增貨品</h3>
        <form id="dataForm">
            <input type="hidden" name="goods_id">
            <div class="form-grid">
                <div class="form-group"><label>名稱</label><input type="text" name="name" required></div>
                <div class="form-group"><label>定價</label><input type="number" name="price" min="0" required></div>
                <div class="form-group"><label>供應商編號</label><input type="number" name="sup_id" min="1" required></div>
                <div class="form-group">
                    <label>停止入貨</label>
                    <select name="stop_purchase">
                        <option value="false">否</option>
                        <option value="true">是</option>
                    </select>
                </div>
            </div>
            <div class="form-actions">
                <button type="submit" class="btn">送出</button>
                <button type="button" class="btn btn-outline" onclick="closeFormModal()">取消</button>
            </div>
        </form>
    </div>
    <?php endif; ?>
</main>

<script>
const API_BASE = "<?= $API_BASE ?>";
const IS_ADMIN = <?= $is_admin ? "true" : "false" ?>;
const errBox = document.getElementById("errBox");
function showError(msg){ errBox.textContent = msg; errBox.style.display = "block"; }

async function loadList() {
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/inv`, { 
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
        rows.forEach(g => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${g.goods_id}</td><td>${g.name}</td><td>${g.quantity}</td><td>${g.price}</td>
                <td>${g.sup_id}</td><td>${g.stop_purchase ? "是" : "否"}</td>
                ${IS_ADMIN ? `<td><button class="btn btn-outline" onclick='openEditModal(${JSON.stringify(g)})'>編輯</button></td>` : ""}`;
            tbody.appendChild(tr);
        });
    } catch (e) { 
        showError("無法載入貨存清單"); 
    }
}

function openCreateModal() {
    document.getElementById("formTitle").textContent = "新增貨品";
    document.getElementById("dataForm").reset();
    document.querySelector('[name="goods_id"]').value = "";
    document.getElementById("formCard").style.display = "block";
}

function openEditModal(g) {
    document.getElementById("formTitle").textContent = `編輯貨品 #${g.goods_id}`;
    document.querySelector('[name="goods_id"]').value = g.goods_id;
    document.querySelector('[name="name"]').value = g.name;
    document.querySelector('[name="price"]').value = g.price;
    document.querySelector('[name="sup_id"]').value = g.sup_id;
    document.querySelector('[name="stop_purchase"]').value = g.stop_purchase ? "true" : "false";
    document.getElementById("formCard").style.display = "block";
}

function closeFormModal() { document.getElementById("formCard").style.display = "none"; }

if (IS_ADMIN) {
    document.getElementById("dataForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        errBox.style.display = "none";
        const fd = new FormData(e.target);
        const goods_id = fd.get("goods_id");
        const payload = {
            name: fd.get("name"),
            price: Number(fd.get("price")),
            sup_id: Number(fd.get("sup_id")),
            stop_purchase: fd.get("stop_purchase") === "true"
        };
        const url = goods_id ? `${API_BASE}/inv/${goods_id}` : `${API_BASE}/inv`;
        const method = goods_id ? "PUT" : "POST";

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
}

loadList();
</script>
<?php require __DIR__ . "/../includes/footer.php"; ?>