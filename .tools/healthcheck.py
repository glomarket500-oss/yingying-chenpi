# -*- coding: utf-8 -*-
"""陳皮網站全站健康檢查（發布前／推送前自動跑）

檢查項目（任一 FAIL 即回傳非 0，pre-push hook 會擋下推送）：
 1. 壞圖：任何 <img src> 指向不存在的檔案
 2. 超大圖：線上頁面用到的圖 >300KB
 3. 錯誤模板：文章使用 Hermes 的 nav-logo / class="brand"（本站 CSS 未定義）
 4. 缺場景圖：文章 figure < 2（只有封面或完全沒圖）
 5. 缺卡片縮圖：articles.html 的卡片沒有 article-thumb + img
 6. 簡體殘留：文章含常見簡體字
 7. 圖片來源字樣：出現「圖片來源／图片来源」（規範第 7 條禁止）
 8. 圖片未破快取：文章 <img> 沒帶 ?v=（換圖後手機容易看到舊圖）
 9. div 配對：<div> 與 </div> 數量不符
10. 場景圖 alt 缺失

用法：
    python healthcheck.py            # 全部檢查
    python healthcheck.py --quiet    # 只輸出失敗項
"""
import re
import sys
from pathlib import Path

REPO = Path(r'C:/Users/a/Desktop/chenpi-website')
IMG = REPO / 'images'
QUIET = '--quiet' in sys.argv
DUMP = '--dump' in sys.argv

SIMP = ('东个仓会录视记车这陈频诚护丰监签题买卖价钱产业广张报数标热现经统营认让议识'
        '资软钟钱摄变场体传艺镜农树讲还开采丰观众条课带团赚过们为说时间长实际关'
        '评论赞内药医书马鸟鱼')
SKIP_SHELL = {'yiyichenpicom_cssauth.html'}

problems = []
def bad(cat, detail):
    problems.append((cat, detail))

# ---- 基線：已知的歷史遺留不算新問題（2026-10-10 建立）----
BASELINE_FILE = Path(__file__).with_name('healthcheck-baseline.txt')
BASELINE = set()
if BASELINE_FILE.is_file():
    BASELINE = {l.strip() for l in BASELINE_FILE.read_text(encoding='utf-8').split('\n') if l.strip()}
def known(cat, detail):
    return f'[{cat}] {detail}' in BASELINE

pages = sorted(p for p in REPO.glob('*.html') if p.name not in SKIP_SHELL)
listed = re.findall(r'<a href="(article-[^"]+\.html)">',
                    (REPO / 'articles.html').read_text(encoding='utf-8')) if (REPO / 'articles.html').is_file() else []

# ---------- 1/8/9 全頁掃描 ----------
for p in pages:
    t = p.read_text(encoding='utf-8', errors='replace')
    for m in re.finditer(r'<img[^>]*src="([^"]+)"', t):
        u = m.group(1)
        bare = u.split('?')[0]
        if bare.startswith(('http', 'data:')):
            continue
        if not (REPO / bare).is_file():
            bad('壞圖', f'{p.name}: {u}')
    if '圖片來源' in t or '图片来源' in t:
        bad('圖片來源字樣', p.name)
    o, c = len(re.findall(r'<div[\s>]', t)), t.count('</div>')
    if o != c:
        bad('div 不配對', f'{p.name}: {o}/{c}')

# ---------- 2 超大圖 ----------
used = {}
for p in pages:
    t = p.read_text(encoding='utf-8', errors='replace')
    for m in re.finditer(r'<img[^>]*src="([^"]+)"', t):
        n = m.group(1).split('?')[0].split('/')[-1]
        used.setdefault(n, set()).add(p.name)
for n, ps in used.items():
    f = IMG / n
    if f.is_file() and f.stat().st_size > 300 * 1024:
        bad('超大圖', f'{n}  {f.stat().st_size/1024:.0f} KB  （{sorted(ps)[:2]}）')

# ---------- 3/4/6 文章掃描 ----------
article_pages = [p for p in pages if p.name.startswith('article-')]
for p in article_pages:
    t = p.read_text(encoding='utf-8', errors='replace')
    if 'nav-logo' in t.split('</style>')[-1] or 'class="brand"' in t.split('</style>')[-1]:
        bad('錯誤模板', f'{p.name}: 使用 nav-logo / brand')
    figs = t.count('<figure')
    if p.name in listed and figs < 2:
        bad('缺場景圖', f'{p.name}: figure={figs}')
    hits = sorted({ch for ch in SIMP if ch in t})
    if hits:
        bad('簡體殘留', f'{p.name}: {hits}')
    for m in re.finditer(r'<img[^>]*src="(images/[^"]+)"', t):
        if '?v=' not in m.group(1) and p.name in listed:
            bad('圖片未破快取', f'{p.name}: {m.group(1)}')
            break
    for m in re.finditer(r'<img[^>]*src="images/[^\"]*-scene\d[^\"]*"[^>]*>', t):
        if 'alt="' not in m.group(0) or re.search(r'alt=""', m.group(0)):
            bad('場景圖缺 alt', p.name)
            break

# ---------- 5 卡片縮圖 ----------
if (REPO / 'articles.html').is_file():
    h = (REPO / 'articles.html').read_text(encoding='utf-8')
    cards = re.findall(r'<article class="article-card">[\s\S]*?</article>', h)
    for c in cards:
        if 'article-thumb' not in c or '<img' not in c:
            m = re.search(r'<a href="([^"]+)"', c)
            bad('缺卡片縮圖', m.group(1) if m else '(未知)')

# ---------- 輸出 ----------
if not QUIET:
    print(f'檢查 {len(pages)} 個頁面、{len(article_pages)} 篇文章、{len(used)} 張引用圖')
if DUMP:
    for cat, d in problems:
        print(f'[DUMP] [{cat}] {d}')
    sys.exit(0)

from collections import Counter
new = [(c, d) for c, d in problems if not known(c, d)]
old = [(c, d) for c, d in problems if known(c, d)]

print(f'\n歷史遺留（基線內，不擋）：{len(old)} 項')
if old and not QUIET:
    for cat, n in Counter(c for c, _ in old).most_common():
        print(f'   [{cat}] {n} 項')

if new:
    print(f'\n❌ 新增問題：{len(new)} 項（健康檢查未通過）')
    for cat, n in Counter(c for c, _ in new).most_common():
        print(f'   [{cat}] {n} 項')
    print()
    for cat, d in new[:40]:
        print(f'   - [{cat}] {d}')
    if len(new) > 40:
        print(f'   … 另有 {len(new)-40} 項')
    sys.exit(1)

if not QUIET:
    print('✅ 健康檢查通過（沒有新增問題）')
sys.exit(0)
