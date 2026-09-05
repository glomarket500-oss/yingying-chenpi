"""
陈皮文章生成 + 发布系统 v4
功能：
- 基于 DEFAULT_TEMPLATE.md 自动生成新文章草稿
- 解析 Markdown frontmatter
- Markdown → HTML 转换
- FAQ → FAQPage Schema 自动提取
- 完整 SEO/GEO 元数据生成
- 发布前格式自检（错别字/标签引号/必备元素/时间秒/FAQ数量）
- git push 自动重试 10 次/5分钟
- Vercel 部署验证

使用方法：
  python publish_chenpi.py --generate               # 基于默认模板自动生成新文章
  python publish_chenpi.py --publish draft.md        # 发布指定草稿
  python publish_chenpi.py --publish                  # 自动选最新草稿
"""

import os
import re
import sys
import json
import shutil
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ==================== 配置 ====================
SITE_URL = "https://yingying-chenpi.vercel.app"
REPO_DIR = r"C:\Users\a\Desktop\chenpi-website"
CHAR_CORRECT = chr(0x6EE2)  # 瀅

VAULT_DIR = f"C:\\Users\\a\\Desktop\\MianAI知识库\\vault\\{CHAR_CORRECT}{CHAR_CORRECT}姐讲陈皮故事"
DRAFT_DIR = f"{VAULT_DIR}\\草稿"
PUBLISHED_DIR = f"{VAULT_DIR}\\已发布"

SCRIPTS_DIR = Path(__file__).parent
DEFAULT_TEMPLATE_PATH = SCRIPTS_DIR / "DEFAULT_TEMPLATE.md"

# Vercel 部署等待秒数
VERCEL_DEPLOY_WAIT = 5

# ==================== 工具函数 ====================


def search_hot_news():
    """搜索当天陈皮热点新闻（占位，可接入 web_search）"""
    return "2026 新會陳皮"


def escape_html(text):
    """转义 HTML 特殊字符，并去除首尾引号"""
    if not text:
        return ""
    text = str(text).strip()
    # 去除首尾的引号（包括英文和中文引号）
    text = text.strip('"').strip("'").strip('"').strip("'")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text


def parse_frontmatter(content):
    """解析 YAML frontmatter"""
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not match:
        return {}, content
    fm = match.group(1)
    body = content[match.end():]
    meta = {}
    for line in fm.split('\n'):
        m = re.match(r'^(\w+):\s*(.*)$', line)
        if m:
            key = m.group(1)
            value = m.group(2)
            # 去除首尾引号
            value = value.strip().strip('"').strip("'")
            # 列表类型
            if value.startswith('[') and value.endswith(']'):
                try:
                    value = json.loads(value)
                except Exception:
                    pass
            meta[key] = value
    return meta, body


