<?php
$page_title = "修改密碼";
require __DIR__ . "/../includes/header.php";
require __DIR__ . "/../includes/sidebar.php";
?>
<main class="main">
    <div class="page-header"><h1>修改密碼</h1></div>
    <div class="error-box" id="errBox"></div>
    <div class="card" style="max-width:420px;">
        <form id="pwForm">
            <div class="form-group" style="margin-bottom:14px;">
                <label>舊密碼</label>
                <input type="password" name="old_pw" required>
            </div>
            <div class="form-group" style="margin-bottom:20px;">
                <label>新密碼（至少 7 碼）</label>
                <input type="password" name="new_pw" minlength="7" required>
            </div>
            <button type="submit" class="btn">送出</button>
        </form>
    </div>
</main>

<script>
const API_BASE = "<?= $API_BASE ?>";
const errBox = document.getElementById("errBox");
function showError(msg){ errBox.textContent = msg; errBox.style.display = "block"; }

document.getElementById("pwForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    errBox.style.display = "none";
    const fd = new FormData(e.target);
    const payload = { 
        old_pw: fd.get("old_pw"), 
        new_pw: fd.get("new_pw") 
    };

    try {
        const res = await fetch(`${API_BASE}/account`, {
            method: "PATCH", 
            headers: { "Content-Type": "application/json" },
            credentials: "include", 
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (!res.ok) { 
            showError(data.error || "修改失敗"); 
            return; 
        }
        
        alert("密碼修改成功，請重新登入");
        await fetch(`${API_BASE}/logout`, { 
            method: "POST", 
            credentials: "include" 
        });
        await fetch("/pages/session_clear.php", {
        method: "POST",
        credentials: "include"
        })
        window.location.href = "/pages/login.php";
    } catch (e) { 
        showError("無法連線到伺服器"); 
    }
});
</script>
<?php require __DIR__ . "/../includes/footer.php"; ?>