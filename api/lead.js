// Nhận form đăng ký từ assets/js/lead-form.js và bắn thông báo về Telegram.
// Bản Vercel Serverless Function tương đương api/lead.php.
// Cần 2 biến môi trường trong Vercel: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

function clean(v, max = 200) {
  return String(v ?? '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ ok: false, message: 'Method not allowed' });
    return;
  }

  // chỉ nhận request từ chính site
  const origin = req.headers.origin || '';
  const host = req.headers.host || '';
  if (origin) {
    try {
      const originHost = new URL(origin).host;
      if (originHost !== host) {
        res.status(403).json({ ok: false, message: 'Forbidden' });
        return;
      }
    } catch (e) {
      res.status(403).json({ ok: false, message: 'Forbidden' });
      return;
    }
  }

  const input = req.body && typeof req.body === 'object' ? req.body : {};

  // honeypot: bot điền vào ô ẩn -> giả vờ thành công
  if (input.website) {
    res.status(200).json({ ok: true, message: 'OK' });
    return;
  }

  const name = clean(input.name);
  const phone = String(input.phone ?? '').replace(/[^\d+]/g, '');
  const email = clean(input.email);
  const needs = clean(Array.isArray(input.needs) ? input.needs.join(', ') : '', 300);
  const page = clean(input.page, 300);
  const form = clean(input.form, 50);

  if (!/^(\+?84|0)\d{9,10}$/.test(phone)) {
    res.status(422).json({ ok: false, message: 'Số điện thoại không hợp lệ.' });
    return;
  }

  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;
  if (!botToken || !chatId) {
    // Lỗi cấu hình của chính app (thiếu biến môi trường trên Vercel) — dùng 500,
    // KHÔNG dùng 502, để không lẫn với lỗi thật của Telegram (upstream) bên dưới.
    // Vercel > Project Settings > Environment Variables, rồi phải Redeploy lại
    // (đổi biến môi trường không tự áp dụng cho các deploy đã build trước đó).
    console.error('lead.js: missing TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID env vars');
    res.status(500).json({ ok: false, message: 'Server thiếu cấu hình TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID.' });
    return;
  }

  const esc = (s) =>
    String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');

  const lines = ['🏠 <b>KHÁCH ĐĂNG KÝ MỚI — Marquee Homes</b>', ''];
  lines.push('👤 Họ tên: <b>' + esc(name || '(không nhập)') + '</b>');
  lines.push('📞 SĐT: <b>' + esc(phone) + '</b>');
  if (email) lines.push('✉️ Email: ' + esc(email));
  if (needs) lines.push('📌 Quan tâm: ' + esc(needs));
  if (form) lines.push('📝 Form: ' + esc(form));
  if (page) lines.push('🔗 Trang: ' + esc(page));
  lines.push(
    '🕒 ' +
      new Intl.DateTimeFormat('vi-VN', {
        timeZone: 'Asia/Ho_Chi_Minh',
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      }).format(new Date())
  );

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    const r = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: lines.join('\n'),
        parse_mode: 'HTML',
        disable_web_page_preview: true,
      }),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    const data = await r.json();

    if (!data.ok) {
      console.error('lead.js telegram error:', JSON.stringify(data));
      res.status(502).json({ ok: false, message: 'Hệ thống đang bận, vui lòng gọi hotline 0972303883.' });
      return;
    }

    res.status(200).json({ ok: true, message: 'Đăng ký thành công! Chúng tôi sẽ liên hệ với bạn sớm nhất.' });
  } catch (e) {
    console.error('lead.js telegram exception:', e);
    res.status(502).json({ ok: false, message: 'Hệ thống đang bận, vui lòng gọi hotline 0972303883.' });
  }
};
