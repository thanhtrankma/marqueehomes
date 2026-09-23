#!/usr/bin/env python3
"""Mirror marqueehomes.vn thành site tĩnh (HTML/CSS + JS giao diện tối thiểu).

Chạy:  python3 tools/mirror.py
Kết quả ghi vào thư mục gốc dự án, giữ nguyên cấu trúc URL của site gốc.
"""
import os, re, sys, time, html
import urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor

HOST = "marqueehomes.vn"
ORIGIN = "https://" + HOST
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
SITEMAPS = ["post", "page", "product", "category", "product_cat"]
MAX_PAGES = 400
LEAD_FORM_JS_VERSION = 3  # tăng khi sửa assets/js/lead-form.js (xem clean_html)

SKIP_PAGE = re.compile(
    r"^/(wp-admin|wp-login|wp-json|xmlrpc|my-account|tai-khoan|cart|gio-hang|"
    r"checkout|thanh-toan|feed|comments)|/feed/|/embed/|/trackback/|/amp/?$")
ASSET_EXT = (r"(?:css|js|png|jpe?g|gif|webp|avif|svg|ico|woff2?|ttf|eot|otf|"
             r"mp4|webm|pdf|json|map)")

# script bị loại: WP Rocket, WooCommerce, CF7, tracking đã chết, v.v.
DROP_SCRIPT = re.compile(
    r"RocketLazyLoadScripts|rocket-browser-checker|rocket-preload-links|"
    r"RocketPreloadLinksConfig|var wpcf7|wc_add_to_cart_params|woocommerce_params|"
    r"stats\.wp\.com|googletagmanager|gtag\(|contact-form-7|woocommerce/assets|"
    r"flatsome/assets/js/woocommerce|wp-includes/js/dist/|woocommerce-no-js|"
    r"speculationrules|wp-emoji|_wpemojiSettings|MSIE\|Internet Explorer|"
    r"wc_cart_fragments|wc-cart-fragments|sourcebuster|order-attribution|"
    r"wp-polyfill|comment-reply", re.I)
DROP_LINK = re.compile(
    r"rel=['\"]?(pingback|profile|dns-prefetch|prefetch|preconnect|EditURI|shortlink|"
    r"https://api\.w\.org/|wlwmanifest)|application/rss\+xml|oembed|"
    r"type=['\"]application/json['\"]", re.I)


def fetch(url, binary=False, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
                ctype = r.headers.get("Content-Type", "")
                return (data if binary else data.decode("utf-8", "replace")), ctype, r.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 410):
                return None, str(e.code), url
        except Exception:
            pass
        time.sleep(1.5 * (i + 1))
    return None, "error", url


def local_path(urlpath):
    p = urllib.parse.unquote(urlpath.split("?")[0].split("#")[0])
    return os.path.join(ROOT, p.lstrip("/"))


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb" if isinstance(data, bytes) else "w", **({} if isinstance(data, bytes) else {"encoding": "utf-8"})) as f:
        f.write(data)


# ---------------------------------------------------------------- HTML cleanup
PROTECT = re.compile(
    r"<link[^>]+rel=['\"]canonical['\"][^>]*>|<link[^>]+rel=['\"](?:next|prev)['\"][^>]*>|"
    r"<meta[^>]+(?:property|name)=['\"](?:og:|twitter:|article:)[^>]*>|"
    r"<script[^>]+application/ld\+json[^>]*>.*?</script>", re.S | re.I)


