# -*- coding: utf-8 -*-
"""Reusable finalizer: insert card (with thumbnail) + sitemap entry + self-check.

Usage: python finalize_article.py <slug> "<title>" "<dateline>" "<excerpt>" <n_scene> [<iso>] [<display>]
"""
import json, re, sys
from pathlib import Path

REPO = Path(r'C:/Users/a/Desktop/chenpi-website')
SIMP_ONLY = ('陈视么们为这个说话时东门华车长问题据证术艺买卖贵价钱银铁钟错关开见现'
             '经济营业点热闻频体坛设备标识级统计网络软数据资产专业团队顾员会议报'
             '导广场张让认记录标礼检杂辖饱满咙账数'
             '干仓湿谜师雾过边来药医书车马鸟鱼')

slug = sys.argv[1]
title = sys.argv[2]
dateline = sys.argv[3]
excerpt = sys.argv[4]
n_scene = int(sys.argv[5])
iso = sys.argv[6] if len(sys.argv) > 6 else ''
disp = sys.argv[7] if len(sys.argv) > 7 else ''
SD = slug[:-5]
URL = f'https://www.yiyichenpi.com/{slug}'

log = []
# ---- 卡片（含縮圖）----
ap = REPO / 'articles.html'
a = ap.read_text(encoding='utf-8')
if slug in a:
    log.append('卡片已存在')
else:
    blk = (f'\n      <article class="article-card">\n        <a href="{slug}">\n'
           f'          <div class="article-thumb"><img src="images/{SD}-1900.jpg" alt="{title}" loading="lazy"></div>\n'
           '          <div class="article-text">\n'
           f'            <h3>{title}</h3>\n'
           f'            <p class="meta">{dateline}</p>\n'
           f'            <p class="excerpt">{excerpt}</p>\n'
           '            <span class="read-more">閱讀全文 →</span>\n'
           '          </div>\n        </a>\n      </article>\n')
    a = a.replace('<section class="article-list">', '<section class="article-list">' + blk, 1)
    ap.write_text(a, encoding='utf-8')
    log.append('卡片已置頂（含縮圖）')

# ---- sitemap ----
sp = REPO / 'sitemap.xml'
s = sp.read_text(encoding='utf-8')
if slug in s:
    log.append('sitemap 已存在')
else:
    entry = (f'  <url>\n    <loc>{URL}</loc>\n    <lastmod>2026-10-06</lastmod>\n'
             '    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n')
    s = s.replace('</urlset>', entry + '</urlset>', 1)
    sp.write_text(s, encoding='utf-8')
    log.append('sitemap 已加入')

# ---- 自檢 ----
raw = (REPO / slug).read_bytes()
t = raw.decode('utf-8')
checks = []
P = lambda n, ok: checks.append((n, ok))
P('UTF-8 無 BOM / 無亂碼', raw[:3] != b'\xef\xbb\xbf' and '\ufffd' not in t)
P('CSS v=5 / lang=zh-HK', 'css/style.css?v=5' in t and '<html lang="zh-HK">' in t)
P('canonical / og:url', f'<link rel="canonical" href="{URL}">' in t and f'content="{URL}"' in t)
P('og:image 指封面', f'images/{SD}-1900.jpg' in t)
P('無舊域名 / 無{{}}', 'yingying-chenpi.vercel.app' not in t and '{{' not in t)
P('品牌名 滢滢', '滢滢' in t and '瀅瀅' not in t)
P('h1/title 各 1', t.count('<h1') == 1 and t.count('<title>') == 1)
P('對話 >= 2', t.count('class="dialogue"') >= 2)
P('FAQ >= 5', t.count('<strong>') >= 5)
P('內鏈 >= 2', len(re.findall(r'class="related-item"', t)) >= 2)
P('結尾鉤子', '下期預告' in t or '下回預告' in t)
P('GEO 地理詞', all(k in t for k in ('新會', '江門', '廣東')))
P('無簡體殘留', not sorted({c for c in SIMP_ONLY if c in t}))
if iso:
    P('時間精確到秒', iso in t and disp in t)
blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
types, ok = [], True
for b in blocks:
    try:
        types.append(json.loads(b).get('@type'))
    except Exception:
        ok = False
P(f'JSON-LD {types}', ok and 'BlogPosting' in types and 'FAQPage' in types)
P(f'figure = 1+{n_scene}', t.count('<figure') == 1 + n_scene)
cover = REPO / 'images' / f'{SD}-1900.jpg'
P('封面存在且 <=200KB', cover.is_file() and cover.stat().st_size <= 200 * 1024)
for i in range(1, n_scene + 1):
    img = REPO / 'images' / f'{SD}-scene{i}.jpg'
    P(f'scene{i} 存在/已插入/<=200KB',
      img.is_file() and f'{SD}-scene{i}.jpg' in t and img.stat().st_size <= 200 * 1024)
P('場景圖 alt 齊全', len(re.findall(r'<img src="images/[^"]*-scene\d\.jpg(?:\?v=\d+)?" alt="[^"]{6,}"', t)) == n_scene)
P('卡片含縮圖', f'<div class="article-thumb"><img src="images/{SD}-1900.jpg"' in (REPO / 'articles.html').read_text(encoding='utf-8'))
P('sitemap 含網址', slug in (REPO / 'sitemap.xml').read_text(encoding='utf-8'))

order = [re.search(r'article-(\d{8})-(\d{4})\.html', h) for h in
         re.findall(r'<a href="(article-[^"]+\.html)">', (REPO / 'articles.html').read_text(encoding='utf-8'))]
seq = [(m.group(1), m.group(2)) for m in order if m][:6]
bad = [(seq[k], seq[k+1]) for k in range(len(seq) - 1) if seq[k] < seq[k+1]]
P(f'列表前 6 條降序 {seq[:3]}', not bad)

print(f'=== {slug} ===')
for l in log:
    print('  -', l)
nbad = 0
for n, ok2 in checks:
    if not ok2:
        print('  [FAIL] ' + n)
        nbad += 1
print(f'  RESULT: {len(checks)-nbad}/{len(checks)} passed')
sys.exit(1 if nbad else 0)
