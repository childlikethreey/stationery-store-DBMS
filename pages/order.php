<?php
$page_title = "訂單管理";
require __DIR__ . "/../includes/header.php";
require __DIR__ . "/../includes/sidebar.php";
$is_admin = ($_SESSION["role"] ?? "") === "admin";
?>
<main class="main">
    <div class="page-header">
        <h1>訂單管理</h1>
        <button class="btn" onclick="openCreateModal()">+ 新增訂單</button>
    </div>

    <div class="error-box" id="errBox"></div>

    <div class="card">
        <table>
            <thead>
                <tr><th>訂單編號</th><th>日期</th><th>總金額</th><th>狀態</th><th>操作</th></tr>
            </thead>
            <tbody id="orderTableBody"></tbody>
        </table>
    </div>

    <!-- 新增訂單 -->
    <div class="card" id="createCard" style="display:none;">
        <h3>新增訂單</h3>
        <form id="createForm">
            <div class="form-grid">
                <div class="form-group"><label>日期</label><input type="date" name="date"></div>
                <div class="form-group"><label>客戶編號 (KXXXXXX)</label><input type="text" name="cust_no" required></div>
                <div class="form-group"><label>職員編號 (CS-XXXXXX)</label><input type="text" name="staff_no" required></div>
                <div class="form-group"><label>折扣金額（選填）</label><input type="number" name="discount" min="0"></div>
                <div class="form-group full"><label>折扣原因（選填）</label><input type="text" name="reason"></div>
            </div>
            <h4>訂購明細</h4>
            <div id="detailRows"></div>
            <button type="button" class="btn btn-outline" onclick="addDetailRow()">+ 新增品項</button>
            <div class="form-actions">
                <button type="submit" class="btn">送出</button>
                <button type="button" class="btn btn-outline" onclick="closeCreateModal()">取消</button>
            </div>
        </form>
    </div>

    <!-- 查看訂單明細 -->
    <div class="card" id="viewCard" style="display:none;">
        <h3 id="viewTitle"></h3>
        <div id="viewBody"></div>
        <div class="form-actions">
            <button type="button" class="btn btn-outline" onclick="closeViewModal()">關閉</button>
        </div>
    </div>

    <!-- 編輯訂單 -->
    <div class="card" id="editCard" style="display:none;">
        <h3>編輯訂單</h3>
        <form id="editForm">
            <input type="hidden" name="order_id">
            <div class="form-grid">
                <div class="form-group"><label>日期</label><input type="date" name="date"></div>
                <div class="form-group">
                    <label>狀態</label>
                    <select name="status">
                        <option value="processing">處理中</option>
                        <option value="shipped">已出貨</option>
                        <option value="completed">已完成</option>
                        <option value="cancelled">已取消</option>
                    </select>
                </div>
                <div class="form-group"><label>客戶編號 (KXXXXXX)</label><input type="text" name="cust_no"></div>
                <div class="form-group">
                    <label>職員編號 (CS-XXXXXX)</label>
                    <input type="text" name="staff_no" id="editStaffNo">
                </div>
                <div class="form-group"><label>折扣金額（留空代表沒有折扣）</label><input type="number" name="discount" min="0"></div>
                <div class="form-group full"><label>折扣原因（留空代表沒有折扣）</label><input type="text" name="reason"></div>
            </div>
            <h4>訂購明細</h4>
            <div id="editDetailRows"></div>
            <button type="button" class="btn btn-outline" id="addEditRowBtn" onclick="addEditDetailRow()">+ 新增品項</button>
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

function showError(msg) {
    errBox.textContent = msg;
    errBox.style.display = "block";
}

