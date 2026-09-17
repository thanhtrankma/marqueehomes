<?php
// Nhận form đăng ký từ assets/js/lead-form.js và bắn thông báo về Telegram.
header('Content-Type: application/json; charset=utf-8');

function done($ok, $message, $code = 200) {
    http_response_code($code);
    echo json_encode(['ok' => $ok, 'message' => $message], JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') done(false, 'Method not allowed', 405);

// chỉ nhận request từ chính site
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin && parse_url($origin, PHP_URL_HOST) !== ($_SERVER['HTTP_HOST'] ?? '')) done(false, 'Forbidden', 403);

$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) done(false, 'Dữ liệu không hợp lệ', 400);

// honeypot: bot điền vào ô ẩn -> giả vờ thành công
if (!empty($in['website'])) done(true, 'OK');

$clean = function ($v, $max = 200) {
    return mb_substr(trim(preg_replace('/\s+/u', ' ', (string)$v)), 0, $max);
};
$name   = $clean($in['name'] ?? '');
$phone  = preg_replace('/[^\d+]/', '', (string)($in['phone'] ?? ''));
$email  = $clean($in['email'] ?? '');
$needs  = $clean(is_array($in['needs'] ?? null) ? implode(', ', $in['needs']) : '', 300);
$page   = $clean($in['page'] ?? '', 300);
$form   = $clean($in['form'] ?? '', 50);

if (!preg_match('/^(\+?84|0)\d{9,10}$/', $phone)) done(false, 'Số điện thoại không hợp lệ.', 422);

// chống spam: tối đa 5 lượt / 10 phút / IP
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$rl = sys_get_temp_dir() . '/mqh_lead_' . md5($ip);
$hits = array_filter(@json_decode(@file_get_contents($rl), true) ?: [], function ($t) { return $t > time() - 600; });
if (count($hits) >= 5) done(false, 'Bạn gửi quá nhanh, vui lòng thử lại sau ít phút.', 429);
$hits[] = time();
@file_put_contents($rl, json_encode(array_values($hits)));

$cfg = require __DIR__ . '/config.php';
$e = function ($s) { return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); };
$lines = ['🏠 <b>KHÁCH ĐĂNG KÝ MỚI — Marquee Homes</b>', ''];
$lines[] = '👤 Họ tên: <b>' . $e($name ?: '(không nhập)') . '</b>';
$lines[] = '📞 SĐT: <b>' . $e($phone) . '</b>';
if ($email) $lines[] = '✉️ Email: ' . $e($email);
if ($needs) $lines[] = '📌 Quan tâm: ' . $e($needs);
if ($form)  $lines[] = '📝 Form: ' . $e($form);
if ($page)  $lines[] = '🔗 Trang: ' . $e($page);
$lines[] = '🕒 ' . (new DateTime('now', new DateTimeZone('Asia/Ho_Chi_Minh')))->format('H:i d/m/Y');

$ch = curl_init('https://api.telegram.org/bot' . $cfg['bot_token'] . '/sendMessage');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 10,
    CURLOPT_POSTFIELDS => [
        'chat_id' => $cfg['chat_id'],
        'text' => implode("\n", $lines),
        'parse_mode' => 'HTML',
        'disable_web_page_preview' => 'true',
    ],
]);
$res = json_decode((string)curl_exec($ch), true);
curl_close($ch);

if (empty($res['ok'])) {
    error_log('lead.php telegram error: ' . json_encode($res));
    done(false, 'Hệ thống đang bận, vui lòng gọi hotline 0972303883.', 502);
}
done(true, 'Đăng ký thành công! Chúng tôi sẽ liên hệ với bạn sớm nhất.');
