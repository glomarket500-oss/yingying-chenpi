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
SITE_URL = "https://yingying-chenpi.vercel.app"
CHAR_CORRECT = chr(0x6EE2)
VAULT_DIR = f"C:\\Users\\a\\Desktop\\MianAI知识库\\MianAI知识库\\{CHAR_CORRECT}{CHAR_CORRECT}姐讲陈皮故事"


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
    out, in_p, in_list = [], False, False

    def close_p():
        nonlocal in_p
        if in_p: out.append('</p>'); in_p = False
    def close_list():
        nonlocal in_list
        if in_list: out.append('</ul>'); in_list = False

    for s in (l.rstrip() for l in lines):
        if s.startswith('## '):
            close_p(); close_list()
            heading = s[3:]
            heading_class = 'section-heading'
            if '開場' in heading:
                heading_class += ' section-opening'
            elif re.match(r'^[一二三四五六七八九十]+、', heading):
                heading_class += ' section-act'
            elif '常見問題' in heading:
                heading_class += ' section-faq'
            elif '茶識' in heading or '小貼士' in heading:
                heading_class += ' section-tips'
            elif '結語' in heading:
                heading_class += ' section-ending'
            out.append(f'<h2 class="{heading_class}">{heading}</h2>')
        elif s.startswith('### '):
            close_p(); close_list(); out.append(f'<h3>{s[4:]}</h3>')
        elif s.startswith('- '):
            close_p()
            if not in_list: out.append('<ul>'); in_list = True
            out.append(f'<li>{s[2:]}</li>')
        elif s.startswith('> '):
            close_p(); close_list(); out.append(f'<blockquote>{s[2:]}</blockquote>')
        elif s == '---':
            close_p(); close_list(); out.append('<hr>')
        elif not s:
            close_p(); close_list()
        else:
            close_list()
            if not in_p: out.append('<p>'); in_p = True
            # 先转义正文，再恢复 Markdown 粗体，避免生成的 <strong> 被再次转义。
            escaped = html.escape(s, quote=False)
            escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
            escaped = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<em>\1</em>', escaped)
            out.append(escaped + ' ')
    close_p(); close_list()
    html_out = '\n'.join(out)
    # 将 FAQ 的 Markdown 段落转换成独立问答卡片，避免问题和答案挤在一个 p 内。
    html_out = re.sub(
        r'<p>\s*<strong>(Q\d+[：:].*?)</strong>\s*(A：[\s\S]*?)</p>',
        r'<div class="faq-item"><p class="faq-question">\1</p><p class="faq-answer">\2</p></div>',
        html_out,
    )
    html_out = re.sub(
        r'(<h2(?: class="[^"]+")?>(?:FAQ )?常見問題</h2>)\s*((?:<div class="faq-item">[\s\S]*?</div>\s*)+)',
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


def build_html(title, body_html, tags, date_str, time_str, faqs, image_url, url, description=""):
    tag_list = tags if isinstance(tags, list) else ["新會陳皮"]
    tags_html = '\n'.join(f'<a href="#">{html.escape(str(t), quote=True)}</a>' for t in tag_list[:5])
    display_date = f"{date_str[:4]}年{date_str[5:7]}月{date_str[8:10]}日"
    iso_date = f"{date_str}T{time_str}+08:00"
    meta_description = html.escape(description or title, quote=True)
    meta_keywords = html.escape(','.join(str(t) for t in tag_list[:8]), quote=True)
    article_image = ''
    if image_url:
        safe_image = html.escape(image_url, quote=True)
        article_image = f'''<figure class="article-inline-image">
    <img src="{safe_image}" alt="{html.escape(title, quote=True)}">
    <figcaption>圖片來源：公開報道配圖｜中國新聞網</figcaption>
  </figure>'''

    faq_schema = ""
    if faqs:
        items = [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
        faq_schema = f'<script type="application/ld+json">\n{json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": items}, ensure_ascii=False, indent=2)}\n</script>'

    blog = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": title, "description": description or title, "image": image_url, "datePublished": iso_date, "dateModified": iso_date, "author": {"@type": "Person", "name": "滢滢"}, "publisher": {"@type": "Organization", "name": "溢豐堂"}, "articleSection": "陳皮故事", "inLanguage": "zh-Hant", "contentLocation": {"@type": "Place", "name": "新會天馬村"}}
    local_business = {"@context": "https://schema.org", "@type": "LocalBusiness", "name": "溢豐堂 · 滢滢家新會陳皮", "address": {"@type": "PostalAddress", "addressLocality": "新會區", "addressRegion": "廣東省", "addressCountry": "CN"}, "geo": {"@type": "GeoCoordinates", "latitude": 22.5317, "longitude": 113.0286}}

    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
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
<meta property="article:author" content="滢滢">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta_description}">
<meta name="twitter:image" content="{image_url}">
<link rel="stylesheet" href="css/style.css">
<script type="application/ld+json">\n{json.dumps(blog, ensure_ascii=False, indent=2)}\n</script>
<script type="application/ld+json">\n{json.dumps(local_business, ensure_ascii=False, indent=2)}\n</script>
{faq_schema}
</head>
<body>
<header class="site-header">
  <nav class="main-nav">
    <a href="index.html" class="logo">溢豐堂 · 滢滢家新會陳皮</a>
    <ul>
      <li><a href="index.html">首頁</a></li>
      <li><a href="articles.html" class="active">陳皮故事</a></li>
      <li><a href="videos.html">短視頻</a></li>
      <li><a href="live.html">直播間</a></li>
      <li><a href="about.html">認識滢滢</a></li>
      <li><a href="contact.html">銷售陳皮</a></li>
    </ul>
  </nav>
</header>

<div class="breadcrumb">
  <a href="index.html">首頁</a> ·
  <a href="articles.html">陳皮故事</a> ·
  {title}
</div>

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
  <div class="article-content">{body_html}</div>
  <div class="cta-box">
    <h3>想買正宗新會陳皮？</h3>
    <p>滢滢家天馬村果園直發，手工開皮、自然生曬、乾倉陳化。</p>
    <p>📱 加滢滢微信，了解詳情</p>
  </div>
  <div class="related">
    <h3>📖 你可能還想看</h3>
    <p><a href="articles.html">查看全部陳皮故事 →</a></p>
  </div>
</article>

<footer>
  <p>📍 新會陳皮村南門牌坊 G04 | 滢滢姐陳皮文化傳播 | 📞 19307501495</p>
  <p>© 溢豐堂 · 滢滢 · 新會天馬村 · <a href="contact.html">聯繫我們</a></p>
</footer>
</body>
</html>'''


def update_index(title, abstract, display_date, time_str, file_name, image_url=""):
    idx_path = os.path.join(REPO_DIR, "index.html")
    with open(idx_path, encoding='utf-8') as f:
        page_html = f.read()

    image_html = ""
    if image_url:
        safe_image = html.escape(image_url, quote=True)
        image_html = f'''<figure class="featured-image">
                <img src="{safe_image}" alt="{html.escape(title, quote=True)}">
                <figcaption>圖片來源：公開報道配圖｜中國新聞網</figcaption>
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
    art_path = os.path.join(REPO_DIR, "articles.html")
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

    with open(art_path, 'w', encoding='utf-8') as f:
        f.write(html)


def git_push():
    os.chdir(REPO_DIR)
    subprocess.run(["git", "add", "index.html", "articles.html", "article-*.html", "images/*"], capture_output=True, timeout=10)

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
    if not image or "homepage-hero" in image or image.endswith("/images/chenpi-hero.jpg"):
        raise ValueError("每篇文章必须先搜索并填写独立主题图片，不能使用首页统一图片")

    # 生成HTML
    faqs = extract_faqs(body)
    body_html = md_to_html(body)
    file_name = f"article-{date_str.replace('-', '')}-{time_str.replace(':', '')[:4]}.html"
    url = f"{SITE_URL}/{file_name}"

    html = build_html(title, body_html, tags, date_str, time_str, faqs, image, url, abstract)

    with open(os.path.join(REPO_DIR, file_name), 'w', encoding='utf-8') as f:
        f.write(html)

    display_date = f"{date_str[:4]}年{date_str[5:7]}月{date_str[8:10]}日"
    update_index(title, abstract, display_date, time_str, file_name, image)
    update_articles(file_name, title, abstract, display_date, time_str, tags)

    ok, msg = git_push()
    if not ok:
        print(f"   ❌ {msg}")
        return False
    print(f"   ✅ {msg}")

    # 移动草稿
    pub_dir = f"{VAULT_DIR}\\已发布"
    os.makedirs(pub_dir, exist_ok=True)
    shutil.move(draft_path, os.path.join(pub_dir, os.path.basename(draft_path)))

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
