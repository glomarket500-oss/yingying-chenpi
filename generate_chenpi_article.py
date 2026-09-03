#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
陈皮文章生成 + 发布系统 v3

【工作流程】
1. 搜索当天热点
2. 基于热点写全新陈皮文章（AI生成）
3. 保存到草稿文件夹
4. 给用户确认（必须等用户说「确定」）
5. 用户确认后 → 发布上网

【时间格式】
网页显示：xxxx年x月x日 xx:xx:xx（精确到秒）
文件名：YYYY-MM-DD-HHMM-标题.md

【使用方式】
- 生成文章：python generate_chenpi_article.py
- 发布文章：python publish_chenpi_v3.py --input "草稿路径.md"
"""

import argparse
import re
import os
import subprocess
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path

# === 配置 ===
REPO_DIR = r"C:\Users\a\Desktop\chenpi-website"
INDEX_HTML = os.path.join(REPO_DIR, "index.html")
ARTICLES_HTML = os.path.join(REPO_DIR, "articles.html")
VAULT_DIR = r"C:\Users\a\Desktop\MianAI知识库\MianAI知识库\vault\滢滢姐讲陈皮故事"
VERCEL_URL = "https://yingying-chenpi.vercel.app"


def search_hot_news():
    """搜索当天热点新闻"""
    try:
        from hermes_tools import web_search
        queries = [
            "今日热点 2026",
            "新会陈皮 最新 今日",
            "健康养生 新闻 今日"
        ]
        for q in queries[:2]:
            result = web_search(q, limit=3)
            if result and 'data' in result:
                web_results = result['data'].get('web', [])
                if web_results:
                    return {
                        'title': web_results[0].get('title', ''),
                        'description': web_results[0].get('description', '')[:200]
                    }
    except Exception as e:
        print(f"   ⚠️ 搜索失败: {e}")
    return None


def generate_article_with_hotspot(hotspot):
    """
    基于热点生成全新陈皮文章
    返回: (markdown内容, 标题, 日期, 时间)
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")
    
    hot_title = hotspot['title'] if hotspot else '今日热点'
    hot_desc = hotspot['description'] if hotspot else ''
    
    # 提取热点关键词
    hot_keywords = []
    keywords_list = ['台风', '暴雨', '高温', '健康', '养生', '中秋', '节日', '疫情', '政策']
    for word in keywords_list:
        if word in hot_title or word in hot_desc:
            hot_keywords.append(word)
    
    keyword = hot_keywords[0] if hot_keywords else '今日热点'
    
    # 构建标题
    title = f"{keyword}之下，新會陳皮點樣幫到你？——瀅瀅姐講陳皮故事"
    
    # 构建Markdown内容（实际使用时这里会调用AI生成更丰富的内容）
    md_content = f"""---
title: "{title}"
date: "{date_str}"
time: "{time_str}"
tags: [陳皮, 新會, 養生, {keyword}]
category: 陳皮日記
source: 滢瀅姐陳皮文章-自動生成
status: 草稿
---

# {title}

> 🌀 **今日热点关联**：{hot_title}
> 
> {hot_desc}...

{keyword}來襲，好多朋友都開始關注身體健康。瀅瀅姐今日想同大家傾傾，點樣用一塊好陳皮，喺呢個時節裏面幫到你。

## 一、陳皮與{keyword}的關聯

新會陳皮素有「一兩陳皮一兩金」嘅美譽，唔單止係嶺南人嘅傳統食材，更係養生佳品。

## 二、瀅瀅姐推薦：{keyword}時節嘅陳皮養生配方

**陳皮{keyword}養生茶**
- 新會陳皮一小片（約三克）
- 熱水沖泡，蓋上壺蓋焗五分鐘
- 每日一壺，溫中祛濕

## 三、點樣揀好陳皮？

瀅瀅姐總結三個要訣：
1. **看產地**：正宗新會天馬村、茶坑村出品
2. **聞香氣**：年份越久，藥香越醇厚
3. **摸質地**：輕脆有韌性，薄如紙卻不碎

## 四、瀅瀅想對你說

買不買我家嘅陳皮無所謂，但瀅瀅希望你明明白白消費，唔好再被不良商家坑。

願你我在紛擾的生活中，都能為自己留一壺陳皮茶的時光。瀅瀅姐下次再同大家傾新故事，保重。

---

*© 溢豐堂 · 瀅瀅 · 新會天馬村*
*發佈時間：{now.strftime("%Y年%m月%d日 %H:%M:%S")}*
"""
    
    return md_content, title, date_str, time_str


