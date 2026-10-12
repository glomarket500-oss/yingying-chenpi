# -*- coding: utf-8 -*-
"""Build the three 2026-10-01 backfill articles on the live article shell."""
import json, re, sys
from pathlib import Path

REPO = Path(r'C:/Users/a/Desktop/chenpi-website')
SHELL = REPO / 'article-20260929-1942.html'

src = SHELL.read_text(encoding='utf-8')
STYLE = re.search(r'<style>.*?</style>', src, re.S).group(0)
NAV = re.search(r'<nav class="nav">.*?</nav>', src, re.S).group(0)
FOOTER = re.search(r'<footer>.*?</footer>', src, re.S).group(0)
COOKIE = re.search(r'<div id="cookie-bar".*?</script>', src, re.S).group(0)


def page(slug, title, desc, keywords, tags, iso, display, body, faq, related):
    url = f'https://www.yiyichenpi.com/{slug}'
    cover = f'https://www.yiyichenpi.com/images/{slug[:-5]}-1900.jpg'
    tags_html = ''.join(f'<a href="articles.html">{t}</a>' for t in tags)
    blog = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": title,
            "description": desc, "image": cover, "datePublished": iso, "dateModified": iso,
            "author": {"@type": "Person", "name": "滢滢"},
            "publisher": {"@type": "Organization", "name": "溢豐堂"},
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "articleSection": "陳皮故事", "inLanguage": "zh-Hant", "keywords": keywords}
    faq_schema = {"@context": "https://schema.org", "@type": "FAQPage",
                  "mainEntity": [{"@type": "Question", "name": q,
                                  "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    rel = ''
    for i, (href, h4, blurb) in enumerate(related):
        mt = ' style="margin-top:12px"' if i else ''
        rel += (f'                <div class="related-item"{mt}>\n'
                f'                    <a href="{href}">\n'
                f'                        <h4>{h4}</h4>\n'
                f'                        <p>{blurb}</p>\n'
                '                    </a>\n                </div>\n')
    return f'''<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | 溢豐堂</title>
    <meta name="description" content="{desc}">
    <meta name="keywords" content="{keywords}">
    <meta name="author" content="滢滢">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
    <meta name="geo.position" content="22.5317;113.0286">
    <meta name="geo.placename" content="新會, 江門, 廣東">
    <meta name="geo.region" content="CN-GD">
    <meta name="ICBM" content="22.5317, 113.0286">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{cover}">
    <meta property="og:locale" content="zh_HK">
    <meta property="article:published_time" content="{iso}">
    <meta property="article:modified_time" content="{iso}">
    <meta property="article:author" content="滢滢">
    <meta property="article:section" content="陳皮故事">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{cover}">
    <link rel="stylesheet" href="css/style.css?v=5">
    <script type="application/ld+json">
{json.dumps(blog, ensure_ascii=False, indent=4)}
    </script>
    <script type="application/ld+json">
{json.dumps(faq_schema, ensure_ascii=False, indent=4)}
    </script>
{STYLE}
</head>
<body>
{NAV}

    <div class="breadcrumb">
        <a href="index.html">首頁</a> &gt; <a href="articles.html">故事</a> &gt; <span>{title}</span>
    </div>

    <main class="article-wrap">
        <article class="article-detail">
            <header class="article-header">
                <h1>{title}</h1>
                <div class="article-meta">
                    <span>🕐 <time datetime="{iso}">{display}</time></span>
                    <span>✍️ 滢滢</span>
                    <span>🏷️ 新會陳皮</span>
                </div>
                <div class="article-tags">
                    {tags_html}
                </div>
            </header>

            <figure class="article-inline-image">
                <img src="images/{slug[:-5]}-1900.jpg" alt="{title[:20]}｜新會陳皮專題配圖"
                     loading="lazy" width="1024" height="576">
            </figure>

{body}
            <div class="cta-box">
                <h3>想買正宗新會陳皮？</h3>
                <p style="color:#888;font-size:.9rem;margin:8px 0 0">新會天馬村果園直發，手工開皮、自然生曬、幹倉陳化</p>
                <a href="contact.html">立即聯繫滢滢姐</a>
            </div>

            <div class="related">
                <h3>相關文章</h3>
{rel}            </div>
        </article>
    </main>

{FOOTER}

{COOKIE}
</body>
</html>
'''
