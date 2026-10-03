# -*- coding: utf-8 -*-
# Create the article HTML directly with proper UTF-8 encoding

import pathlib
p = pathlib.Path(r'C:/Users/a/Desktop/chenpi-website')

# The article content - properly encoded
title = "百年新會陳皮的文化底蘊：從一片果皮讀懂時光的故事"
description = "七十二歲的老陳伯在天台曬皮的清晨一小時，串起新會陳皮四百年地道地位、傳統工藝傳承與現代市場打假困境。"
keywords = "陳皮,新會,文化"

# Create proper HTML with correct UTF-8
html = f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | 溢豐堂 · 滢滢家新會陳皮</title>
<meta name="description" content="{description}">
<meta name="keywords" content="{keywords}">
<meta name="author" content="滢滢">
<link rel="canonical" href="https://www.yiyichenpi.com/article-20260918-2050.html">
<meta name="geo.position" content="22.5317;113.0286">
<meta name="ICBM" content="22.5317, 113.0286">
<meta name="geo.placename" content="新會天馬村, 江門, 廣東">
<meta name="geo.region" content="CN-GD">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://www.yiyichenpi.com/article-20260918-2050.html">
<meta property="og:image" content="images/article-20260918-1015.jpg">
<meta property="og:locale" content="zh_HK">
<meta property="article:published_time" content="2026-09-18T20:50:00+08:00">
<meta property="article:author" content="滢滢">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="images/article-20260918-1015.jpg">
<link rel="stylesheet" href="css/style.css">
</head>
<body>
<article>
<h1>{title}</h1>
<figure class="article-inline-image no-source">
    <img src="images/article-20260918-1015-scene1.jpg" alt="老陳伯在天台曬皮">
</figure>
<p>清晨五點半，天還沒透亮，江門新會茶坑村的老陳伯就已經蹲在自家二樓的天台上了。他今年七十二歲，守這片柑園守了五十年。</p>
<p>父親走的時候，拉著他的手說：「我這輩子最大的家當，不是這幾畝地，是樓上那幾罐陳皮。你要好好替我守著。」那幾罐陳皮，最老的，是一九四七年的。</p>
<h2>一、一片果皮，何以稱「陳」</h2>
<p>陳皮不是普通的橘子皮。它必須是廣東新會核心產區種植的茶枝柑剝下來的果皮，必須經過至少三年以上的自然陳化。明代李時珍《本草綱目》裡寫得很清楚：「今天下以廣中來者為勝。」</p>
<figure class="article-inline-image no-source">
    <img src="images/article-20260918-1015-scene2.jpg" alt="三刀法開皮工藝">
</figure>
<h2>二、三十五年的皮，是怎麼「陳」出來的</h2>
<p>行內有句話叫「三年成皮，五年入藥，十年成寶」。老陳伯說：「三十多年前的皮，全靠人手。那時候沒有機器開皮，一刀下去要正、要穩、要順著柑的紋路。」</p>
<figure class="article-inline-image no-source">
    <img src="images/article-20260918-1015-scene3.jpg" alt="父女視頻討論陳皮真假">
</figure>
<h2>三、造假與信任</h2>
<p>陳皮市場的亂象，是這幾年最讓老一輩新會人痛心的事。常見的造假手法有：茶水泡染、高溫濕倉催熟、蒸皮做舊、陳皮水勾兌。</p>
<figure class="article-inline-image no-source">
    <img src="images/article-20260918-1015-scene4.jpg" alt="陳皮莊園旅遊體驗">
</figure>
<h2>四、寫在最後</h2>
<p>「你們年輕人啊，別把陳皮只當商品。它是時間的琥珀，是這片土地給我們的禮物。」</p>
</article>
</body>
</html>'''

# Write with explicit UTF-8
output_path = p / 'article-20260918-2050.html'
output_path.write_text(html, encoding='utf-8')
print(f"Written: {output_path}")
print(f"Size: {len(html)}")

# Verify
data = output_path.read_bytes()
idx = data.find(b'<title>')
end = data.find(b'</title>', idx)
title_bytes = data[idx+7:end]
print(f"Title bytes: {title_bytes}")
print(f"Title hex: {title_bytes.hex()}")
