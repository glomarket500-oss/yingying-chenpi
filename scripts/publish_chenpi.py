#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
陈皮文章生成 + 发布系统 v4
============================

【改造记录 2026-09-06】
- 删除内联CSS（250行），统一引用外部 css/style.css
- 对齐 article-20260904-2247.html 结构（用户认可版本）
- 新增 FAQPage Schema 自动提取
- 新增 ICBM、article:section、article:tag 等 GEO 优化
- 双模式：--generate（自动生成）+ --publish MD_PATH（发布草稿）
- git push 自动重试（10次/5分钟间隔）

【工作流程】
1. 搜索当天热点
2. 基于热点生成全新陈皮文章（--generate 模式）
3. 保存到草稿文件夹
4. 用户亲口说「确定」
5. --publish 发布上网（生成HTML、更新列表、git push）

【时间格式铁律】
- 网页显示：xxxx年x月x日 xx:xx:xx（精确到秒）
- 文件名：YYYYMMDD-HHMM

【使用方式】
生成草稿：python publish_chenpi.py --generate
发布草稿：python publish_chenpi.py --publish "草稿路径.md"
"""

import argparse
import re
import os
import subprocess
import sys
import time
import shutil
import json
from datetime import datetime
from pathlib import Path

# === 配置 ===
REPO_DIR = r"C:\Users\a\Desktop\chenpi-website"
INDEX_HTML = os.path.join(REPO_DIR, "index.html")
ARTICLES_HTML = os.path.join(REPO_DIR, "articles.html")
CSS_FILE = os.path.join(REPO_DIR, "css", "style.css")
VAULT_DIR = r"C:\Users\a\Desktop\MianAI知识库\vault\滢滢姐讲陈皮故事"
VERCEL_URL = "https://yingying-chenpi.vercel.app"


# ============================================================
# 热点搜索 + 自动生成
# ============================================================

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
    基于热点生成全新陈皮故事文章
    热点融入故事场景，不是标签
    返回: (markdown内容, 标题, 日期, 时间)
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M")

    hot_title = hotspot['title'] if hotspot else '今日热点'
    hot_desc = hotspot['description'] if hotspot else ''

    hot_keywords = []
    keywords_list = ['台风', '暴雨', '高温', '健康', '养生', '中秋', '节日', '疫情', '政策', '陈皮', '价格']
    for word in keywords_list:
        if word in hot_title or word in hot_desc:
            hot_keywords.append(word)

    keyword = hot_keywords[0] if hot_keywords else '养生'

    if '台风' in keyword or '暴雨' in keyword:
        title = f"{keyword}天，客人問瀅瀅姐：『濕氣重飲乜好？』"
        story = f"""清晨六點，天還未完全亮。瀅瀅姐被手機震醒，阿爸發來語音：「{keyword}來咗，快啲去倉庫睇睇啲陳皮收好未！」

瀅瀅姐披住件薄外套就趕去果園。風已經開始大，路邊嘅樹搖搖擺擺。佢心裏面擔心嘅唔單止係倉庫，仲有舊年嗰批十五年梅江——如果濕氣入侵，幾十年嘅心血就毀咗。

正當佢同阿爸搬緊陳皮入乾倉，手機又震。係佛山嘅陳姐：

「瀅瀅姐，{keyword}天濕氣重，我成個人冇精神、舌苔白、胃口差，飲乜好？」

瀅瀅姐望住窗外傾盆大雨，忽然想起阿婆以前講過嘅一句話。佢停低手，擦擦額頭嘅汗，慢慢打字回覆：

「陳姐，你記唔記得我上次同你講過，陳皮最勁嘅地方唔係補，而係『化』——化濕、化滯、化痰。」

瀅瀅姐繼續講：「我阿婆以前每到落雨天，就會煲一壺陳皮炒薏米水。三片十年陳皮，抓一把炒過嘅薏米，煲足一個鐘。唔單止祛濕，仲暖胃。我細個嗰陣，成日飲，到而家個胃都幾好。」

陳姐回咗個「多謝」，跟住又問：「咁我買邊種陳皮好？你推薦邊款？」

