<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

require __DIR__ . "/config.php";

if (!isset($_SESSION["staff_no"])) {
    header("Location: /pages/login.php");
    exit;
}

$page_title = $page_title ?? "文具出入貨系統";
?>
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title><?= htmlspecialchars($page_title) ?></title>
    <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
<div class="layout">