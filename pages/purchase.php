<?php
$page_title = "入貨管理";
require __DIR__ . "/../includes/header.php";
require __DIR__ . "/../includes/sidebar.php";
$is_admin = ($_SESSION["role"] ?? "") === "admin";
?>
<main class="main">
    <div class="page-header">
        <h1>入貨管理</h1>
        <button class="btn" onclick="openCreateModal()">+ 新增入貨單</button>
    </div>
    <div class="error-box" id="errBox"></div>

    <div class="card">
        <table>
            <thead>
                <tr>
                    <th>入貨單編號</th>
                    <th>日期</th>
                    <th>總金額</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <!-- 新增入貨單 -->
    <div class="card" id="createCard" style="display:none;">
        <h3>新增入貨單</h3>
        <form id="createForm">
            <div class="form-grid">
                <div class="form-group"><label>日期</label><input type="date" name="date" required></div>
                <div class="form-group"><label>職員編號 (CS-XXXXXX)</label><input type="text" name="staff_no" required></div>
                <div class="form-group"><label>折扣金額（選填）</label><input type="number" name="discount" min="0"></div>
                <div class="form-group"><label>折扣原因（選填）</label><input type="text" name="reason"></div>
            </div>
            <h4>入貨明細</h4>
            <div id="detailRows"></div>
            <button type="button" class="btn btn-outline" onclick="addDetailRow()">+ 新增品項</button>
            <div class="form-actions">
                <button type="submit" class="btn">送出</button>
                <button type="button" class="btn btn-outline" onclick="closeCreateModal()">取消</button>
            </div>
        </form>
    </div>

    <!-- 查看入貨單明細 -->
    <div class="card" id="viewCard" style="display:none;">
        <h3 id="viewTitle"></h3>
        <div id="viewBody"></div>
        <div class="form-actions">
            <button type="button" class="btn btn-outline" onclick="closeViewModal()">關閉</button>
        </div>
    </div>

    <!-- 編輯入貨單 -->
    <div class="card" id="editCard" style="display:none;">
        <h3>編輯入貨單</h3>
        <form id="editForm">
            <input type="hidden" name="pu_id">
            <div class="form-grid">
                <div class="form-group"><label>日期</label><input type="date" name="date"></div>
                <div class="form-group">
                    <label>職員編號 (CS-XXXXXX)</label>
                    <input type="text" name="staff_no" id="editStaffNo">
                </div>
                <div class="form-group"><label>折扣金額（留空代表沒有折扣）</label><input type="number" name="discount" min="0"></div>
                <div class="form-group"><label>折扣原因（留空代表沒有折扣）</label><input type="text" name="reason"></div>
            </div>
            <h4>入貨明細</h4>
            <div id="editDetailRows"></div>
            <button type="button" class="btn btn-outline" onclick="addEditDetailRow()">+ 新增品項</button>
            <div class="form-actions">
                <button type="submit" class="btn">儲存</button>
                <button type="button" class="btn btn-outline" onclick="closeEditModal()">取消</button>
            </div>
        </form>
    </div>
</main>

<script>
const API_BASE = "<?= $API_BASE ?>";
const errBox = document.getElementById("errBox");
const IS_ADMIN = <?= $is_admin ? "true" : "false" ?>;

function showError(msg){
    errBox.textContent = msg;
    errBox.style.display = "block";
}

function formatDate(dateStr) {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    return d.toLocaleDateString("zh-TW", { year: "numeric", month: "2-digit", day: "2-digit" });
}

function toDateInputValue(dateStr) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

// ---------- 顯示表格 ----------
async function loadList() {
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/pur`, {
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
        rows.forEach(p => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${p.pu_no}</td>
                <td>${formatDate(p.date)}</td>
                <td>${p.amount ?? "-"}</td>
                <td>
                    <button class="btn btn-outline" onclick="viewPurchase(${p.pu_id})">查看</button>
                    <button class="btn btn-outline" onclick="openEditModal(${p.pu_id})">編輯</button>
                </td>`;
            tbody.appendChild(tr);
        });
    } catch (e) {
        showError("無法載入入貨清單");
    }
}