def inline_format(text):
    """Markdown 内联格式转 HTML（粗体、斜体、链接）"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def md_to_html(md_body):
    """极简 Markdown → HTML"""
    lines = md_body.split('\n')
    out = []
    in_p = False
    in_list = False

    def close_p():
        nonlocal in_p
        if in_p:
            out.append('</p>')
            in_p = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append('</ul>')
            in_list = False

    for line in lines:
        s = line.rstrip()

        # 标题
        if s.startswith('## '):
            close_p(); close_list()
            out.append(f'<h2>{inline_format(escape_html(s[3:]))}</h2>')
        elif s.startswith('### '):
            close_p(); close_list()
            out.append(f'<h3>{inline_format(escape_html(s[4:]))}</h3>')

        # 列表
        elif s.startswith('- '):
            close_p()
            if not in_list:
                out.append('<ul>')
                in_list = True
            out.append(f'<li>{inline_format(escape_html(s[2:]))}</li>')

        # 引用
        elif s.startswith('> '):
            close_p(); close_list()
            out.append(f'<blockquote>{inline_format(escape_html(s[2:]))}</blockquote>')

        # 表格（简版）
        elif s.startswith('|'):
            close_p(); close_list()
            cells = [c.strip() for c in s.strip('|').split('|')]
            if all(re.match(r'^-+$', c) for c in cells):
                continue  # 分隔行
            tag = 'th' if not hasattr(md_to_html, '_in_table') else 'td'
            if not hasattr(md_to_html, '_in_table') or not md_to_html._in_table:
                out.append('<table>')
                md_to_html._in_table = True
                tag = 'th'
            else:
                tag = 'td'
            out.append('<tr>' + ''.join(f'<{tag}>{inline_format(escape_html(c))}</{tag}>' for c in cells) + '</tr>')

        # 分隔线
        elif s == '---':
            close_p(); close_list()
            if hasattr(md_to_html, '_in_table') and md_to_html._in_table:
                out.append('</table>')
                md_to_html._in_table = False
            out.append('<hr>')

        # 空行
        elif not s:
            close_p(); close_list()
            if hasattr(md_to_html, '_in_table') and md_to_html._in_table:
                out.append('</table>')
                md_to_html._in_table = False

        # 段落
        else:
            close_list()
            if not in_p:
                out.append('<p>')
                in_p = True
            out.append(inline_format(escape_html(s)) + ' ')

    close_p(); close_list()
    if hasattr(md_to_html, '_in_table') and md_to_html._in_table:
        out.append('</table>')
        md_to_html._in_table = False
    return '\n'.join(out)


def extract_faqs(body_md):
    """从 Markdown 正文提取 FAQ（**Q1：xxx？** A：xxx 格式）"""
    faqs = []
    pattern = re.compile(r'\*\*Q\d+[：:](.+?)\*\*\s*[A A][：:](.+?)(?=\n\n|\n\*\*Q|\n##|\Z)', re.DOTALL)
    for m in pattern.finditer(body_md):
        q = m.group(1).strip().rstrip('？').rstrip('?').strip()
        a = m.group(2).strip()
        faqs.append({"q": q, "a": a})
    return faqs


def build_faq_schema(faqs):
    """构建 FAQPage JSON-LD"""
    if not faqs:
        return ""
    items = []
    for f in faqs:
        items.append({
            "@type": "Question",
            "name": f["q"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f["a"]
            }
        })
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": items
    }
    return f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n</script>'


def check_format(html, md_body):
    """发布前格式自检（关键错误中止）"""
    errors = []
    warnings = []

    # 1. 错别字检查
    for wrong in [chr(0x7005), chr(0x6ED1), chr(0x6EDE), chr(0x6E80)]:
        cnt = html.count(wrong)
        if cnt > 0:
            errors.append(f"错别字 U+{ord(wrong):04X}: {cnt}处")

    # 2. 必备元素检查
    required = [
        ('article-detail', '<article class="article-detail">'),
        ('blogposting', '"@type": "BlogPosting"'),
        ('faqpage', '"@type": "FAQPage"'),
        ('canonical', 'rel="canonical"'),
        ('geoposition', 'geo.position'),
        ('icbm', 'ICBM'),
    ]
    for name, marker in required:
        if marker not in html:
            errors.append(f"必备元素缺失: {name}")

    # 3. 外部CSS引用
    if 'href="css/style.css"' not in html:
        warnings.append("外部CSS引用未找到")

    # 4. FAQ数量一致
    faqs = extract_faqs(md_body)
    schema_count = html.count('"@type": "Question"')
    if faqs and schema_count != len(faqs):
        warnings.append(f"FAQ数量不一致：Markdown={len(faqs)}, Schema={schema_count}")

    return errors, warnings


# ==================== HTML 生成 ====================


def generate_full_html(title, body_html, tags, date_str, time_str, faqs, image_url, url, author="瀅瀅"):
    """生成完整HTML（含SEO/GEO/Schema）"""
    if isinstance(tags, str):
        tag_list = [t.strip().strip('"').strip("'") for t in re.findall(r'\[?["\']([^"\']+)["\']\]?', tags) if t.strip()]
        if not tag_list:
            tag_list = [t.strip() for t in tags.split(',')]
    else:
        tag_list = tags or []

    tag_list = [escape_html(t).strip('"').strip("'") for t in tag_list[:5]]

    description = f"{title}——{author}姐在天马村仓库的实拍记录，用镜头讲述新会陈皮的真实故事。"
    keywords = "新会陈皮,陈皮收藏,陈皮年份,陈皮价格,陈皮储存,瀅瀅姐,天马村"

    # 转换时间
    display_date = f"{date_str[:4]}年{date_str[5:7]}月{date_str[8:10]}日"
    iso_date = f"{date_str}T{time_str}+08:00"

    # 标签HTML
    tags_html = '\n'.join(f'<a href="#">{t}</a>' for t in tag_list) if tag_list else '<a href="#">新會陳皮</a>'

    # FAQ Schema
    faq_schema = build_faq_schema(faqs)

    # BlogPosting Schema
    blog_posting_schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "image": image_url,
        "datePublished": iso_date,
        "dateModified": iso_date,
        "author": {
            "@type": "Person",
            "name": author,
            "url": SITE_URL + "/about.html"
        },
        "publisher": {
            "@type": "Organization",
            "name": "溢豐堂",
            "logo": {
                "@type": "ImageObject",
                "url": SITE_URL + "/images/logo.png"
            }
        },
        "articleSection": "陳皮日記",
        "keywords": keywords,
        "wordCount": len(body_html),
        "inLanguage": "zh-Hant"
    }

    person_schema = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": author,
        "jobTitle": "新會陳皮文化傳播者",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "新會",
            "addressRegion": "江門",
            "addressCountry": "CN"
        },
        "url": SITE_URL
    }

    local_business_schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "溢豐堂 · 瀅瀅家新會陳皮",
        "image": image_url,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "新會陳皮村南門牌坊 G04",
            "addressLocality": "新會",
            "addressRegion": "江門",
            "addressCountry": "CN"
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": "22.5317",
            "longitude": "113.0286"
        },
        "telephone": "+86-19307501495",
        "url": SITE_URL,
        "priceRange": "$$"
    }

    def jsonld(obj):
        return f'<script type="application/ld+json">\n{json.dumps(obj, ensure_ascii=False, indent=2)}\n</script>'

    html = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape_html(title)} | 溢豐堂 · 瀅瀅家新會陳皮</title>
<meta name="description" content="{escape_html(description)}">
<meta name="keywords" content="{escape_html(keywords)}">
<meta name="author" content="{escape_html(author)}">
<link rel="canonical" href="{url}">

<!-- SEO GEO Meta -->
<meta name="geo.position" content="22.5317;113.0286">
<meta name="geo.placename" content="新會, 江門, 廣東">
<meta name="geo.region" content="CN-GD">
<meta name="ICBM" content="22.5317, 113.0286">

<!-- Open Graph -->
<meta property="og:type" content="article">
<meta property="og:locale" content="zh_HK">
<meta property="og:title" content="{escape_html(title)}">
<meta property="og:description" content="{escape_html(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image_url}">
<meta property="og:site_name" content="溢豐堂">
<meta property="article:published_time" content="{iso_date}">
<meta property="article:modified_time" content="{iso_date}">
<meta property="article:author" content="{escape_html(author)}">
<meta property="article:section" content="陳皮日記">
<meta property="article:tag" content="新會陳皮">
<meta property="article:tag" content="陳皮收藏">
<meta property="article:tag" content="陳皮年份">
<meta property="article:tag" content="陳皮價格">
<meta property="article:tag" content="天馬村">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape_html(title)}">
<meta name="twitter:description" content="{escape_html(description)}">
<meta name="twitter:image" content="{image_url}">

<!-- Stylesheet -->
<link rel="stylesheet" href="css/style.css">

<!-- Schema.org -->
{jsonld(blog_posting_schema)}
{faq_schema}
{jsonld(person_schema)}
{jsonld(local_business_schema)}
</head>
<body>

<header class="site-header">
  <nav class="main-nav">
    <a href="index.html" class="logo">溢豐堂 · 瀅瀅家新會陳皮</a>
    <ul>
      <li><a href="index.html">首頁</a></li>
      <li><a href="articles.html" class="active">陳皮日記</a></li>
      <li><a href="videos.html">短視頻</a></li>
      <li><a href="live.html">直播間</a></li>
      <li><a href="about.html">認識瀅瀅</a></li>
      <li><a href="contact.html">買陳皮</a></li>
    </ul>
  </nav>
</header>

<div class="breadcrumb">
  <a href="index.html">首頁</a> ·
  <a href="articles.html">陳皮日記</a> ·
  {escape_html(title)}
</div>

<article class="article-detail">
  <header class="article-header">
    <h1>{escape_html(title)}</h1>
    <div class="article-meta">
      <span>📅 {display_date} {time_str}</span>
      <span>👤 {escape_html(author)}</span>
      <span>📍 新會天馬村</span>
      <span>🕐 閱讀約8分鐘</span>
    </div>
    <div class="article-tags">
      {tags_html}
    </div>
  </header>

  <div class="article-content">
{body_html}
  </div>

  <div class="cta-box">
    <h3>想買正宗新會陳皮？</h3>
    <p>瀅瀅家天馬村果園直發，手工開皮、自然生曬、乾倉陳化。</p>
    <p>不滿意七天無理由退，我敢這麼說，是因為我對自己的陳皮有信心。</p>
    <p>📱 加瀅瀅微信，了解詳情</p>
  </div>

  <div class="related">
    <h3>📖 你可能還想看</h3>
    <p><a href="articles.html">查看全部陳皮故事 →</a></p>
  </div>
</article>

<footer>
  <p>📍 新會陳皮村南門牌坊 G04 | 瀅瀅姐陳皮文化傳播 | 📞 [REDACTED] | QQ [REDACTED] | 微信 [REDACTED]</p>
  <p>© 溢豐堂 · 瀅瀅 · 新會天馬村 · <a href="contact.html">聯繫我們</a></p>
  <p class="social-links">
    <a href="#">📕 小紅書</a>
    <a href="#">📱 微信</a>
    <a href="#">🎵 抖音</a>
  </p>
  <p class="publish-time">發佈時間：{display_date} {time_str}</p>
</footer>

</body>
</html>'''
    return html


# ==================== 发布流程 ====================


def update_index_featured(title, abstract, display_date, time_str, file_name):
    """更新 index.html featured 区域"""
    index_path = os.path.join(REPO_DIR, "index.html")
    with open(index_path, encoding="utf-8") as f:
        html = f.read()

    # 找到 featured 区块
    pattern = re.compile(
        r'(<div class="featured-article">|<article class="featured">)(.*?)(</div>|</article>)',
        re.DOTALL
    )

    new_featured = f'''<article class="featured">
        <a href="{file_name}">
          <h2>{escape_html(title)}</h2>
          <p class="meta">{display_date} {time_str} | 新會陳皮</p>
          <p class="excerpt">{escape_html(abstract)}</p>
          <span class="read-more">閱讀全文 →</span>
        </a>
      </article>'''

    if pattern.search(html):
        html = pattern.sub(new_featured + r'\3', html, count=1)
    else:
        # 没找到就插入到 main 开始处
        html = html.replace('<main', new_featured + '\n\n<main', 1)

    with open(index_path, 'w', encoding="utf-8") as f:
        f.write(html)


def insert_to_articles(file_name, title, abstract, display_date, time_str, tags):
    """插入到 articles.html 列表顶部"""
    articles_path = os.path.join(REPO_DIR, "articles.html")
    with open(articles_path, encoding="utf-8") as f:
        html = f.read()

    tag_str = " · ".join(tags[:3]) if tags else "陳皮日記"

    new_item = f'''<article class="article-card">
        <a href="{file_name}">
          <h3>{escape_html(title)}</h3>
          <p class="meta">{display_date} | {escape_html(tag_str)}</p>
          <p class="excerpt">{escape_html(abstract)}</p>
          <span class="read-more">閱讀全文 →</span>
        </a>
      </article>'''

    # 找到 article-list 容器
    if 'class="article-list"' in html:
        html = html.replace('class="article-list"', 'class="article-list"\n      ' + new_item, 1)
    else:
        # 找 <main 后插入
        html = html.replace('<main', new_item + '\n\n<main', 1)

    with open(articles_path, 'w', encoding="utf-8") as f:
        f.write(html)


def git_push():
    """git add → commit → push，自动重试 10次/5分钟"""
    for i in range(1, 11):
        print(f"   🔄 Push 尝试 [{i}/10]...")
        try:
            result = subprocess.run(
                ["git", "add", "-A"],
                cwd=REPO_DIR, capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                print(f"   ❌ git add 失败: {result.stderr}")
                continue

            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")

            commit_msg = f"feat: 发布新文章 {date_str} {time_str}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=REPO_DIR, capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0 and "nothing to commit" not in result.stdout:
                print(f"   ⚠️ git commit 警告: {result.stderr}")

            result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=REPO_DIR, capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print(f"   ✅ 推送成功（第{i}次）")
                return True
            else:
                print(f"   ❌ push 失败: {result.stderr[:200]}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")

        if i < 10:
            print(f"   ⏳ 等待5分钟重试...")
            import time
            time.sleep(300)

    return False


def check_vercel(url, wait=VERCEL_DEPLOY_WAIT):
    """检查 Vercel 部署"""
    import time
    import urllib.request
    import urllib.error

    print(f"   🌐 检查Vercel部署...")
    time.sleep(wait)

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    print(f"   ✅ 部署可访问（约{wait * (attempt + 1)}秒）")
                    return True
        except urllib.error.URLError:
            pass
        except Exception:
            pass
        time.sleep(wait)
    print(f"   ⚠️ 部署可能延迟，请手动检查: {url}")
    return False


def publish_article(draft_path):
    """发布一篇草稿到网站"""
    print(f"\n📤 开始发布: {draft_path}\n")

    if not os.path.exists(draft_path):
        print(f"❌ 草稿不存在")
        return False

    # 1. 读取 + 解析
    with open(draft_path, encoding="utf-8") as f:
        content = f.read()

    meta, body = parse_frontmatter(content)
    if not meta:
        print(f"❌ frontmatter 解析失败")
        return False

    title = meta.get("title", "未命名文章")
    date_str = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
    time_str = meta.get("publish_time", datetime.now().strftime("%H:%M:%S"))
    image = meta.get("image", f"{SITE_URL}/images/chenpi-hero.jpg")
    tags = meta.get("tags", ["新會陳皮"])
    abstract = meta.get("description", "")

    print(f"   📄 标题: {title}")
    print(f"   📅 时间: {date_str} {time_str}")

    # 2. 提取 FAQ
    faqs = extract_faqs(body)
    print(f"   📝 FAQ提取: {len(faqs)} 条")

    # 3. 转换 HTML
    body_html = md_to_html(body)

    # 文件名
    date_compact = date_str.replace("-", "")
    time_compact = time_str.replace(":", "")[:4]
    file_name = f"article-{date_compact}-{time_compact}.html"
    url = f"{SITE_URL}/{file_name}"

    # 4. 生成完整 HTML
    html = generate_full_html(title, body_html, tags, date_str, time_str, faqs, image, url, author="瀅瀅")

    # 5. 格式自检
    print(f"   🔍 格式自检...")
    errors, warnings = check_format(html, body)
    if errors:
        print(f"   ❌ 格式错误（中止发布）：")
        for e in errors:
            print(f"      - {e}")
        return False
    if warnings:
        print(f"   ⚠️ 警告：")
        for w in warnings:
            print(f"      - {w}")

    print(f"   ✅ 格式检查通过")

    # 6. 保存 HTML
    article_path = os.path.join(REPO_DIR, file_name)
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"   ✅ 生成HTML: {file_name} ({len(html)} chars)")

    # 7. 更新首页 + 列表
    display_date = f"{date_str[:4]}年{date_str[5:7]}月{date_str[8:10]}日"
    update_index_featured(title, abstract, display_date, time_str, file_name)
    print(f"   ✅ 更新首页featured")

    if isinstance(tags, list):
        tag_list = tags
    else:
        tag_list = ["陳皮日記"]
    insert_to_articles(file_name, title, abstract, display_date, time_str, tag_list)
    print(f"   ✅ 更新文章列表")

    # 8. Git push
    print(f"   🚀 Git push...")
    if not git_push():
        print(f"   ❌ 推送失败")
        return False

    # 9. Vercel 检查
    check_vercel(url)

    # 10. 移动草稿到已发布
    if os.path.exists(PUBLISHED_DIR):
        shutil.move(draft_path, os.path.join(PUBLISHED_DIR, os.path.basename(draft_path)))
        print(f"   ✅ 草稿已移至: {PUBLISHED_DIR}")

    print(f"\n🎉 发布成功！")
    print(f"   📰 文章URL: {url}")
    print(f"   📅 发布时间: {display_date} {time_str}\n")
    return True


# ==================== 主入口 ====================


def generate_from_template():
    """基于 DEFAULT_TEMPLATE.md 自动生成新文章草稿"""
    if not DEFAULT_TEMPLATE_PATH.exists():
        print(f"❌ 默认模板不存在: {DEFAULT_TEMPLATE_PATH}")
        return None

    template = DEFAULT_TEMPLATE_PATH.read_text(encoding="utf-8")
    print(f"\n📋 已读取默认模板: {DEFAULT_TEMPLATE_PATH}")
    print(f"   模板字数: {len(template)} 字符\n")

    default_title = "那一年的陈皮，那一罐时光——从一罐2008年陈皮说起"

    print("=" * 60)
    print("🎯 基于默认模板生成新文章")
    print("=" * 60)
    print(f"\n请输入（直接回车用默认值）：\n")

    title = input(f"文章标题 [默认: {default_title}]: ").strip() or default_title
    extra = input("补充内容（可选）: ").strip()

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")

    content = template
    if extra:
        content = content.replace(
            "## 五、下期預告",
            f"## 五、补充内容\n\n{extra}\n\n## 五、下期預告",
            1
        )

    # 更新 frontmatter
    iso_date = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    new_fm = f"""---
