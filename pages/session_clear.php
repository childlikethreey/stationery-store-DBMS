<?php
if (session_status() == PHP_SESSION_NONE) session_start();
unset($_SESSION["staff_no"]);
unset($_SESSION["role"]);
echo json_encode(["message" => "session cleared"]);
?>