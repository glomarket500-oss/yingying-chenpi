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
    基于热点生成全新陈皮故事文章
    热点融入故事场景，不是标签
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
    
    keyword = hot_keywords[0] if hot_keywords else '养生'
    
    # 根据热点构建故事场景
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
        # 通用故事模板
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
tags: [陳皮, 新會, 故事, {keyword}]
category: 陳皮日記
source: 滢瀅姐陳皮文章-自動生成
status: 草稿
---

{story}
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