def save_to_draft(md_content, date_str, time_str):
    """保存到草稿文件夹"""
    now = datetime.now()
    seconds = now.strftime('%S')
    filename = f"{date_str}-{time_str}{seconds}-滢瀅姐-{datetime.now().strftime('%H%M%S')}.md"
    draft_dir = Path(VAULT_DIR) / "草稿"
    draft_dir.mkdir(exist_ok=True)
    draft_path = draft_dir / filename
    draft_path.write_text(md_content, encoding="utf-8")
    return str(draft_path)


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def md_to_html(md_body):
    """Markdown转HTML"""
    paragraphs = []
    for line in md_body.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            paragraphs.append(f'<h1>{escape_html(line[2:])}</h1>')
        elif line.startswith('## '):
            paragraphs.append(f'<h2>{escape_html(line[3:])}</h2>')
        elif line.startswith('### '):
            paragraphs.append(f'<h3>{escape_html(line[4:])}</h3>')
        elif line.startswith('> '):
            paragraphs.append(f'<blockquote><p>{escape_html(line[2:])}</p></blockquote>')
        elif line.startswith('- '):
            paragraphs.append(f'<li>{escape_html(line[2:])}</li>')
        else:
            paragraphs.append(f'<p>{escape_html(line)}</p>')
    return '\n'.join(paragraphs)