瀅瀅姐笑咗。呢個問題佢答過幾百次，但每次答都覺得值得——因為每答一次，就等於幫一個人避開假貨嘅坑。

「如果你係想祛湿，我推薦你試下天馬五年。香氣足，價錢又唔會太貴，日常煲水飲夠晒。如果你預算多啲，梅江十年更好，藥香已經出咗，祛湿效果更強。」

「點解你成日強調『正宗新會』？」陳姐好奇問。

瀅瀅姐望住倉庫裏面一排排嘅陶罐，語氣認真：「因為假貨太多。你以為你買咗新會陳皮，其實係廣西皮、湖南皮，甚至係染色嘅普通橘皮。啲人攞硫磺熏、攞藥水浸，為咗睇落去似舊皮。你飲落去，唔止冇益，仲有害。」

佢停一停，又講：「我阿爸種柑三十年，開皮、翻曬、貯藏，每一步都親手做。我賣陳皮，賣嘅唔係一塊皮，係我阿爸三十年的心血。你買一次，就知道同假貨有咩分別。」

雨越嚟越大，瀅瀅姐同阿爸終於將最後一筐陳皮搬入乾倉。佢坐喺門口，飲住自己沖嘅陳皮茶，望住外面白茫茫嘅雨幕，心裏面諗：其實陳皮同人生都一樣，要經歷風吹雨打，先至會變得有價值。

佢又發咗條語音畀陳姐：「陳姐，記得，陳皮要揀正宗新會，產地唔啱，再貴都冇用。有咩唔明白，隨時問我。」

窗外，風雨依舊。但瀅瀅姐知道，總有人因為一塊好陳皮，而喺濕冷嘅日子裏面，感受到一絲溫暖。

---

**瀅瀅姐小貼士：**

{keyword}天氣祛濕陳皮茶
- 新會陳皮 1 片（約 3 克）
- 炒薏米 15 克
- 茯苓 10 克
- 煲水 1 小時，當茶飲

功效：祛濕健脾，適合舌苔白膩、冇胃口、身體困重之人。

---

*© 溢豐堂 · 瀅瀅 · 新會天馬村*
*發佈時間：{now.strftime("%Y年%m月%d日 %H:%M:%S")}*"""

    elif '中秋' in keyword or '节日' in keyword:
        title = f"中秋前夜，瀅瀅姐幫客人揀陳皮禮盒時，講起一段舊事"
        story = f"""中秋節前兩日，瀅瀅姐嘅微信響個唔停。

「瀅瀅姐，我想買陳皮送老闆，邊款好？」
「瀅瀅，中秋禮盒有冇？要體面啲嘅。」
「瀅瀅姐，預算五百，買到真貨嗎？」

瀅瀅姐逐條回覆，手指打到有啲攰。佢諗起舊年中秋，有個客人嘅故事，到而家都記得好清楚。

舊年中秋節前夕，瀅瀅姐收到一條語音，把聲有啲慌張：

「瀅瀅姐，我阿媽住院咗，醫生話濕氣太重、脾胃虛。我想買啲陳皮畀佢調理，但係我上網買咗兩次都係假貨，泡出嚟有股霉味……」

發語音嘅係廣州嘅李生，做IT嘅，平時少講嘢，但講到阿媽，把聲明顯急咗。

瀅瀅姐當時就問佢：「你買嘅陳皮幾錢？咩顏色？聞到咩味？」

李生話：「三百幾蚊半斤，顏色好黑，聞落去有股甜味，但泡出嚟苦澀澀。」

瀅瀅姐聽完就知——假貨。佢解釋畀李生聽：「正宗新會陳皮，年份淺嘅係橙紅色，年份深嘅係棕褐色，唔會黑到發亮。如果你聞到甜味，可能係加糖熏過。真陳皮聞落去係柑香同藥香，泡出嚟先微苦後甘。」

「咁我應該點揀？」李生問。

瀅瀅姐諗咗諗，推薦咗梅江十年畀佢：「你阿媽脾胃虛，十年陳皮藥香出咗，溫中健脾最好。你買小半斤，分開裝，每次用一片煲水。記得，一定要用新會正宗，產地唔啱，再平都冇用。」

