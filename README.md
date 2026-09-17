# marqueehomes.vn — bản tĩnh

Bản sao tĩnh (HTML/CSS) của https://marqueehomes.vn, giữ nguyên cấu trúc URL và đường dẫn ảnh để không ảnh hưởng SEO.

- Mỗi trang: `<slug>/index.html` · CSS/JS/ảnh/font: `wp-content/`, `wp-includes/`, `assets/vendor/`
- Xem thử: `python3 -m http.server 8765` rồi mở http://localhost:8765
- Cào lại từ site gốc: `python3 tools/mirror.py` (ghi đè các chỉnh sửa tay!)
- Sinh lại sitemap sau khi thêm/xoá trang: `python3 tools/build_sitemap.py`

JS còn giữ: jQuery + `flatsome.js` (slider, tab, popup, menu mobile). Đã bỏ: WP Rocket, WooCommerce, Contact Form 7, tracking.

## Form đăng ký → Telegram

`assets/js/lead-form.js` bắt mọi form đăng ký → POST JSON tới `api/lead` → bot Telegram gửi vào nhóm.

- **Hosting PHP** (cũ): dùng `api/lead.php` + `api/config.php` (token/chat id, đã gitignore). Cần PHP có cURL.
- **Vercel** (hiện tại): dùng `api/lead.js` (Node Serverless Function). Token + chat id lấy từ biến môi trường
  `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` khai báo trong Vercel Project Settings → Environment Variables.
  `api/lead.php`, `api/.htaccess`, `api/config.php` không được đưa lên Vercel (xem `.vercelignore`).
  Lưu ý: giới hạn 5 lượt/10 phút/IP của bản PHP không còn (serverless không giữ state giữa các lần gọi),
  chỉ còn honeypot chống bot cơ bản.

Xem thử local có gửi Telegram thật (không cần PHP): `python3 tools/dev_server.py`.

### Deploy lên Vercel

1. Import repo GitHub vào Vercel, Framework Preset chọn **Other**, Build Command để trống, Output Directory để `.`.
2. Thêm 2 biến môi trường: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (lấy giá trị từ `api/config.php` cũ).
3. Deploy. Hoặc dùng CLI: `npx vercel --prod` (sau khi `npx vercel login`).