def clean_html(src):
    # 1. script
    def script_sub(m):
        tag, body = m.group(1), m.group(2)
        if "application/ld+json" in tag:
            return m.group(0)
        if DROP_SCRIPT.search(tag) or DROP_SCRIPT.search(body[:4000]):
            return ""
        tag = re.sub(r"\s+type=(['\"])rocketlazyloadscript\1", "", tag)
        tag = re.sub(r"\s+data-rocket-type=(['\"]).*?\1", "", tag)
        tag = tag.replace("data-rocket-src=", "src=")
        return "<script%s>%s</script>" % (tag, body)
    src = re.sub(r"<script([^>]*)>(.*?)</script>", script_sub, src, flags=re.S | re.I)

    # 2. link/meta rác của WordPress
    src = re.sub(r"<link[^>]*>", lambda m: "" if DROP_LINK.search(m.group(0)) else m.group(0), src)
    src = re.sub(r"<meta name=['\"]generator['\"][^>]*>\s*", "", src)
    src = re.sub(r"<style id=['\"]wp-emoji-styles-inline-css['\"].*?</style>\s*", "", src, flags=re.S)
    src = re.sub(r"<!-- This website is like a Rocket.*?-->", "", src, flags=re.S)
    src = re.sub(r"<meta[^>]*data-osh-[^>]*>\s*|<script[^>]*/_osh/[^>]*></script>\s*", "", src)  # hosting panel chèn
    src = re.sub(r"\s+integrity=(['\"]).*?\1", "", src)
    src = re.sub(r"\s+crossorigin=(['\"]).*?\1", "", src)

    # hotline/zalo mới (site gốc vẫn dùng số cũ 0901583289)
    src = re.sub(r"0901([ .]?)583([ .]?)289", r"0972\g<1>303\g<2>883", src)

    # logo trong header mobile bị hỏng (404) trên chính site gốc -> thay ảnh logo đang dùng
    src = src.replace(
        "/wp-content/uploads/2023/12/hhc_logo-02-1.png",
        "/wp-content/uploads/2026/07/Logo-Marquee-2-03.png",
    )

    # form đăng ký -> /api/lead (Vercel) hoặc /api/lead.php (PHP) -> Telegram
    # LEAD_FORM_JS_VERSION: tăng số này mỗi khi sửa assets/js/lead-form.js để tránh
    # cache 5 phút (must-revalidate, xem vercel.json) trả file cũ cho khách đang mở trang.
    src = src.replace(
        "</body>",
        '<script src="/assets/js/lead-form.js?v=%d" defer></script>\n</body>' % LEAD_FORM_JS_VERSION,
        1,
    )

    # 3. font awesome CDN -> local
    src = re.sub(r"https://use\.fontawesome\.com/releases/v5\.15\.4/", "/assets/vendor/fontawesome/", src)

    # 4. URL tuyệt đối -> root-relative (trừ canonical / og / schema)
    kept = []
    def keep(m):
        kept.append(m.group(0)); return "\x00%d\x00" % (len(kept) - 1)
    src = PROTECT.sub(keep, src)
    for a, b in ((ORIGIN + "/", "/"), ("https:\\/\\/%s\\/" % HOST, "\\/"),
                 ("http://%s/" % HOST, "/"), ("//%s/" % HOST, "/"),
                 (ORIGIN, "/")):
        src = src.replace(a, b)
    # đường dẫn tương đối thiếu "/" (lỗi của site gốc) -> root-relative
    src = re.sub(r"((?:src|href)=['\"])(wp-(?:content|includes)/)", r"\1/\2", src)
    # bỏ ?ver=... trên asset
    src = re.sub(r"(\.(?:css|js))\?ver=[\w.\-]+", r"\1", src)
    src = re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], src)
    # html class: no-js vẫn được JS nhỏ đổi thành js
    src = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", src)
    return src


def find_links(src):
    out = set()
    for m in re.finditer(r"<a\s[^>]*?href=(['\"])(.*?)\1", src, flags=re.I | re.S):
        h = html.unescape(m.group(2)).strip()
        if h.startswith(ORIGIN):
            h = h[len(ORIGIN):] or "/"
        if not h.startswith("/") or h.startswith("//"):
            continue
        h = h.split("#")[0]
        if not h or "?" in h or SKIP_PAGE.search(h):
            continue
        if re.search(r"\.%s$" % ASSET_EXT, h, flags=re.I):
            continue
        out.add(h if h.endswith("/") else h + "/")
    return out


def find_assets(text):
    out = set()
    for m in re.finditer(r"(?<![\w.])(/(?:wp-content|wp-includes|assets)/[^\s\"'()<>,\\]+?\.%s)(?=[\s\"'()<>,?#\\]|$)" % ASSET_EXT,
                         text.replace("\\/", "/"), flags=re.I):
        out.add(html.unescape(m.group(1)))
    return out