李生聽完，直接轉咗八百蚊過嚟。瀅瀅姐退返二百畀佢，話：「梅江十年小半斤，六百夠晒。多嗰二百，等阿媽好返先請我飲茶。」

三個月後，李生發咗張相過嚟——阿媽坐喺公園長椅上面，面色紅潤咗好多。佢話：「瀅瀅姐，阿媽而家每日都飲陳皮水，胃口好咗，舌苔都薄咗。你嗰日退返我嗰二百蚊，我記住咗。」

瀅瀅姐望住張相，心裏面暖咗一下。佢賣陳皮賣咗咁多年，最開心唔系收錢嗰陣，而系聽到客人話「有用」嗰陣。

今年中秋，瀅瀅姐又開始幫客人揀禮盒。佢一邊包裝，一邊同徒弟講：「你記住，賣陳皮唔系賣貨，系賣信任。客人信你，先會將屋企人嘅健康交畀你。呢份信任，比咩都重要。」

窗外月光灑落，瀅瀅姐望住一盒盒裝好嘅陳皮，心裏面諗：但願每個收到禮盒嘅人，都能感受到呢份來自新會天馬村嘅溫暖。

---

**瀅瀅姐小貼士：**

中秋送禮陳皮揀選指南
- 送長輩：梅江十年以上，藥香醇厚，調理脾胃
- 送朋友：天馬五年，柑香十足，性價比高
- 送客戶：梅江十五年禮盒裝，體面大方

記得：正宗新會產地、自然生曬、乾倉貯藏，三者缺一不可。

---

*© 溢豐堂 · 瀅瀅 · 新會天馬村*
*發佈時間：{now.strftime("%Y年%m月%d日 %H:%M:%S")}*"""

    else:
        title = f"瀅瀅姐陳皮日記｜{keyword}話題下，一位客人嘅故事"
        story = f"""今日{keyword}話題刷屏，瀅瀅姐一邊刷手機一邊包陳皮。

正當佢睇到一條新聞，微信突然收到一條長語音。打開一聽，係東莞嘅張姨，把聲帶點猶豫：

「瀅瀅姐，我個仔話我買嘅陳皮係假貨，叫我唔好飲。但我飲咗半個月，覺得個胃舒服咗……」

瀅瀅姐聽完，就知又係一個被網上信息搞到唔知信邊個嘅客人。佢放下手上嘅陳皮，慢慢打字：

「張姨，你影張相畀我，我幫你睇下先。」

相發過嚟，瀅瀅姐放大睇——皮張厚實、顏色偏黃、油室唔明顯。佢嘆咗口氣，回覆：「張姨，你個仔講得冇錯，呢個的確唔係正宗新會陳皮，係廣西皮。」

「但我飲完真係舒服咗喎……」張姨有啲唔信。

「因為佢始終係陳皮，只係產地唔同、品質差啲。但你長期飲，可能有農藥殘留或者硫磺問題，對身體唔好。」瀅瀅姐認真解釋。

張姨沉默咗一陣，然後問：「咁我點樣先買到真嘅？」

瀅瀅姐發咗段語音，一條一條講：「第一，正宗新會陳皮特產地要系新會，最好系天馬、梅江、茶坑呢幾個核心產區。第二，看油室，新會陳皮油室細密均勻，普通皮冇咁多。第三，聞香氣，正宗嘅有柑香同藥香，假貨要嘛冇味，要嘛有股霉味。」

「咁貴唔貴？」張姨最關心呢個。

「入門級天馬五年，日常飲都夠，唔會貴到離譜。但如果你長期調理身體，建議買十年以上，效果更明顯。」瀅瀅姐答。

張姨最後買咗半斤天馬十年。收到貨之後，佢專登發咗張相畀瀅瀅姐——相裏面陳皮擺喺茶盤上，陽光照射下面，油室閃閃發光。

「瀅瀅姐，呢個先至叫陳皮！」張姨嘅語音充滿驚喜。

瀅瀅姐望住張相，笑咗。佢知道，又幫一個人避開咗假貨嘅坑。呢個，就係佢堅持寫陳皮日記嘅原因。

---

**瀅瀅姐小貼士：**