def generate_full_html(title, body_html, tags, date_str, time_str):
    """生成完整HTML（使用标准模板）"""
    now = datetime.now()
    iso_date = now.strftime("%Y-%m-%d")
    # 精确到秒的时间显示
    display_datetime = now.strftime("%Y年%m月%d日 %H:%M:%S")
    
    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
    tags_html = ' · '.join(tags_list) if tags_list else '陳皮知識'
    keywords_str = ','.join(tags_list) if tags_list else '新會陳皮,陳皮養生'
    
    # 提取摘要
    abstract = body_html[:150].replace('\n', ' ') if len(body_html) > 150 else body_html
    abstract_clean = re.sub(r'<[^>]+>', '', abstract)[:150]
    
    html = f'''<!DOCTYPE html>
<html lang="zh-HK">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | 溢豐堂</title>
<meta name="description" content="{escape_html(abstract_clean[:150])}...">
<meta name="keywords" content="{keywords_str}">
<meta name="author" content="瀅瀅">
<meta name="robots" content="index, follow">
<meta name="geo.position" content="22.5317;113.0286">
<meta name="geo.placename" content="新會, 江門, 廣東">
<meta name="geo.region" content="CN-GD">
<link rel="canonical" href="{VERCEL_URL}/article-{{now.strftime('%Y%m%d')}}.html">
<meta property="og:title" content="{title} | 溢豐堂">
<meta property="og:description" content="{escape_html(abstract_clean[:150])}...">
<meta property="og:type" content="article">
<meta property="og:url" content="{VERCEL_URL}/article-{{now.strftime('%Y%m%d')}}.html">
<meta property="og:image" content="{VERCEL_URL}/images/chenpi-hero.jpg">
<meta property="og:locale" content="zh_HK">
<meta property="article:published_time" content="{iso_date}">
<meta property="article:author" content="瀅瀅">
<script type="application/ld+json">
{{"@context": "https://schema.org", "@type": "BlogPosting", "headline": "{title}", "description": "{escape_html(abstract_clean[:150])}...", "author": {{"@type": "Person", "name": "瀅瀅"}}, "datePublished": "{iso_date}", "dateModified": "{iso_date}"}}
</script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "PingFang SC","Microsoft YaHei",sans-serif; color: #333; background: #faf8f3; line-height: 1.8; }}
  a {{ text-decoration: none; color: inherit; }}
  .nav {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 5vw; background: #fff; border-bottom: 1px solid #eee; position: sticky; top: 0; z-index: 100; }}
  .nav-logo {{ font-size: 1.2rem; font-weight: 700; color: #8b4513; }}
  .nav-logo span {{ font-weight: 400; font-size: 0.75rem; color: #999; display: block; }}
  .nav-links {{ display: flex; gap: 24px; }}
  .nav-links a {{ font-size: 0.9rem; color: #666; }}
  .nav-links a:hover, .nav-links a.active {{ color: #8b4513; }}
  .article-wrap {{ max-width: 720px; margin: 0 auto; padding: 40px 5vw 60px; }}
  .breadcrumb {{ font-size: 0.82rem; color: #999; margin-bottom: 24px; }}
  .breadcrumb a {{ color: #8b4513; }}
  .article-header {{ margin-bottom: 40px; padding-bottom: 24px; border-bottom: 2px solid #f0e6d8; }}
  .article-header h1 {{ font-size: 1.6rem; font-weight: 700; color: #2c2c2c; margin-bottom: 16px; line-height: 1.4; }}
  .article-meta {{ display: flex; gap: 12px; font-size: 0.85rem; color: #888; margin-bottom: 16px; flex-wrap: wrap; }}
  .article-meta span {{ background: #f5f0eb; padding: 4px 12px; border-radius: 12px; }}
  .article-tags {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .article-tags a {{ font-size: 0.82rem; color: #8b4513; background: #f5f0eb; padding: 4px 12px; border-radius: 12px; }}
  .hotspot-box {{ background: linear-gradient(135deg, #fff8f0 0%, #fff0e0 100%); border-left: 4px solid #e74c3c; padding: 16px 20px; margin: 24px 0; border-radius: 0 8px 8px 0; }}
  .hotspot-box .label {{ font-size: 0.75rem; color: #e74c3c; font-weight: 600; margin-bottom: 6px; }}
  .hotspot-box .label::before {{ content: "🔥 "; }}
  .hotspot-box p {{ font-size: 0.92rem; color: #666; margin: 0; }}
  .scene {{ margin-bottom: 32px; }}
  .scene h2 {{ font-size: 1.2rem; font-weight: 600; color: #2c2c2c; margin: 32px 0 16px; padding-left: 12px; border-left: 3px solid #8b4513; }}
  .scene h3 {{ font-size: 1.05rem; font-weight: 600; color: #444; margin: 24px 0 12px; }}
  .scene p {{ margin-bottom: 14px; font-size: 0.96rem; color: #444; text-align: justify; }}
  .dialogue {{ background: #fff; border-left: 3px solid #8b4513; padding: 16px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
  .dialogue .who {{ font-weight: 600; color: #8b4513; font-size: 0.85rem; margin-bottom: 6px; }}
  .dialogue .who::before {{ content: "💬 "; }}
  .dialogue p {{ font-size: 0.94rem; margin: 0; color: #555; }}
  .recipe-box {{ background: linear-gradient(135deg, #fff 0%, #faf8f3 100%); border: 2px dashed #d4c4a8; padding: 24px; margin: 28px 0; border-radius: 12px; }}
  .recipe-box .title {{ font-size: 1.1rem; font-weight: 600; color: #8b4513; margin-bottom: 16px; text-align: center; }}
  .recipe-box .title::before {{ content: "🍵 "; }}
  .recipe-box ul {{ margin: 0; padding: 0; list-style: none; }}
  .recipe-box li {{ font-size: 0.92rem; color: #555; padding: 6px 0; border-bottom: 1px dotted #e0d5c5; }}
  .recipe-box li:last-child {{ border-bottom: none; }}
  .cta-box {{ background: linear-gradient(135deg, #8b4513 0%, #6b3410 100%); color: #fff; padding: 32px; border-radius: 12px; text-align: center; margin: 40px 0; }}
  .cta-box h3 {{ font-size: 1.2rem; margin-bottom: 12px; }}
  .cta-box p {{ font-size: 0.92rem; margin-bottom: 20px; opacity: 0.9; }}
  .cta-box a {{ display: inline-block; padding: 14px 32px; background: #fff; color: #8b4513; border-radius: 6px; font-weight: 600; }}
  .related {{ margin-top: 48px; padding-top: 32px; border-top: 2px solid #f0e6d8; }}
  .related h3 {{ font-size: 1.1rem; font-weight: 600; color: #2c2c2c; margin-bottom: 20px; }}
  footer {{ text-align: center; padding: 32px 5vw; font-size: 0.85rem; color: #999; border-top: 1px solid #eee; background: #fff; }}
  footer a {{ color: #8b4513; }}
  @media (max-width: 480px) {{ .nav {{ flex-direction: column; padding: 12px 5vw; }} .nav-links {{ justify-content: center; margin-top: 8px; gap: 16px; }} .article-header h1 {{ font-size: 1.3rem; }} .article-wrap {{ padding: 24px 4vw 40px; }} }}
</style>
</head>
<body>

<nav class="nav">
  <a href="index.html" class="nav-logo">
    溢豐堂
    <span>瀅瀅家新會陳皮</span>
  </a>
  <div class="nav-links">
    <a href="index.html">首頁</a>
    <a href="articles.html" class="active">陳皮日記</a>
    <a href="videos.html">短視頻</a>
    <a href="live.html">直播間</a>
    <a href="about.html">認識瀅瀅</a>
    <a href="contact.html">買陳皮</a>
  </div>
</nav>

<div class="article-wrap">
  <div class="breadcrumb">
    <a href="index.html">首頁</a>
    <span> · </span>
    <a href="articles.html">陳皮日記</a>
    <span> · </span>
    <span>{title}</span>
  </div>
  
  <header class="article-header">
    <h1>{title}</h1>
    <div class="article-meta">
      <span>📅 {display_datetime}</span>
      <span>👤 瀅瀅</span>
      <span>📍 新會天馬村</span>
      <span>🕐 閱讀約5分鐘</span>
    </div>
    <div class="article-tags">
      {''.join([f'<a href="#">{t}</a>' for t in tags_list])}
    </div>
  </header>
  
  <div class="article-content">
{body_html}
  </div>
  
  <div class="cta-box">
    <h3>想買正宗新會陳皮？</h3>
    <p>瀅瀅家天馬村果園直發，手工開皮、自然生曬、乾倉陳化。<br>不滿意七天無理由退，我敢這麼說，是因為我對自己的陳皮有信心。</p>
    <a href="contact.html">📱 加瀅瀅微信，了解詳情</a>
  </div>
  
  <div class="related">
    <h3>📖 你可能還想看</h3>
    <a href="articles.html" style="color: #8b4513;">查看全部陳皮故事 →</a>
  </div>
</div>

<footer>
  <p>© 溢豐堂 · 瀅瀅 · 新會天馬村 · <a href="contact.html">聯繫我們</a></p>
</footer>

</body>
</html>'''
    
    return html