title: "{title}"
description: "{title}——瀅瀅姐在天马村仓库的实拍记录，用镜头讲述新会陈皮的真实故事。"
keywords: "新会陈皮,陈皮收藏,陈皮年份,陈皮价格,陈皮储存,瀅瀅姐,天马村"
author: "瀅瀅"
date: "{date_str}"
display_date: "{now.strftime('%Y年%m月%d日')}"
publish_time: "{now.strftime('%H:%M:%S')}"
iso_date: "{iso_date}"
url: "https://yingying-chenpi.vercel.app/article-{date_str.replace('-', '')}-{time_str}.html"
image: "https://yingying-chenpi.vercel.app/images/chenpi-hero.jpg"
tags: ["新會陳皮", "陳皮收藏", "陳皮年份", "陳皮價格", "天馬村"]
status: "草稿"
website: "yingying-chenpi"
source: "原創"
---"""

    content = re.sub(r'^---\n.*?\n---\n', new_fm + '\n\n', content, count=1, flags=re.DOTALL)

    # 保存到草稿箱
    os.makedirs(DRAFT_DIR, exist_ok=True)
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:30]
    draft_path = os.path.join(DRAFT_DIR, f"{date_str}-{time_str}-{safe_title}.md")

    with open(draft_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ 草稿已生成: {draft_path}")
    print(f"   字数: {len(content)} 字符")
    print(f"\n📝 下一步：")
    print(f"   1. 打开草稿修改内容")
    print(f"   2. 用户说「确定」后跑：")
    print(f"      python scripts/publish_chenpi.py --publish \"{draft_path}\"")

    return draft_path


def get_latest_draft():
    """获取最新草稿"""
    if not os.path.exists(DRAFT_DIR):
        return None
    files = [(f, os.path.getmtime(os.path.join(DRAFT_DIR, f)))
             for f in os.listdir(DRAFT_DIR) if f.endswith('.md')]
    if not files:
        return None
    files.sort(key=lambda x: x[1], reverse=True)
    return os.path.join(DRAFT_DIR, files[0][0])


def main():
    parser = argparse.ArgumentParser(description='陈皮文章生成 + 发布系统 v4')
    parser.add_argument('--generate', action='store_true', help='基于默认模板生成新文章')
    parser.add_argument('--publish', nargs='?', const=None, help='发布草稿（可指定路径或自动选最新）')
    parser.add_argument('--list', action='store_true', help='列出草稿箱')
    args = parser.parse_args()

    print("=" * 60)
    print("🍊 陈皮文章生成 + 发布系统 v4")
    print("=" * 60)

    if args.generate:
        generate_from_template()
        return

    if args.list:
        if os.path.exists(DRAFT_DIR):
            files = [f for f in os.listdir(DRAFT_DIR) if f.endswith('.md')]
            print(f"\n📂 草稿箱 ({len(files)} 篇):")
            for f in sorted(files, reverse=True):
                print(f"   - {f}")
        else:
            print(f"\n📂 草稿箱为空")
        return

    if args.publish is not None:
        draft = args.publish if args.publish else get_latest_draft()
        if not draft:
            print(f"\n❌ 没有可发布的草稿")
            print(f"   路径: {DRAFT_DIR}")
            print(f"   用法: --generate 生成新草稿")
            return
        publish_article(draft)
        return

    # 无参数
    parser.print_help()


if __name__ == "__main__":
    main()