# ---------------------------------------------------------------- main
def main():
    pages = set(["/"])
    for s in SITEMAPS:
        xml, _, _ = fetch("%s/%s-sitemap.xml" % (ORIGIN, s))
        for loc in re.findall(r"<loc>([^<]+)</loc>", xml or ""):
            if loc.startswith(ORIGIN) and not re.search(r"\.%s$" % ASSET_EXT, loc, flags=re.I):
                p = loc[len(ORIGIN):] or "/"
                if not SKIP_PAGE.search(p):
                    pages.add(p)
    print("sitemap:", len(pages), "trang")

    done, assets, report = {}, set(), []
    queue = sorted(pages)
    while queue and len(done) < MAX_PAGES:
        p = queue.pop(0)
        if p in done:
            continue
        raw, ctype, final = fetch(ORIGIN + urllib.parse.quote(p, safe="/%"))
        if raw is None or "html" not in ctype:
            done[p] = None; report.append("SKIP %s (%s)" % (p, ctype)); continue
        fp = urllib.parse.urlparse(final).path
        if fp != p and fp in done:
            done[p] = None; report.append("REDIRECT %s -> %s" % (p, fp)); continue
        for l in find_links(raw):
            if l not in done and l not in queue:
                queue.append(l)
        out = clean_html(raw)
        assets |= find_assets(out)
        # og:image... vẫn là URL tuyệt đối -> cũng cần tải
        assets |= find_assets(raw.replace(ORIGIN, ""))
        write(os.path.join(local_path(p), "index.html"), out)
        done[p] = True
        print("page", len([1 for v in done.values() if v]), p)
        time.sleep(0.3)

    # flatsome chunks (nạp động bởi flatsome.js)
    for c in ("slider", "popups", "tooltips", "countup", "lottie", "sticky-sidebar"):
        assets.add("/wp-content/themes/flatsome/assets/js/chunk.%s.js" % c)

    fetched = set()
    def get_asset(a):
        if a in fetched:
            return []
        fetched.add(a)
        dest = local_path(a)
        if a.startswith("/assets/vendor/fontawesome/"):
            url = "https://use.fontawesome.com/releases/v5.15.4/" + a[len("/assets/vendor/fontawesome/"):]
        else:
            url = ORIGIN + urllib.parse.quote(a, safe="/%")
        data, ctype, _ = fetch(url, binary=True)
        if data is None:
            report.append("ASSET FAIL %s (%s)" % (a, ctype)); return []
        more = []
        if a.lower().endswith(".css"):
            css = data.decode("utf-8", "replace").replace(ORIGIN + "/", "/")
            css = css.replace("https://use.fontawesome.com/releases/v5.15.4/", "/assets/vendor/fontawesome/")
            for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", css):
                u = m.group(1).strip()
                if u.startswith(("data:", "http", "//")):
                    continue
                more.append(urllib.parse.urljoin(a, u).split("?")[0].split("#")[0])
            for m in re.finditer(r"@import\s+['\"]([^'\"]+)['\"]", css):
                more.append(urllib.parse.urljoin(a, m.group(1)).split("?")[0])
            data = css.encode("utf-8")
        write(dest, data)
        return more

    todo = sorted(assets)
    while todo:
        with ThreadPoolExecutor(6) as ex:
            nxt = [x for r in ex.map(get_asset, todo) for x in r]
        todo = sorted(set(nxt) - fetched)
    print("assets:", len(fetched))

    ok = sorted(p for p, v in done.items() if v)
    write(os.path.join(ROOT, "tools", "pages.txt"), "\n".join(ok) + "\n")
    write(os.path.join(ROOT, "tools", "mirror-report.txt"), "\n".join(report) + "\n")
    print("xong: %d trang, %d cảnh báo (tools/mirror-report.txt)" % (len(ok), len(report)))


if __name__ == "__main__":
    sys.exit(main())