def insert_to_index(file_name, title, abstract, display_datetime, tags):
    """插入到index.html"""
    idx_content = Path(INDEX_HTML).read_text(encoding="utf-8", errors="ignore")
    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
    tags_html = ' · '.join(tags_list[:2]) if tags_list else '陳皮知識'
    
    card = f'''<div class="diary-card"><a href="{file_name}"><div class="thumb"></div><div class="body"><div class="date">{display_datetime} · {tags_html}</div><h3>{title} <span class="new-badge">NEW</span></h3><p>{abstract[:80]}...</p></div></a></div>

'''
    
    pattern = r'(<div class="diary-grid">\s*\n)'
    new_idx = re.sub(pattern, r'\1' + card, idx_content, count=1)
    
    if new_idx != idx_content:
        Path(INDEX_HTML).write_text(new_idx, encoding="utf-8")
        return True
    return False


def insert_to_articles(file_name, title, abstract, display_datetime, tags):
    """插入到articles.html"""
    art_content = Path(ARTICLES_HTML).read_text(encoding="utf-8", errors="ignore")
    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
    tags_html = ' · '.join(tags_list[:2]) if tags_list else '陳皮知識'
    
    new_item = f'''<article class="article-item">
  <div class="article-meta">
    <span class="article-date">{display_datetime}</span>
    <span class="article-tag">{tags_html}</span>
  </div>
  <h3><a href="{file_name}">{title}</a></h3>
  <p>{abstract[:100]}...</p>
  <a href="{file_name}" class="read-more">閱讀全文 →</a>
</article>

'''
    
    insert_pos = art_content.find('<article class="article-item">')
    if insert_pos != -1:
        new_art = art_content[:insert_pos] + new_item + art_content[insert_pos:]
        Path(ARTICLES_HTML).write_text(new_art, encoding="utf-8")
        return True
    return False


