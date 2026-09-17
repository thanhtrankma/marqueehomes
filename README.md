# marqueehomes.vn — bản tĩnh

Bản sao tĩnh (HTML/CSS) của https://marqueehomes.vn, giữ nguyên cấu trúc URL và đường dẫn ảnh để không ảnh hưởng SEO.

- Mỗi trang: `<slug>/index.html` · CSS/JS/ảnh/font: `wp-content/`, `wp-includes/`, `assets/vendor/`
- Xem thử: `python3 -m http.server 8765` rồi mở http://localhost:8765
- Cào lại từ site gốc: `python3 tools/mirror.py` (ghi đè các chỉnh sửa tay!)
- Sinh lại sitemap sau khi thêm/xoá trang: `python3 tools/build_sitemap.py`

JS còn giữ: jQuery + `flatsome.js` (slider, tab, popup, menu mobile). Đã bỏ: WP Rocket, WooCommerce, Contact Form 7, tracking.

## Form đăng ký → Telegram

`assets/js/lead-form.js` bắt mọi form đăng ký → POST JSON tới `api/lead.php` → bot Telegram gửi vào nhóm.
Token + chat id nằm trong `api/config.php` (đã gitignore, **không** đưa vào JS/HTML). Hosting cần PHP có cURL.
Xem thử local có gửi Telegram thật (không cần PHP): `python3 tools/dev_server.py`.