辨別正宗新會陳皮三招
1. **看產地**：認準新會天馬、梅江、茶坑核心產區
2. **看油室**：細密均勻，呈蜂窩狀
3. **聞香氣**：柑香+藥香，年份越久藥香越濃

---

*© 溢豐堂 · 瀅瀅 · 新會天馬村*
*發佈時間：{now.strftime("%Y年%m月%d日 %H:%M:%S")}*"""

    md_content = f"""---
title: "{title}"
date: "{date_str}"
time: "{time_str}"
display_date: "{now.strftime('%Y年%m月%d日')}"
publish_time: "{now.strftime('%H:%M:%S')}"
iso_date: "{now.strftime('%Y-%m-%dT%H:%M:%S+08:00')}"
tags: [陳皮, 新會, 故事, {keyword}]
keywords: "新會陳皮,陳皮故事,陳皮養生,{keyword}"
description: "{title}。{keyword[:20]}話題下，瀅瀅姐用真實故事講新會陳皮嘅時間、產地同價值。"
author: "瀅瀅"
category: "陳皮日記"
source: "滢瀅姐陳皮文章-自動生成"
status: "草稿"
website: "yingying-chenpi"
url: "{VERCEL_URL}/article-{now.strftime('%Y%m%d')}-{time_str}.html"
image: "{VERCEL_URL}/images/chenpi-hero.jpg"
---

