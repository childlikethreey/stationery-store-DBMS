<?php
if (session_status() === PHP_SESSION_NONE) session_start();
$input = json_decode(file_get_contents("php://input"), true);

if (isset($input["staff_no"]) && isset($input["role"])) {
    $_SESSION["staff_no"] = $input["staff_no"];
    $_SESSION["role"] = $input["role"];
    echo json_encode(["message" => "ok"]);
} else {
    http_response_code(400);
    echo json_encode(["message" => "missing fields"]);
}