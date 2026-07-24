<?php
$current = basename($_SERVER["PHP_SELF"]);
$role = $_SESSION["role"] ?? "staff";
$staff_no = $_SESSION["staff_no"] ?? "";

function nav_class($file, $current) {
    return $file === $current ? "active" : "";
}
?>
<aside class="sidebar">
    <div class="brand">文具出入貨系統</div>
    <div class="current-user">登入帳號：<br><?= htmlspecialchars($staff_no) ?></div>
    <nav>
        <a class="<?= nav_class('order.php', $current) ?>" href="/pages/order.php">訂單管理</a>
        <a class="<?= nav_class('customer.php', $current) ?>" href="/pages/customer.php">客戶管理</a>
        <a class="<?= nav_class('inventory.php', $current) ?>" href="/pages/invertory.php">貨存管理</a>
        <a class="<?= nav_class('purchase.php', $current) ?>" href="/pages/purchase.php">入貨管理</a>
        <a class="<?= nav_class('supplier.php', $current) ?>" href="/pages/supplier.php">供應商管理</a>
        <?php if ($role === "admin"): ?>
        <a class="<?= nav_class('staff.php', $current) ?>" href="/pages/staff.php">職員管理</a>
        <?php endif; ?>
        <a class="<?= nav_class('account.php', $current) ?>" href="/pages/account.php">修改密碼</a>
    </nav>
    <div class="logout">
        <a href="#" onclick="doLogout()">登出</a>
    </div>
</aside>
<script>
async function doLogout() {
    const API_BASE = "<?= $API_BASE ?>"
    const res = await fetch(`${API_BASE}/logout`, { 
        method: "POST", 
        credentials: "include" 
    });
    const msg = await res.json();
    console.log(msg.message)

    await fetch("/pages/session_clear.php", {
        method: "POST",
        credentials: "include"
    })

    window.location.href = "/pages/login.php";
}

</script>