function badgeClass(status) {
    return { processing: "badge-processing", shipped: "badge-shipped",
             completed: "badge-completed", cancelled: "badge-cancelled" }[status] || "";
}
function statusLabel(status) {
    return { processing: "處理中", shipped: "已出貨",
             completed: "已完成", cancelled: "已取消" }[status] || status;
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

// ---------- 讀取清單 ----------
async function loadOrders() {
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/order`, { credentials: "include" });
        if (res.status === 401) { window.location.href = "/pages/login.php"; return; }
        const rows = await res.json();
        const tbody = document.getElementById("orderTableBody");
        tbody.innerHTML = "";
        rows.forEach(o => {
            const tr = document.createElement("tr");
            const canEdit = o.status === "processing" || o.status === "shipped";
            tr.innerHTML = `
                <td>${o.order_no}</td>
                <td>${formatDate(o.date)}</td>
                <td>${o.amount ?? "-"}</td>
                <td><span class="badge ${badgeClass(o.status)}">${statusLabel(o.status)}</span></td>
                <td>
                    <button class="btn btn-outline" onclick="viewOrder(${o.order_id})">查看</button>
                    ${canEdit ? `<button class="btn btn-outline" onclick="openEditModal(${o.order_id})">編輯</button>` : ""}
                </td>`;
            tbody.appendChild(tr);
        });
    } catch (e) { showError("無法載入訂單清單"); }
}

// ---------- 查看明細 ----------
async function viewOrder(order_id) {
    closeCreateModal();
    closeEditModal();
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/order/${order_id}`, { credentials: "include" });
        const data = await res.json();
        if (!res.ok) { showError(data.error || "查詢失敗"); return; }

        document.getElementById("viewTitle").textContent = `訂單 ${data.order_no}`;
        let rowsHtml = data.details.map(d => `
            <tr><td>${d.goods_id}</td><td>${d.name}</td><td>${d.unit}</td><td>${d.price}</td><td>${d.amount}</td></tr>
        `).join("");
        document.getElementById("viewBody").innerHTML = `
            <p>日期：${formatDate(data.date)}　狀態：<span class="badge ${badgeClass(data.status)}">${statusLabel(data.status)}</span></p>
            <p>客戶：${data.cust_no}　職員：${data.staff_no}</p>
            <p>折扣：${data.discount ?? "-"}　折扣原因：${data.reason ?? "-"}</p>
            <p>總金額：${data.amount}</p>
            <table>
                <thead><tr><th>貨品編號</th><th>名稱</th><th>數量</th><th>單價</th><th>小計</th></tr></thead>
                <tbody>${rowsHtml}</tbody>
            </table>
        `;
        document.getElementById("viewCard").style.display = "block";
    } catch (e) { showError("無法連線到伺服器"); }
}
function closeViewModal() { document.getElementById("viewCard").style.display = "none"; }

// ---------- 新增訂單 ----------
function addDetailRow() {
    const wrap = document.getElementById("detailRows");
    const row = document.createElement("div");
    row.className = "detail-row";
    row.innerHTML = `
        <div class="form-group"><label>貨品編號</label><input type="number" class="d-goods" min="1" required></div>
        <div class="form-group"><label>數量</label><input type="number" class="d-unit" min="1" required></div>
        <div></div>
        <button type="button" class="btn btn-outline" onclick="this.parentElement.remove()">刪除</button>
    `;
    wrap.appendChild(row);
}

function openCreateModal() {
    closeEditModal();
    closeViewModal();
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
            unit: Number(row.querySelector(".d-unit").value)
        });
    });
    const payload = { cust_no: fd.get("cust_no"), staff_no: fd.get("staff_no"), details };
    if (fd.get("date")) payload.date = fd.get("date");
    if (fd.get("discount")) payload.discount = Number(fd.get("discount"));
    if (fd.get("reason")) payload.reason = fd.get("reason");

    try {
        const res = await fetch(`${API_BASE}/order`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            credentials: "include", body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) { showError(data.error || "新增失敗"); return; }
        closeCreateModal();
        loadOrders();
    } catch (err) { showError("無法連線到伺服器"); }
});