{story}
"""

    return md_content, title, date_str, time_str


def save_to_draft(md_content, date_str, time_str):
    """保存到草稿文件夹"""
    now = datetime.now()
    seconds = now.strftime('%S')
    filename = f"{date_str}-{time_str}{seconds}-瀅瀅姐陳皮日記.md"
    draft_dir = Path(VAULT_DIR) / "草稿"
    draft_dir.mkdir(exist_ok=True)
    draft_path = draft_dir / filename
    draft_path.write_text(md_content, encoding="utf-8")
    return str(draft_path)


# ============================================================
# Markdown → HTML（v4 改进版）
# ============================================================

def escape_html(text):
    """HTML转义"""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def inline_format(text):
    """行内格式：粗体"""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return text


def md_to_html(md_body):
    """Markdown转HTML（对齐20260904-2247结构）"""
    out = []
    in_quote = False
    in_ul = False
    in_p = False

    def close_all():
        nonlocal in_quote, in_ul, in_p
        if in_p:
            out.append('</p>')
            in_p = False
        if in_ul:
            out.append('</ul>')
            in_ul = False
        if in_quote:
            out.append('</blockquote>')
            in_quote = False

    for line in md_body.split('\n'):
        line = line.rstrip()
        if not line:
            close_all()
            continue
        if line.startswith('### '):
            close_all()
            out.append(f'<h3>{inline_format(escape_html(line[4:]))}</h3>')
        elif line.startswith('## '):
            close_all()
            out.append(f'<h2>{inline_format(escape_html(line[3:]))}</h2>')
        elif line.startswith('> '):
            close_all()
            if not in_quote:
                out.append('<blockquote>')
                in_quote = True
            out.append(f'<p>{inline_format(escape_html(line[2:]))}</p>')
        elif line.startswith('- '):
            if in_p:
                out.append('</p>')
                in_p = False
            if not in_ul:
                out.append('<ul>')
                in_ul = True
            out.append(f'<li>{inline_format(escape_html(line[2:]))}</li>')
        else:
            if in_quote:
                out.append('</blockquote>')
                in_quote = False
            if in_ul:
                out.append('</ul>')
                in_ul = False
            if not in_p:
                out.append('<p>')
                in_p = True
            out.append(inline_format(escape_html(line)))

    close_all()
    return '\n'.join(out)


def extract_faqs(body_md):
    """从Markdown提取FAQ，用于FAQPage Schema"""
    faqs = []
    faq_match = re.search(r'##\s*(?:常見問題|FAQ)(.*?)(?=##|$)', body_md, re.DOTALL)
    if faq_match:
        faq_text = faq_match.group(1)
        # 匹配 Q：... \n\n A：... 格式
        qa = re.findall(r'\*?\*?Q\d+：(.+?)\*?\*?\s*\n+\s*A：(.+?)(?=\n\n|\*?\*?Q|$)', faq_text, re.DOTALL)
        for q, a in qa:
            q_clean = q.strip()
            a_clean = a.strip()
            if q_clean and a_clean:
                faqs.append({"q": q_clean, "a": a_clean})
    return faqs


def build_faq_schema(faqs):
    """构建FAQPage JSON-LD"""
    if not faqs:
        return ""
    main_entity = [{"@type": "Question", "name": faq["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}}
                   for faq in faqs]
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity
    }
    return json.dumps(schema, ensure_ascii=False, indent=4)


# ============================================================
# HTML 模板（v4 — 外部CSS + 完整SEO/GEO Schema）
# ============================================================

def generate_full_html(title, body_html, tags, date_str, time_str, faqs, image_url, url):
    """
    生成完整HTML文章页
    v4关键改进：
    - 引用外部 css/style.css（无内联CSS）
    - 完整 Schema.org：BlogPosting + FAQPage + Person + LocalBusiness
    - 完整 GEO：geo.position / ICBM / geo.placename
    - 完整 Open Graph + Twitter Card
    """
    now = datetime.now()
    iso_date = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    display_date = now.strftime("%Y年%m月%d日")
    publish_time = now.strftime("%H:%M:%S")

    # 解析tags（接受 list 或 str 两种入参）
    if isinstance(tags, list):
        tags_list = [str(t).strip() for t in tags if str(t).strip()]
    else:
        tags_clean = tags.strip('[]')
        tags_list = [t.strip() for t in tags_clean.split(',') if t.strip()]

    # 提取摘要
    abstract_match = re.search(r'<p>(.+?)</p>', body_html)
    abstract = abstract_match.group(1) if abstract_match else title
    abstract_clean = re.sub(r'<[^>]+>', '', abstract)[:150]

    tags_html = ''.join(f'<a href="#">{escape_html(t).strip(chr(34)).strip(chr(39))}</a>' for t in tags_list)
    keywords_str = ','.join(tags_list)

    faq_schema = build_faq_schema(faqs)

    html = f'''<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- SEO -->
    <title>{escape_html(title)} | 溢豐堂</title>
    <meta name="description" content="{escape_html(abstract_clean)}">
    <meta name="keywords" content="{escape_html(keywords_str)}">
    <meta name="author" content="瀅瀅">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">

    <!-- GEO -->
    <meta name="geo.position" content="22.5317;113.0286">
    <meta name="geo.placename" content="新會, 江門, 廣東">
    <meta name="geo.region" content="CN-GD">
    <meta name="ICBM" content="22.5317, 113.0286">

    <!-- Canonical -->
    <link rel="canonical" href="{url}">

    <!-- Open Graph -->
    <meta property="og:title" content="{escape_html(title)} | 溢豐堂">
    <meta property="og:description" content="{escape_html(abstract_clean)}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:locale" content="zh_HK">
    <meta property="article:published_time" content="{iso_date}">
    <meta property="article:modified_time" content="{iso_date}">
    <meta property="article:author" content="瀅瀅">
    <meta property="article:section" content="陳皮日記">
    <meta property="article:tag" content="{escape_html(keywords_str)}">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape_html(title)}">
    <meta name="twitter:description" content="{escape_html(abstract_clean)}">
    <meta name="twitter:image" content="{image_url}">

    <!-- Schema.org BlogPosting -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "{escape_html(title)}",
        "description": "{escape_html(abstract_clean)}",
        "author": {{
            "@type": "Person",
            "name": "瀅瀅",
            "jobTitle": "新會陳皮傳承人",
            "url": "{VERCEL_URL}/about.html"
        }},
        "publisher": {{
            "@type": "Organization",
            "name": "溢豐堂",
            "url": "{VERCEL_URL}"
        }},
        "datePublished": "{iso_date}",
        "dateModified": "{iso_date}",
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "{url}"
        }},
        "image": {{
            "@type": "ImageObject",
            "url": "{image_url}",
            "width": 1200,
            "height": 630
        }},
        "articleSection": "陳皮日記",
        "keywords": "{escape_html(keywords_str)}"
    }}
    </script>

    <!-- Schema.org FAQPage -->
    <script type="application/ld+json">
    {faq_schema}
    </script>

    <!-- Schema.org Person -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "瀅瀅",
        "alternateName": "溢豐堂瀅瀅",
        "jobTitle": "新會陳皮傳承人",
        "description": "在新會賣陳皮，每天寫一篇陳皮日記，講真話、說故事、幫你避坑。",
        "url": "{VERCEL_URL}/about.html",
        "worksFor": {{
            "@type": "Organization",
            "name": "溢豐堂",
            "url": "{VERCEL_URL}"
        }},
        "knowsAbout": ["新會陳皮", "陳皮鑑別", "陳皮收藏", "茶枝柑"]
    }}
    </script>

    <!-- Schema.org LocalBusiness -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "溢豐堂 - 瀅瀅家新會陳皮",
        "description": "正宗新會天馬村陳皮，手工開皮、自然生曬、乾倉陳化。",
        "url": "{VERCEL_URL}",
        "telephone": "+86-193-0750-1495",
        "address": {{
            "@type": "PostalAddress",
            "addressLocality": "新會",
            "addressRegion": "廣東",
            "addressCountry": "CN"
        }},
        "geo": {{
            "@type": "GeoCoordinates",
            "latitude": 22.5317,
            "longitude": 113.0286
        }},
        "priceRange": "$$"
    }}
    </script>

    <!-- 外部CSS（v4关键改进：删除250行内联） -->
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- 導航 -->
    <nav class="nav">
        <a href="index.html" class="logo">
            <h1>溢豐堂</h1>
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

    <!-- 文章主體 -->
    <article class="article-detail">
        <!-- 面包屑 -->
        <div class="breadcrumb">
            <a href="index.html">首頁</a>
            <span> · </span>
            <a href="articles.html">陳皮日記</a>
            <span> · </span>
            <span>{escape_html(title)}</span>
        </div>

        <!-- 文章頭部 -->
        <header class="article-header">
            <h1>{escape_html(title)}</h1>
            <div class="article-meta">
                <span>📅 {display_date} {publish_time}</span>
                <span>👤 瀅瀅</span>
                <span>📍 新會天馬村</span>
                <span>🕐 閱讀約8分鐘</span>
            </div>
            <div class="article-tags">
                {tags_html}
            </div>
        </header>

        <!-- 文章正文 -->
        <div class="article-content">
{body_html}
        </div>

        <!-- CTA -->
        <div class="cta-box">
            <h3>想買正宗新會陳皮？</h3>
            <p>瀅瀅家天馬村果園直發，手工開皮、自然生曬、乾倉陳化。<br>不滿意七天無理由退，我敢這麼說，是因為我對自己的陳皮有信心。</p>
            <a href="contact.html">📱 加瀅瀅微信，了解詳情</a>
        </div>

        <!-- 相關文章 -->
        <div class="related">
            <h3>📖 你可能還想看</h3>
            <a href="articles.html" class="read-more">查看全部陳皮故事 →</a>
        </div>
    </article>

    <!-- 頁腳 -->
    <footer>
        <p>© 溢豐堂 · 瀅瀅 · 新會天馬村 · <a href="contact.html">聯繫我們</a></p>
        <div class="social">
            <a href="#">📕 小紅書</a>
            <a href="#">📱 微信</a>
            <a href="#">🎵 抖音</a>
        </div>
    </footer>
</body>
</html>'''

    return html


# ============================================================
# 列表更新：index.html + articles.html
# ============================================================

def update_index_featured(title, abstract, display_date, publish_time, file_name):
    """更新 index.html featured 区块"""
    idx_content = Path(INDEX_HTML).read_text(encoding="utf-8", errors="ignore")

    # 匹配当前 featured 区块
    pattern = r'<article class="article-card article-featured">.*?</article>'
    new_featured = f'''<article class="article-card article-featured">
            <div class="article-meta">
                <span class="article-date">{display_date} {publish_time[:5]}</span>
                <span class="article-tag">#陳皮日記</span>
            </div>
            <h3><a href="{file_name}">{escape_html(title)}</a></h3>
            <p>{escape_html(abstract[:150])}...</p>
            <div class="article-cta">
                <a href="{file_name}" class="btn">讀完整日記 →</a>
            </div>
        </article>'''

    new_idx, count = re.subn(pattern, new_featured, idx_content, count=1, flags=re.DOTALL)
    if count > 0:
        Path(INDEX_HTML).write_text(new_idx, encoding="utf-8")
        return True
    return False


def insert_to_articles(file_name, title, abstract, display_date, publish_time, tags):
    """在 articles.html 顶部插入新文章"""
    art_content = Path(ARTICLES_HTML).read_text(encoding="utf-8", errors="ignore")
    tags_list = [t.strip() for t in tags.strip('[]').split(',') if t.strip()]
    tags_html = ' · '.join(tags_list[:2]) if tags_list else '陳皮日記'

    new_item = f'''<article class="article-item">
  <div class="article-meta">
    <span class="article-date">{display_date} {publish_time[:5]}</span>
    <span class="article-tag">{tags_html}</span>
  </div>
  <h3><a href="{file_name}">{escape_html(title)}</a></h3>
  <p>{escape_html(abstract[:150])}...</p>
  <a href="{file_name}" class="read-more">閱讀全文 →</a>
</article>

'''

    insert_pos = art_content.find('<article class="article-item">')
    if insert_pos != -1:
        new_art = art_content[:insert_pos] + new_item + art_content[insert_pos:]
        Path(ARTICLES_HTML).write_text(new_art, encoding="utf-8")
        return True
    return False


# ============================================================
# Git 自动推送（10次重试，5分钟间隔）
# ============================================================

def git_push():
    """自动重试git push（按用户全自动模式：10次/5分钟）"""
    os.chdir(REPO_DIR)
    subprocess.run(["git", "add", "-A"], capture_output=True)
    commit_msg = f"feat: 发布陈皮文章 {datetime.now().strftime('%Y%m%d-%H%M')}"
    subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True)

    attempt = 0
    max_attempts = 10
    while attempt < max_attempts:
        attempt += 1
        print(f"   🔄 Push 尝试 [{attempt}/{max_attempts}]...")
        result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return True, f"推送成功（第{attempt}次）"
        if "rejected" in (result.stderr or "").lower():
            subprocess.run(["git", "pull", "origin", "main", "--no-rebase"], capture_output=True)
            result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return True, "推送成功（先pull后push）"
        if attempt < max_attempts:
            print(f"   ⚠️ 失败，5分钟后重试...")
            time.sleep(300)
    return False, f"推送失败：已达最大重试次数"


def check_vercel():
    """检查Vercel部署（HEAD请求）"""
    import urllib.request
    start = time.time()
    while time.time() - start < 180:
        try:
            req = urllib.request.Request(VERCEL_URL, method='HEAD')
            req.add_header('User-Agent', 'Mozilla/5.0')
            resp = urllib.request.urlopen(req, timeout=10)
            elapsed = int(time.time() - start)
            if resp.status == 200:
                return True, f"部署可访问（约{elapsed}秒）"
        except Exception:
            pass
        time.sleep(10)
    return False, "等待超时（Vercel可能在CDN刷新中）"


# ============================================================
# 主流程
# ============================================================

def parse_frontmatter(content):
    """解析YAML frontmatter（简化版：仅支持 key: value 与 [tags]）"""
    fm = {}
    body = content
    if content.startswith("---"):
        m = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if m:
            fm_text = m.group(1)
            body = content[m.end():]
            current_list_key = None
            for line in fm_text.split('\n'):
                if line.startswith('  - ') and current_list_key:
                    # 列表项
                    val = line.strip()[2:].strip().strip('"').strip("'")
                    fm[current_list_key].append(val)
                elif ':' in line and not line.startswith(' '):
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if val.startswith('['):
                        # 数组
                        fm[key] = re.findall(r'\[(.*?)\]', val)
                        if not fm[key]:
                            fm[key] = [v.strip().strip('"').strip("'") for v in val.strip('[]').split(',') if v.strip()]
                    else:
                        fm[key] = val
                    current_list_key = key if isinstance(fm[key], list) else None
    return fm, body


def publish_article(draft_path):
    """发布流程：MD → HTML → 更新列表 → git push"""
    print(f"\n📤 开始发布: {draft_path}")

    # 1. 读取草稿
    content = Path(draft_path).read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    title = fm.get('title', '新會陳皮故事')
    tags = fm.get('tags', '[陳皮, 新會]')
    if isinstance(tags, list):
        tags_str = '[' + ', '.join(tags) + ']'
    else:
        tags_str = tags

    # 2. 当前精确时间（按铁律：精确到秒）
    now = datetime.now()
    display_date = now.strftime("%Y年%m月%d日")
    publish_time = now.strftime("%H:%M:%S")
    iso_date = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    # 3. 文件名
    file_name = f"article-{now.strftime('%Y%m%d')}-{now.strftime('%H%M')}.html"
    file_path = os.path.join(REPO_DIR, file_name)

    # 4. URL与图片
    url = fm.get('url', f"{VERCEL_URL}/{file_name}")
    image_url = fm.get('image', f"{VERCEL_URL}/images/chenpi-hero.jpg")

    # 5. Markdown → HTML
    body_html = md_to_html(body)
    faqs = extract_faqs(body)
    print(f"   📝 FAQ提取: {len(faqs)} 条")

    # 6. 生成完整HTML
    html = generate_full_html(title, body_html, tags_str, '', '', faqs, image_url, url)
    Path(file_path).write_text(html, encoding="utf-8")
    print(f"   ✅ 生成HTML: {file_name} ({len(html)} chars)")

    # 7. 更新 index.html & articles.html
    abstract = re.sub(r'<[^>]+>', '', body[:200]).replace('\n', ' ')
    update_index_featured(title, abstract, display_date, publish_time, file_name)
    print("   ✅ 更新首页featured")
    insert_to_articles(file_name, title, abstract, display_date, publish_time, tags_str)
    print("   ✅ 更新文章列表")

    # 8. Git push
    print("   🚀 Git push...")
    ok, msg = git_push()
    if not ok:
        print(f"   ❌ {msg}")
        return False
    print(f"   ✅ {msg}")

    # 9. 检查Vercel
    print("   🌐 检查Vercel部署...")
    ok, msg = check_vercel()
    if ok:
        print(f"   ✅ {msg}")
    else:
        print(f"   ⏳ {msg}")

    # 10. 移动草稿到已发布
    published_dir = Path(VAULT_DIR) / "已发布"
    published_dir.mkdir(exist_ok=True)
    dest = published_dir / Path(draft_path).name
    shutil.move(draft_path, dest)
    print(f"   ✅ 草稿已移至: {dest}")

    print(f"\n🎉 发布成功！")
    print(f"   📰 文章URL: {VERCEL_URL}/{file_name}")
    print(f"   📅 发布时间: {display_date} {publish_time}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='陈皮文章生成 + 发布系统 v4',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python publish_chenpi.py --generate                    # 自动生成草稿
  python publish_chenpi.py --publish "草稿.md"           # 发布草稿
        """
    )
    parser.add_argument('--generate', action='store_true', help='自动生成草稿（基于热点）')
    parser.add_argument('--publish', metavar='MD_PATH', help='发布指定草稿文件')
    args = parser.parse_args()

    print("=" * 60)
    print("🍊 陈皮文章生成 + 发布系统 v4")
    print("=" * 60)

    if args.generate:
        print("\n🔍 搜索当天热点...")
        hotspot = search_hot_news()
        if hotspot:
            print(f"   ✅ 热点: {hotspot['title'][:60]}")
        else:
            print("   ℹ️ 未找到热点，使用默认主题")

        print("\n📝 基于热点生成陈皮故事...")
        md_content, title, date_str, time_str = generate_article_with_hotspot(hotspot)
        draft_path = save_to_draft(md_content, date_str, time_str)
        print(f"\n✅ 草稿已生成: {draft_path}")
        print(f"📰 标题: {title}")
        print("\n" + "-" * 60)
        print("⚠️  请确认后执行：")
        print(f'   python publish_chenpi.py --publish "{draft_path}"')
        print("-" * 60)
        return 0

    elif args.publish:
        return 0 if publish_article(args.publish) else 1

    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())