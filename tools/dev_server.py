#!/usr/bin/env python3
"""Server xem thử local: phục vụ file tĩnh + mô phỏng api/lead.php (đọc token từ api/config.php).
Chạy: python3 tools/dev_server.py  ->  http://localhost:8765"""
import os, re, json, html, datetime, urllib.request, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = dict(re.findall(r"'(bot_token|chat_id)'\s*=>\s*'([^']+)'", open(os.path.join(ROOT, "api/config.php")).read()))

class H(SimpleHTTPRequestHandler):
    def reply(self, code, ok, msg):
        body = json.dumps({"ok": ok, "message": msg}, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/") or self.path.startswith("/tools/"):
            return self.send_error(403)
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/lead.php":
            return self.send_error(404)
        try:
            d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except Exception:
            return self.reply(400, False, "Dữ liệu không hợp lệ")
        if d.get("website"):
            return self.reply(200, True, "OK")
        phone = re.sub(r"[^\d+]", "", str(d.get("phone", "")))
        if not re.match(r"^(\+?84|0)\d{9,10}$", phone):
            return self.reply(422, False, "Số điện thoại không hợp lệ.")
        e = lambda k: html.escape(str(d.get(k, ""))[:300])
        lines = ["🏠 <b>KHÁCH ĐĂNG KÝ MỚI — Marquee Homes</b>", "",
                 "👤 Họ tên: <b>%s</b>" % (e("name") or "(không nhập)"), "📞 SĐT: <b>%s</b>" % phone]
        if d.get("email"): lines.append("✉️ Email: " + e("email"))
        if d.get("needs"): lines.append("📌 Quan tâm: " + html.escape(", ".join(d["needs"])))
        if d.get("form"): lines.append("📝 Form: " + e("form"))
        if d.get("page"): lines.append("🔗 Trang: " + e("page"))
        lines.append("🕒 " + datetime.datetime.now().strftime("%H:%M %d/%m/%Y"))
        data = urllib.parse.urlencode({"chat_id": cfg["chat_id"], "text": "\n".join(lines),
                                       "parse_mode": "HTML", "disable_web_page_preview": "true"}).encode()
        try:
            with urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % cfg["bot_token"], data, timeout=10) as r:
                ok = json.loads(r.read()).get("ok")
        except Exception as ex:
            print("telegram error:", getattr(ex, "code", ex)); ok = False
        if not ok:
            return self.reply(502, False, "Hệ thống đang bận, vui lòng gọi hotline 0972303883.")
        self.reply(200, True, "Đăng ký thành công! Chúng tôi sẽ liên hệ với bạn sớm nhất.")

ThreadingHTTPServer(("127.0.0.1", 8765), partial(H, directory=ROOT)).serve_forever()