// ---------- 查看入貨單明細 ----------
async function viewPurchase(pu_id) {
    closeCreateModal();
    closeEditModal();
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/pur/${pu_id}`, {
            method: "GET",
            credentials: "include"
        });
        const data = await res.json();

        if (!res.ok) {
            showError(data.error || "查詢失敗");
            return;
        }

        document.getElementById("viewTitle").textContent = `入貨單 ${data.pu_no}`;
        let rowsHtml = data.details.map(d => `
            <tr><td>${d.goods_id}</td>
            <td>${d.name}</td>
            <td>${d.unit}</td>
            <td>${d.price}</td>
            <td>${d.amount}</td></tr>
        `).join("");
        document.getElementById("viewBody").innerHTML = `
            <p>日期：${formatDate(data.date)}　職員：${data.staff_no}</p>
            <p>折扣：${data.discount ?? "-"}　折扣原因：${data.reason ?? "-"}</p>
            <p>總金額：${data.amount}</p>
            <table>
                <thead><tr>
                <th>貨品編號</th>
                <th>名稱</th>
                <th>數量</th>
                <th>單價</th>
                <th>小計</th>
                </tr></thead>
                <tbody>${rowsHtml}</tbody>
            </table>`;
        document.getElementById("viewCard").style.display = "block";
    } catch (e) {
        showError("無法連線到伺服器");
    }
}

function closeViewModal() {
    document.getElementById("viewCard").style.display = "none";
}

// ---------- 新增入貨單 ----------
function addDetailRow() {
    const wrap = document.getElementById("detailRows");
    const row = document.createElement("div");
    row.className = "detail-row";
    row.innerHTML = `
        <div class="form-group"><label>貨品編號</label><input type="number" class="d-goods" min="1" required></div>
        <div class="form-group"><label>數量</label><input type="number" class="d-unit" min="0" required></div>
        <div class="form-group"><label>單價</label><input type="number" class="d-price" min="0" required></div>
        <button type="button" class="btn btn-outline" onclick="this.parentElement.remove()">刪除</button>
    `;
    wrap.appendChild(row);
}

function openCreateModal() {
    closeViewModal();
    closeEditModal();
    document.getElementById("createCard").style.display = "block";
    document.getElementById("detailRows").innerHTML = "";
    addDetailRow();
}
function closeCreateModal() {
    document.getElementById("createCard").style.display = "none";
    document.getElementById("createForm").reset();
}

document.getElementById("createForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    errBox.style.display = "none";
    const fd = new FormData(e.target);
    const details = [];
    document.querySelectorAll("#detailRows .detail-row").forEach(row => {
        details.push({
            goods_id: Number(row.querySelector(".d-goods").value),
            unit: Number(row.querySelector(".d-unit").value),
            price: Number(row.querySelector(".d-price").value)
        });
    });
    const payload = { staff_no: fd.get("staff_no"), details };
    if (fd.get("date")) payload.date = fd.get("date");
    if (fd.get("discount")) payload.discount = Number(fd.get("discount"));
    if (fd.get("reason")) payload.reason = fd.get("reason");

    try {
        const res = await fetch(`${API_BASE}/pur`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) {
            showError(data.error || "新增失敗");
            return;
        }

        closeCreateModal();
        loadList();
    } catch (e) {
        showError("無法連線到伺服器");
    }
});

// ---------- 編輯入貨單 ----------
function addEditDetailRow(goods_id = "", unit = "", price = "") {
    const wrap = document.getElementById("editDetailRows");
    const row = document.createElement("div");
    row.className = "detail-row";
    row.innerHTML = `
        <div class="form-group"><label>貨品編號</label><input type="number" class="ed-goods" min="1" value="${goods_id}" required></div>
        <div class="form-group"><label>數量</label><input type="number" class="ed-unit" min="0" value="${unit}" required></div>
        <div class="form-group"><label>單價</label><input type="number" class="ed-price" min="0" value="${price}" required></div>
        <button type="button" class="btn btn-outline" onclick="this.parentElement.remove()">刪除</button>
    `;
    wrap.appendChild(row);
}

async function openEditModal(pu_id) {
    closeCreateModal();
    closeViewModal();
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/pur/${pu_id}`, { credentials: "include" });
        const data = await res.json();
        if (!res.ok) { showError(data.error || "查詢失敗"); return; }

        document.querySelector('#editForm [name="pu_id"]').value = pu_id;
        document.querySelector('#editForm [name="date"]').value = toDateInputValue(data.date);
        document.querySelector('#editForm [name="staff_no"]').value = data.staff_no;
        document.querySelector('#editForm [name="discount"]').value = data.discount ?? "";
        document.querySelector('#editForm [name="reason"]').value = data.reason ?? "";

        // staff 不能改負責職員
        document.getElementById("editStaffNo").disabled = !IS_ADMIN;

        document.getElementById("editDetailRows").innerHTML = "";
        data.details.forEach(d => addEditDetailRow(d.goods_id, d.unit, d.price));

        document.getElementById("editCard").style.display = "block";
    } catch (e) {
        showError("無法連線到伺服器");
    }
}

function closeEditModal() {
    document.getElementById("editCard").style.display = "none";
    document.getElementById("editForm").reset();
    document.getElementById("editDetailRows").innerHTML = "";
}

document.getElementById("editForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    errBox.style.display = "none";
    const fd = new FormData(e.target);
    const pu_id = fd.get("pu_id");

    const details = [];
    document.querySelectorAll("#editDetailRows .detail-row").forEach(row => {
        details.push({
            goods_id: Number(row.querySelector(".ed-goods").value),
            unit: Number(row.querySelector(".ed-unit").value),
            price: Number(row.querySelector(".ed-price").value)
        });
    });

    const payload = { details };
    if (fd.get("date")) payload.date = fd.get("date");
    if (IS_ADMIN && fd.get("staff_no")) payload.staff_no = fd.get("staff_no");

    // 編輯模式：折扣／折扣原因只要其中一個有填，兩個都送出；都空的話明確送 null 代表清空
    const discountVal = fd.get("discount");
    const reasonVal = fd.get("reason");
    payload.discount = discountVal ? Number(discountVal) : null;
    payload.reason = reasonVal || null;

    try {
        const res = await fetch(`${API_BASE}/pur/${pu_id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) { showError(data.error || "更新失敗"); return; }
        closeEditModal();
        loadList();
    } catch (err) {
        showError("無法連線到伺服器");
    }
});

loadList();
</script>
<?php require __DIR__ . "/../includes/footer.php"; ?>