#!/usr/bin/env python3
"""Sinh sitemap.xml từ các file index.html trong dự án. Chạy: python3 tools/build_sitemap.py"""
import os, re, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN = "https://marqueehomes.vn"
SKIP = ("tools", "wp-content", "wp-includes", "assets", ".git", ".claude")
rows = []
for d, dirs, files in os.walk(ROOT):
    dirs[:] = [x for x in dirs if not (d == ROOT and x in SKIP)]
    if "index.html" not in files:
        continue
    f = os.path.join(d, "index.html")
    src = open(f, encoding="utf-8").read(20000)
    if re.search(r'name="robots" content="[^"]*noindex', src):
        continue
    m = re.search(r'(?:article:modified_time|og:updated_time)" content="([^"]+)"', src)
    mod = m.group(1) if m else datetime.date.fromtimestamp(os.path.getmtime(f)).isoformat()
    rel = os.path.relpath(d, ROOT)
    rows.append((ORIGIN + "/" + ("" if rel == "." else rel.replace(os.sep, "/") + "/"), mod))
rows.sort()
xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
xml += ["  <url><loc>%s</loc><lastmod>%s</lastmod></url>" % r for r in rows]
xml.append("</urlset>")
open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(xml) + "\n")
print(len(rows), "URL -> sitemap.xml")