def git_push():
    """自动重试git push"""
    os.chdir(REPO_DIR)
    subprocess.run(["git", "add", "-A"], capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Add article: {datetime.now().strftime('%Y%m%d')}"], capture_output=True)
    
    attempt = 0
    while True:
        attempt += 1
        result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
        if result.returncode == 0:
            return True, "推送成功"
        if "rejected" in result.stderr.lower():
            subprocess.run(["git", "pull", "origin", "main", "--no-rebase"], capture_output=True)
            result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
            if result.returncode == 0:
                return True, "推送成功（先pull后push）"
        if attempt >= 3:
            return False, f"推送失败: {result.stderr[:100]}"
        time.sleep(300)


def check_vercel():
    """检查Vercel部署"""
    import urllib.request
    start = time.time()
    while time.time() - start < 120:
        try:
            req = urllib.request.Request(VERCEL_URL, method='HEAD')
            req.add_header('User-Agent', 'Mozilla/5.0')
            resp = urllib.request.urlopen(req, timeout=10)
            if resp.status == 200 and (time.time() - start) >= 15:
                return True, f"部署完成（约 {int(time.time() - start)} 秒）"
        except:
            pass
        time.sleep(5)
    return False, "等待超时"


def main():
    parser = argparse.ArgumentParser(description='陈皮文章生成 + 发布系统 v3')
    parser.add_argument('--generate-only', action='store_true', help='只生成文章，不发布（给用户确认）')
    parser.add_argument('--input', help='草稿文件路径（用户确认后发布）')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🍊 陈皮文章生成 + 发布系统 v3")
    print("=" * 60)
    
    # 1. 搜索热点
    print("\n🔍 搜索当天热点...")
    hotspot = search_hot_news()
    if hotspot:
        print(f"   ✅ 找到热点: {hotspot['title'][:50]}...")
    else:
        print("   ℹ️ 未找到热点，使用默认主题")
    
    # 2. 生成文章
    print("\n📝 基于热点生成全新陈皮文章...")
    md_content, title, date_str, time_str = generate_article_with_hotspot(hotspot)
    
    # 3. 保存到草稿
    draft_path = save_to_draft(md_content, date_str, time_str)
    print(f"   ✅ 已保存到草稿: {draft_path}")
    
    # 4. 给用户确认（关键步骤）
    print("\n" + "=" * 60)
    print("📋 【请确认】文章内容预览：")
    print("=" * 60)
    print(f"\n📝 标题: {title}")
    print(f"\n📄 正文预览（前300字）：")
    print(md_content[:300] + "...")
    print(f"\n📁 文件位置: {draft_path}")
    print("\n" + "-" * 60)
    print("⚠️  请确认是否发布上网：")
    print("   回复「确定」→ 立即发布")
    print("   回复「改」→ 重新生成")
    print("   回复「不要」→ 放弃发布")
    print("-" * 60)
    
    if args.generate_only:
        print("\n✅ 文章已生成，等待用户确认...")
        print(f"   请查看草稿: {draft_path}")
        return 0
    
    # 如果指定了输入文件（用户已确认），直接发布
    if args.input:
        print(f"\n📤 用户已确认，开始发布: {args.input}")
        draft_path = args.input
        
        # 读取草稿
        content = Path(draft_path).read_text(encoding="utf-8")
        fm = {}
        body = content
        if content.startswith("---"):
            m = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if m:
                fm_text = m.group(1)
                body = content[m.end():]
                for line in fm_text.split('\n'):
                    if ':' in line and not line.startswith(' ') and not line.startswith('-'):
                        key, val = line.split(':', 1)
                        fm[key.strip()] = val.strip().strip('"').strip("'")
        
        title = fm.get('title', '新會陳皮故事')
        tags = fm.get('tags', '陳皮,新會')
        
        # 获取当前精确时间
        now = datetime.now()
        display_datetime = now.strftime("%Y年%m月%d日 %H:%M:%S")
        iso_date = now.strftime("%Y-%m-%d")
        
        # 生成文件名
        file_name = f"article-{now.strftime('%Y%m%d')}-{time_str}.html"
        file_path = os.path.join(REPO_DIR, file_name)
        
        # 生成HTML
        body_html = md_to_html(body)
        html = generate_full_html(title, body_html, tags, date_str, time_str)
        Path(file_path).write_text(html, encoding="utf-8")
        print(f"   ✅ 生成HTML: {file_name}")
        
        # 更新index和articles
        abstract = body[:120].replace('\n', ' ')
        insert_to_index(file_name, title, abstract, display_datetime, tags)
        insert_to_articles(file_name, title, abstract, display_datetime, tags)
        print("   ✅ 更新首页和文章列表")
        
        # Git push
        print("   🚀 Git push...")
        ok, msg = git_push()
        if not ok:
            print(f"   ❌ {msg}")
            return 1
        print(f"   ✅ {msg}")
        
        # 检查部署
        print("   🌐 检查Vercel部署...")
        ok, msg = check_vercel()
        if ok:
            print(f"   ✅ {msg}")
        else:
            print(f"   ⏳ {msg}")
        
        # 移动文件到已发布
        print("   📋 更新文章状态...")
        published_dir = Path(VAULT_DIR) / "已发布"
        published_dir.mkdir(exist_ok=True)
        dest = published_dir / Path(draft_path).name
        shutil.move(draft_path, dest)
        print(f"   ✅ 已移动到: {dest}")
        
        print(f"\n🎉 发布成功！")
        print(f"   网站: {VERCEL_URL}")
        print(f"   新文章: {VERCEL_URL}/{file_name}")
        print(f"   发布时间: {display_datetime}")
        
        return 0
    
    print("\nℹ️  文章已生成，请确认后再发布")
    print(f"   草稿路径: {draft_path}")
    print("   确认后运行: python generate_chenpi_article.py --input \"草稿路径.md\"")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