// ---------- 編輯訂單 ----------
function addEditDetailRow(goods_id = "", unit = "") {
    const wrap = document.getElementById("editDetailRows");
    const row = document.createElement("div");
    row.className = "detail-row";
    row.innerHTML = `
        <div class="form-group"><label>貨品編號</label><input type="number" class="ed-goods" min="1" value="${goods_id}" required></div>
        <div class="form-group"><label>數量</label><input type="number" class="ed-unit" min="1" value="${unit}" required></div>
        <div></div>
        <button type="button" class="btn btn-outline" onclick="this.parentElement.remove()">刪除</button>
    `;
    wrap.appendChild(row);
}

async function openEditModal(order_id) {
    closeCreateModal();
    closeViewModal();
    errBox.style.display = "none";
    try {
        const res = await fetch(`${API_BASE}/order/${order_id}`, { credentials: "include" });
        const data = await res.json();
        if (!res.ok) { showError(data.error || "查詢失敗"); return; }

        document.querySelector('#editForm [name="order_id"]').value = order_id;
        document.querySelector('#editForm [name="date"]').value = toDateInputValue(data.date);
        document.querySelector('#editForm [name="status"]').value = data.status;
        document.querySelector('#editForm [name="cust_no"]').value = data.cust_no;
        document.querySelector('#editForm [name="staff_no"]').value = data.staff_no;
        document.querySelector('#editForm [name="discount"]').value = data.discount ?? "";
        document.querySelector('#editForm [name="reason"]').value = data.reason ?? "";

        // 只有 processing 狀態才能改「其他資料」（日期、客戶、折扣等），shipped 只能改狀態
        const canEditOthers = data.status === "processing";
        document.querySelector('#editForm [name="date"]').disabled = !canEditOthers;
        document.querySelector('#editForm [name="cust_no"]').disabled = !canEditOthers;
        document.querySelector('#editForm [name="discount"]').disabled = !canEditOthers;
        document.querySelector('#editForm [name="reason"]').disabled = !canEditOthers;

        // staff_no：先看是不是 processing，再看角色
        document.getElementById("editStaffNo").disabled = !canEditOthers || !IS_ADMIN;

        // 只有 processing 狀態才能改明細
        const canEditDetails = data.status === "processing";
        document.getElementById("editDetailRows").innerHTML = "";
        data.details.forEach(d => addEditDetailRow(d.goods_id, d.unit));
        document.querySelectorAll("#editDetailRows input, #editDetailRows button").forEach(el => {
            el.disabled = !canEditDetails;
        });
        document.getElementById("addEditRowBtn").disabled = !canEditDetails;

        document.getElementById("editCard").style.display = "block";
    } catch (e) { showError("無法連線到伺服器"); }
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
    const order_id = fd.get("order_id");

    const payload = { status: fd.get("status") };

    if (!document.querySelector('#editForm [name="date"]').disabled && fd.get("date")) {
        payload.date = fd.get("date");
    }
    if (!document.querySelector('#editForm [name="cust_no"]').disabled && fd.get("cust_no")) {
        payload.cust_no = fd.get("cust_no");
    }
    if (!document.getElementById("editStaffNo").disabled && fd.get("staff_no")) {
        payload.staff_no = fd.get("staff_no");
    }
    if (!document.querySelector('#editForm [name="discount"]').disabled) {
        payload.discount = fd.get("discount") ? Number(fd.get("discount")) : null;
        payload.reason = fd.get("reason") || null;
    }

    const detailsEnabled = !document.querySelector("#editDetailRows input")?.disabled;
    if (detailsEnabled) {
        const details = [];
        document.querySelectorAll("#editDetailRows .detail-row").forEach(row => {
            details.push({
                goods_id: Number(row.querySelector(".ed-goods").value),
                unit: Number(row.querySelector(".ed-unit").value)
            });
        });
        payload.details = details;
    }

    try {
        const res = await fetch(`${API_BASE}/order/${order_id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) { showError(data.error || "更新失敗"); return; }
        closeEditModal();
        loadOrders();
    } catch (err) { showError("無法連線到伺服器"); }
});

loadOrders();
</script>
<?php require __DIR__ . "/../includes/footer.php"; ?>