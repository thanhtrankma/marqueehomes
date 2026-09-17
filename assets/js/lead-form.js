/* Gửi các form đăng ký (markup Contact Form 7 cũ) về /api/lead -> Telegram */
(function () {
  var ENDPOINT = '/api/lead';

  // dùng form.elements (không dùng querySelector) vì Flatsome có thể chuyển các ô ra ngoài <form> khi mở popup
  function fields(form, prefix) {
    return Array.prototype.filter.call(form.elements, function (el) { return el.name && el.name.indexOf(prefix) === 0; });
  }
  function val(form, prefix) {
    var el = fields(form, prefix)[0];
    return el ? el.value.trim() : '';
  }

  function show(form, ok, msg) {
    // nếu các ô đã bị chuyển ra popup thì hiện thông báo cạnh nút gửi, không phải trong <form> đang ẩn
    var btn = Array.prototype.filter.call(form.elements, function (el) { return el.type === 'submit'; })[0];
    var host = btn && !form.contains(btn) ? btn.parentNode : form;
    var out = host.querySelector('.wpcf7-response-output');
    if (!out) { out = document.createElement('div'); out.className = 'wpcf7-response-output'; host.appendChild(out); }
    out.removeAttribute('aria-hidden');
    out.textContent = msg;
    out.style.cssText = 'display:block;margin:1em 0 0;padding:.5em 1em;border:2px solid ' + (ok ? '#46b450' : '#dc3232');
  }

  document.querySelectorAll('.wpcf7 form').forEach(function (form, i) {
    // gắn cứng các ô vào form để vẫn gửi được khi bị chuyển ra ngoài
    if (!form.id) form.id = 'lead-form-' + i;
    form.querySelectorAll('input,select,textarea,button').forEach(function (el) { el.setAttribute('form', form.id); });
    // honeypot chống bot
    var hp = document.createElement('input');
    hp.type = 'text'; hp.name = 'website'; hp.tabIndex = -1; hp.autocomplete = 'off';
    hp.style.cssText = 'position:absolute;left:-9999px;opacity:0;height:0';
    form.appendChild(hp);

    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var phone = val(form, 'tel-');
      if (!/^(\+?84|0)\d{9,10}$/.test(phone.replace(/[^\d+]/g, ''))) return show(form, false, 'Vui lòng nhập đúng số điện thoại.');
      var consent = fields(form, 'privacy-consent')[0];
      if (consent && !consent.checked) return show(form, false, 'Vui lòng đồng ý với điều khoản xử lý thông tin.');

      var btn = Array.prototype.filter.call(form.elements, function (el) { return el.type === 'submit'; })[0];
      if (btn) btn.disabled = true;
      var idInput = form.elements['_wpcf7'];
      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: val(form, 'text-'),
          phone: phone,
          email: val(form, 'email-'),
          needs: fields(form, 'checkbox-').filter(function (c) { return c.checked; }).map(function (c) { return c.value; }),
          form: idInput ? 'CF7 #' + idInput.value : '',
          page: location.href,
          website: hp.value
        })
      }).then(function (r) { return r.json(); }).then(function (d) {
        show(form, !!d.ok, d.message || (d.ok ? 'Đã gửi.' : 'Có lỗi xảy ra.'));
        if (d.ok) form.reset();
      }).catch(function () {
        show(form, false, 'Không gửi được, vui lòng gọi hotline 0972303883.');
      }).then(function () { if (btn) btn.disabled = false; });
    });
  });
})();
