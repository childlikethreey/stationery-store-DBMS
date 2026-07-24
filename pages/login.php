<?php
if (session_status() === PHP_SESSION_NONE) session_start();
if (isset($_SESSION["staff_no"])) {
    header("Location: /pages/order.php");
    exit;
}

require __DIR__ . "/../includes/config.php";
?>
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>登入 - 文具出入貨系統</title>
    <link rel="stylesheet" href="/assets/css/style.css">
</head> 
<body>
<div class="login-wrap">
    <div class="login-card">
        <h1>ABC Warehouse</h1>
        <div class="error-box" id="errBox"></div>
        <form id="login-info">
            <div class="form-group" style="margin-bottom:14px;">
                <label>職員編號</label>
                <input type="text" id="staff_no" placeholder="CS-XXXXXX（6個數字）" required>
            </div>
            <div class="form-group" style="margin-bottom:20px;">
                <label>密碼</label>
                <input type="password" id="pw" required>
            </div>
            <button type="submit" class="btn" style="width:100%; font-size: 20px">Login</button>
        </form>
    </div>
</div>

<script>
const API_BASE = "<?= $API_BASE ?>";

document.getElementById("login-info").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errBox = document.getElementById("errBox");
    errBox.style.display = "none";

    const staff_no = document.getElementById("staff_no").value.trim();
    const pw = document.getElementById("pw").value;

    try {
        const res = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ staff_no, pw })
        });
        const data = await res.json();

        if (!res.ok) {
            errBox.textContent = data.error || "登入失敗";
            errBox.style.display = "block";
            return;
        }

        const session_res = await fetch("/pages/session_set.php", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ staff_no: data.staff_no, role: data.role })
        });

        if(!session_res.ok) {
            showError("登入處理失敗，請重試");
            return;
        }

        window.location.href = "/pages/order.php";
    } catch (err) {
        errBox.textContent = "無法連線到伺服器";
        errBox.style.display = "block";
    }
});
</script>
</body>
</html>