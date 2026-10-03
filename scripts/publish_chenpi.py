#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
陈皮文章发布脚本 v4.1-fast
用法：python publish_chenpi.py --publish "草稿路径.md"
"""

import argparse
import glob
import html
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from opencc import OpenCC
    HK_CONVERTER = OpenCC('s2hk')
except ImportError:
    HK_CONVERTER = None

REPO_DIR = r"C:\Users\a\Desktop\chenpi-website"
SITE_URL = "https://www.yiyichenpi.com"
CHAR_CORRECT = chr(0x6EE2)
VAULT_DIR = f"C:\\Users\\a\\Desktop\\MianAI知识库\\MianAI知识库\\vault\\{CHAR_CORRECT}{CHAR_CORRECT}姐讲陈皮故事"


def hk_text(value):
    """转换为香港繁体，并统一正确人名写法为「滢滢」。"""
    if not isinstance(value, str):
        return value
    converted = HK_CONVERTER.convert(value) if HK_CONVERTER else value
    correct = chr(0x6EE2) * 2
    wrong_a = chr(0x7005) * 2
    wrong_b = chr(0x6EE2) + chr(0x7005)
    wrong_c = chr(0x7005) + chr(0x6EE2)
    return converted.replace(wrong_a, correct).replace(wrong_b, correct).replace(wrong_c, correct)


def read_md(md_path):
    content = Path(md_path).read_text(encoding="utf-8")
    fm, body = {}, content
    m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
        body = content[m.end():]
    # 解析tags列表
    tags_raw = fm.get('tags', '')
    if tags_raw.startswith('[') and tags_raw.endswith(']'):
        try:
            fm['tags'] = json.loads(tags_raw)
        except:
            fm['tags'] = [t.strip().strip('"').strip("'") for t in tags_raw[1:-1].split(',') if t.strip()]
    # 统一正文与 frontmatter 为香港繁体，并固定作者名为「滢滢」。
    fm = {k: hk_text(v) for k, v in fm.items()}
    if isinstance(fm.get('tags'), list):
        fm['tags'] = [hk_text(t) for t in fm['tags']]
    body = hk_text(body)
    return fm, body


def md_to_html(body):
    lines = body.split('\n')
    out, in_p, in_list, in_scene = [], False, False, False

    def close_p():
        nonlocal in_p
        if in_p: out.append('</p>'); in_p = False
    def close_list():
        nonlocal in_list
        if in_list: out.append('</ul>'); in_list = False
    def open_scene():
        nonlocal in_scene
        if not in_scene:
            out.append('<section class="scene">')
            in_scene = True
    def close_scene():
        nonlocal in_scene
        if in_scene:
            out.append('</section>')
            in_scene = False
    def format_dialogue(s):
        """把 > xxx說：「...」 转为 dialogue 区块，否则回 <blockquote>"""
        text = s[2:].strip()
        m = re.match(r'^(.+?)[說称讲问答叫喊叹][：:「『"\'](.+)[」』"\'。？?！!]*$', text)
        if m:
            who = m.group(1).strip()
            words = m.group(2).strip()
            return (f'<div class="dialogue"><div class="who">{html.escape(who)}</div>'
                    f'<p>{html.escape(words)}</p></div>')
        return f'<blockquote>{html.escape(text)}</blockquote>'

    for s in (l.rstrip() for l in lines):
        if s.startswith('## '):
            close_p(); close_list(); close_scene()
            open_scene()
            out.append(f'<h2>{s[3:]}</h2>')
        elif s.startswith('### '):
            close_p(); close_list()
            out.append(f'<h3>{s[4:]}</h3>')
        elif s.startswith('- '):
            close_p()
            if not in_list: out.append('<ul>'); in_list = True
            out.append(f'<li>{s[2:]}</li>')
        elif s.startswith('> '):
            close_p(); close_list()
            out.append(format_dialogue(s))
        elif s == '---':
            close_p(); close_list(); out.append('<hr>')
        elif not s:
            close_p(); close_list()
        else:
            close_list()
            if not in_p: out.append('<p>'); in_p = True
            escaped = html.escape(s, quote=False)
            escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
            escaped = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', escaped)
            out.append(escaped + ' ')

    close_p(); close_list(); close_scene()
    html_out = '\n'.join(out)
    # FAQ items → faq-item
    html_out = re.sub(
        r'<p>\s*<strong>(Q\d+[：:].*?)</strong>\s*(A：[\s\S]*?)</p>',
        r'<div class="faq-item"><p class="faq-question">\1</p><p class="faq-answer">\2</p></div>',
        html_out,
    )
    html_out = re.sub(
        r'(<h2>(?:FAQ )?常見問題</h2>)\s*((?:<div class="faq-item">[\s\S]*?</div>\s*)+)',
        r'\1\n<div class="faq-list">\n\2</div>',
        html_out,
    )
    html_out = html_out.replace('<p class="faq-answer">A：', '<p class="faq-answer">')
    return html_out


def extract_faqs(body):
    faqs = []
    for m in re.finditer(r'\*\*Q\d+[：:](.+?)\*\*\s*[A A][：:](.+?)(?=\n\n|\n\*\*Q|\n##|\Z)', body, re.DOTALL):
        faqs.append({"q": m.group(1).strip().rstrip('？').strip(), "a": m.group(2).strip()})
    return faqs


def build_html(title, body_html, tags, date_str, time_str, faqs, image_url, url, description="", image_source="公開報道配圖"):
    tag_list = tags if isinstance(tags, list) else ["新會陳皮"]
    tags_html = '\n'.join(f'<a href="#">{html.escape(str(t), quote=True)}</a>' for t in tag_list[:5])
    display_date = f"{date_str[:4]}年{date_str[5:7]}月{date_str[8:10]}日"
    iso_date = f"{date_str}T{time_str}+08:00"
    meta_description = html.escape(description or title, quote=True)
    meta_keywords = html.escape(','.join(str(t) for t in tag_list[:8]), quote=True)
    source_caption = (image_source or "").strip()
    no_source_markers = {"", "暫不署名", "暂不署名", "無", "无", "不寫來源", "不写来源", "none", "null"}
    article_image = ''
    if image_url:
        safe_image = html.escape(image_url, quote=True)
        if source_caption in no_source_markers:
            article_image = f'''<figure class="article-inline-image no-source">
    <img src="{safe_image}" alt="{html.escape(title, quote=True)}">
  </figure>'''
        else:
            safe_caption = html.escape(source_caption or "公開報道配圖", quote=False)
            article_image = f'''<figure class="article-inline-image">
    <img src="{safe_image}" alt="{html.escape(title, quote=True)}">
    <figcaption>圖片來源：{safe_caption}</figcaption>
  </figure>'''

    # FAQ tip-box HTML（插入文章正文结尾、CTA 之前）
    faq_html = ""
    if faqs:
        faq_items_html = "\n".join(
            f'                <p><strong>Q：{html.escape(f["q"])}</strong></p>\n                <p>A：{html.escape(f["a"])}</p>'
            for f in faqs
        )
        faq_html = f'''
        <div class="tip-box">
            <div class="label">常見問題</div>
{faq_items_html}
        </div>
'''

    blog = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": title, "description": description or title, "image": image_url, "datePublished": iso_date, "dateModified": iso_date, "author": {"@type": "Person", "name": "滢滢"}, "publisher": {"@type": "Organization", "name": "溢豐堂"}, "articleSection": "陳皮故事", "inLanguage": "zh-Hant", "contentLocation": {"@type": "Place", "name": "新會天馬村"}}

    local_business = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": "溢豐堂 · 滢滢家新會陳皮", "address": {"@type": "PostalAddress", "addressLocality": "新會區", "addressRegion": "廣東省", "addressCountry": "CN"}, "geo": {"@type": "GeoCoordinates", "latitude": 22.5317, "longitude": 113.0286}}

    faq_schema = ""
    if faqs:
        faq_items = [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
        faq_schema = f'\n<script type="application/ld+json">\n{json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_items}, ensure_ascii=False, indent=2)}\n</script>'

    embedded_style = '''
    <style>
        .article-wrap { max-width: 720px; margin: 0 auto; padding: 40px 5vw 60px; background: #fff; }
        .article-body { font-size: 1rem; line-height: 1.9; color: #333; }
        .article-body h2 { font-size: 1.4rem; color: #8B4513; margin: 36px 0 16px; padding-left: 14px; border-left: 4px solid #c9a96e; line-height: 1.4; font-weight: 700; }
        .article-body h3 { font-size: 1.1rem; color: #6b3410; margin: 20px 0 10px; font-weight: 700; }
        .article-body p { margin: 14px 0; }
        .article-body strong { color: #6b3410; }
        .article-body .scene { margin-bottom: 32px; }
        .article-body .dialogue { background: #fff; border-left: 3px solid #8B4513; padding: 14px 18px; margin: 20px 0; border-radius: 0 8px 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,.04); }
        .article-body .dialogue .who { font-weight: 700; color: #8B4513; font-size: .85rem; margin-bottom: 6px; }
        .article-body .dialogue p { font-size: .94rem; margin: 0; color: #555; }
        .article-body .faq-item { margin-bottom: 16px; padding: 12px; background: #faf8f3; border-radius: 8px; }
        .article-body .faq-item p { margin: 4px 0; }
    </style>'''

    return f'''<!DOCTYPE html>
<html lang="zh-HK">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | 溢豐堂 · 滢滢家新會陳皮</title>
<meta name="description" content="{meta_description}">
<meta name="keywords" content="{meta_keywords}">
<meta name="author" content="滢滢">
<link rel="canonical" href="{url}">
<meta name="geo.position" content="22.5317;113.0286">
<meta name="ICBM" content="22.5317, 113.0286">
<meta name="geo.placename" content="新會天馬村, 江門, 廣東">
<meta name="geo.region" content="CN-GD">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image_url}">
<meta property="og:locale" content="zh_HK">
<meta property="article:published_time" content="{iso_date}">
<meta property="article:modified_time" content="{iso_date}">
<meta property="article:author" content="滢滢">
<meta property="article:section" content="陳皮故事">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta_description}">
<meta name="twitter:image" content="{image_url}">
<link rel="stylesheet" href="css/style.css?v=5">
{embedded_style}
<script type="application/ld+json">
{json.dumps(blog, ensure_ascii=False, indent=2)}
</script>
<script type="application/ld+json">
{json.dumps(local_business, ensure_ascii=False, indent=2)}
</script>
{faq_schema}
</head>
<body>
    <nav class="nav">
        <a href="index.html" class="nav-logo">
            <span class="brand">溢豐堂</span>
            <span>滢滢家新會陳皮</span>
        </a>
        <div class="nav-links">
            <a href="index.html">首頁</a>
            <a href="articles.html" class="active">陳皮故事</a>
            <a href="videos.html">短視頻</a>
            <a href="live.html">直播間</a>
            <a href="about.html">認識滢滢</a>
            <a href="contact.html">銷售陳皮</a>
        </div>
    </nav>

    <div class="breadcrumb">
        <a href="index.html">首頁</a> &gt;
        <a href="articles.html">陳皮故事</a> &gt;
        <span>{title}</span>
    </div>

    <main class="article-wrap">
        <article class="article-detail">
            <header class="article-header">
                <h1>{title}</h1>
                <div class="article-meta">
                    <span>📅 {display_date} {time_str}</span>
                    <span>👤 滢滢</span>
                    <span>📍 新會天馬村</span>
                    <span>🕐 閱讀約8分鐘</span>
                </div>
                <div class="article-tags">{tags_html}</div>
            </header>
            {article_image}
            <div class="article-body">{body_html}</div>
            {faq_html}
            <div class="cta-box">
                <h3>想買正宗新會陳皮？</h3>
                <p>滢滢家天馬村果園直發，手工開皮、自然生曬、幹倉陳化。<br>不滿意七天無理由退，我敢這麼說，是因為我對自己的陳皮有信心。</p>
                <a href="contact.html">📱 加滢滢微信，了解詳情</a>
            </div>
            <div class="related">
                <h3>📖 你可能還想看</h3>
                <div class="related-item">
                    <a href="articles.html">
                        <h4>查看全部陳皮故事</h4>
                        <p>傾聽每一塊陳皮的聲音</p>
                    </a>
                </div>
            </div>
        </article>
    </main>

    <footer>
        <p>© 2026 溢豐堂 · 滢滢家新會陳皮 ｜
            <a href="contact.html" style="color:#8B4513">聯繫我們</a></p>
    </footer>

    <div id="cookie-bar" style="display:none;position:fixed;bottom:0;left:0;right:0;background:#8B4513;color:#fff;padding:12px 20px;text-align:center;z-index:9999;font-size:.85rem;">
        本網站使用 Cookie 改善您的體驗。
        <button onclick="document.getElementById('cookie-bar').style.display='none';localStorage.setItem('cookie_consent_chenpi','yes')"
                style="background:#fff;color:#8B4513;border:none;padding:6px 16px;border-radius:16px;margin-left:12px;cursor:pointer">
            確定
        </button>
    </div>
    <script>if(!localStorage.getItem('cookie_consent_chenpi')){{document.getElementById('cookie-bar').style.display='block';}}</script>
</body>
</html>'''


def update_index(title, abstract, display_date, time_str, file_name, image_url="", image_source="公開報道配圖"):
    idx_path = os.path.join(REPO_DIR, "index.html")
    with open(idx_path, encoding='utf-8') as f:
        page_html = f.read()

    image_html = ""
    if image_url:
        safe_image = html.escape(image_url, quote=True)
        no_source_markers = {"", "暫不署名", "暂不署名", "無", "无", "不寫來源", "不写来源", "none", "null"}
        if (image_source or "").strip() in no_source_markers:
            image_html = f'''<figure class="featured-image no-source">
                <img src="{safe_image}" alt="{html.escape(title, quote=True)}">
            </figure>'''
        else:
            source_caption = html.escape(image_source or "公開報道配圖", quote=False)
            image_html = f'''<figure class="featured-image">
                <img src="{safe_image}" alt="{html.escape(title, quote=True)}">
                <figcaption>圖片來源：{source_caption}</figcaption>
            </figure>'''

    new_featured = f'''<article class="article-card article-featured">
            <div class="article-meta">
                <span class="article-date">{display_date} {time_str}</span>
                <span class="article-tag">#陳皮故事</span>
            </div>
            <h3><a href="{file_name}">{title}</a></h3>
            {image_html}
            <p>{abstract}</p>'''

    new_featured += '''
            <div class="article-cta">
                <a href="{file_name}" class="btn">讀完整故事 →</a>
            </div>
        </article>'''.replace('{file_name}', file_name)

    # 替换 featured 区块
    page_html = re.sub(r'<article class="article-card article-featured".*?</article>', new_featured, page_html, count=1, flags=re.DOTALL)
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(page_html)


def update_articles(file_name, title, abstract, display_date, time_str, tags):
    """先 fetch 线上 sha，再在内存中修改，最后推送。"""
    import urllib.request
    art_path = os.path.join(REPO_DIR, "articles.html")
    API = "https://api.github.com/repos/glomarket500-oss/yingying-chenpi/contents/articles.html"
    try:
        req = urllib.request.Request(API,
            headers={"Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN','')}",
                     "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        with urllib.request.urlopen(req, timeout=15) as r:
            online_sha = json.loads(r.read()).get("sha", "")
    except:
        online_sha = ""

    with open(art_path, encoding='utf-8') as f:
        html = f.read()

    tag_str = " · ".join(tags[:3]) if isinstance(tags, list) else "陳皮故事"
    new_item = f'''<article class="article-card">
        <a href="{file_name}">
          <h3>{title}</h3>
          <p class="meta">{display_date} {time_str} | {tag_str}</p>
          <p class="excerpt">{abstract}</p>
          <span class="read-more">閱讀全文 →</span>
        </a>
      </article>'''

    html = html.replace('<section class="article-list">', '<section class="article-list">\n      ' + new_item, 1)

    import base64
    body = json.dumps({
        "message": f"update articles.html: add {file_name}",
        "sha": online_sha,
        "content": base64.b64encode(html.encode("utf-8")).decode()
    }).encode()
    req = urllib.request.Request(API, data=body,
        headers={"Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN','')}",
                 "Content-Type": "application/json",
                 "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read())
            print(f"   ✅ articles.html 更新: {result.get('commit',{}).get('sha','')[:8]}")
    except Exception as e:
        print(f"   ⚠️ articles.html 更新失敗: {e}")
        # 回写到本地文件，不阻断
        with open(art_path, 'w', encoding='utf-8') as f:
            f.write(html)


def update_sitemap(file_name):
    """更新 sitemap.xml，fetch 线上 sha。"""
    import urllib.request, base64
    sm_path = os.path.join(REPO_DIR, "sitemap.xml")
    API = "https://api.github.com/repos/glomarket500-oss/yingying-chenpi/contents/sitemap.xml"
    try:
        req = urllib.request.Request(API,
            headers={"Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN','')}",
                     "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        with urllib.request.urlopen(req, timeout=15) as r:
            online_sha = json.loads(r.read()).get("sha", "")
    except:
        online_sha = ""

    with open(sm_path, encoding='utf-8') as f:
        xml = f.read()
    url_tag = f"<url><loc>{SITE_URL}/{file_name}</loc></url>"
    if url_tag not in xml:
        xml = xml.replace("</urlset>", f"  {url_tag}\n</urlset>")
        body = json.dumps({
            "message": f"update sitemap.xml: add {file_name}",
            "sha": online_sha,
            "content": base64.b64encode(xml.encode("utf-8")).decode()
        }).encode()
        req = urllib.request.Request(API, data=body,
            headers={"Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN','')}",
                     "Content-Type": "application/json",
                     "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
            method="PUT")
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                result = json.loads(r.read())
                print(f"   ✅ sitemap.xml 更新: {result.get('commit',{}).get('sha','')[:8]}")
        except Exception as e:
            print(f"   ⚠️ sitemap.xml 更新失敗: {e}")
            with open(sm_path, 'w', encoding='utf-8') as f:
                f.write(xml)


def verify_online(url):
    """验证线上页面 HTTP 200。"""
    import urllib.request
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=20) as r:
                status = r.status
                ct = r.headers.get("Content-Type", "")
                return status == 200, f"HTTP {status} ({ct[:40]})"
        except Exception as e:
            if attempt < 2:
                import time; time.sleep(5)
            continue
    return False, str(e)[:80]


def git_push():
    os.chdir(REPO_DIR)
    subprocess.run(["git", "add", "index.html", "articles.html", "article-*.html", "images/*", ".pending_push"], capture_output=True, timeout=10)

    msg = f"feat: 发布新文章 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    r = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        if "nothing" in r.stdout.lower() or "nothing" in r.stderr.lower():
            return True, "无变更"
        return False, r.stderr[:100]

    try:
        r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return False, "GitHub 推送超时，文章已生成但尚未完成远程同步"
    except OSError as exc:
        return False, f"Git 推送无法启动：{exc}"
    if r.returncode == 0:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        return True, f"已推送 ({h.stdout.strip()})"
    return False, (r.stderr or r.stdout or "Git 推送失败").strip()[:160]


def publish(draft_path):
    print(f"\n📤 发布: {os.path.basename(draft_path)}")

    fm, body = read_md(draft_path)
    title = fm.get("title", "未命名")
    date_str = fm.get("date", datetime.now().strftime("%Y-%m-%d"))
    time_str = fm.get("publish_time", datetime.now().strftime("%H:%M:%S"))
    tags = fm.get("tags", ["新會陳皮"])
    abstract = fm.get("description", "")
    image = fm.get("image", "").strip()
    image_source = fm.get("image_source", "公開報道配圖").strip()
    if not image or "homepage-hero" in image or image.endswith("/images/chenpi-hero.jpg"):
        raise ValueError("❌ 发布错误：每篇文章必须先搜索并填写独立主题图片，不能使用首页统一图片")

    # 生成HTML
    faqs = extract_faqs(body)
    body_html = md_to_html(body)
    file_name = f"article-{date_str.replace('-', '')}-{time_str.replace(':', '')[:4]}.html"
    url = f"{SITE_URL}/{file_name}"

    html = build_html(title, body_html, tags, date_str, time_str, faqs, image, url, abstract, image_source)

    with open(os.path.join(REPO_DIR, file_name), 'w', encoding='utf-8') as f:
        f.write(html)

    display_date = f"{date_str[:4]}年{date_str[5:7]}月{date_str[8:10]}日"
    update_index(title, abstract, display_date, time_str, file_name, image, image_source)
    update_articles(file_name, title, abstract, display_date, time_str, tags)
    update_sitemap(file_name)

    ok, msg = git_push()
    if not ok:
        print(f"   ❌ GitHub 推送失败: {msg}")
        raise RuntimeError(f"❌ 发布错误：GitHub 推送失败 — {msg}")

    # 推后验证
    print(f"   🔍 验证线上: {url}")
    ok_verify, detail = verify_online(url)
    if not ok_verify:
        raise RuntimeError(f"❌ 发布错误：线上验证失败 — {detail}")

    print(f"   ✅ 验证通过")

    # 验证通过后再归档草稿
    pub_dir = f"{VAULT_DIR}\\已发布"
    os.makedirs(pub_dir, exist_ok=True)
    shutil.move(draft_path, os.path.join(pub_dir, os.path.basename(draft_path)))
    # 清理待推送标记
    pending_flag = os.path.join(REPO_DIR, ".pending_push")
    if os.path.exists(pending_flag):
        os.remove(pending_flag)

    print(f"\n🎉 {url}")
    return True


def get_latest_draft():
    draft_dir = f"{VAULT_DIR}\\草稿"
    files = [(f, os.path.getmtime(os.path.join(draft_dir, f))) for f in os.listdir(draft_dir) if f.endswith('.md')]
    if not files:
        return None
    files.sort(key=lambda x: x[1], reverse=True)
    return os.path.join(draft_dir, files[0][0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', nargs='?', const=None, help='发布草稿')
    parser.add_argument('--list', action='store_true', help='列出草稿')
    args = parser.parse_args()

    if args.list:
        draft_dir = f"{VAULT_DIR}\\草稿"
        for f in sorted(os.listdir(draft_dir), reverse=True):
            if f.endswith('.md'):
                print(f"  - {f}")
        return

    if args.publish is not None:
        draft = args.publish if args.publish else get_latest_draft()
        if draft:
            publish(draft)
        else:
            print("❌ 无草稿")
        return


if __name__ == "__main__":
    main()
