# -*- coding: utf-8 -*-
# Create article HTML with proper UTF-8 by writing bytes directly
import pathlib

p = pathlib.Path(r'C:/Users/a/Desktop/chenpi-website')

# Define content using raw UTF-8 bytes
# We'll write the full HTML as bytes, using explicit byte strings for problematic chars

# The key is: write HTML as a proper UTF-8 file
html_parts = []

# Header
html_parts.append('<!DOCTYPE html>\n<html lang="zh-Hant">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n')

# Title - use bytes that we KNOW are correct
# 百年新會陳皮的文化底蘊：從一片果皮讀懂時光的故事
title = '百年新會陳皮的文化底蘊：從一片果皮讀懂時光的故事'
html_parts.append(f'<title>{title} | 溢豐堂 · 滢滢家新會陳皮</title>\n')

desc = '七十二歲的老陳伯在天台曬皮的清晨一小時，串起新會陳皮四百年地道地位、傳統工藝傳承與現代市場打假困境。'
html_parts.append(f'<meta name="description" content="{desc}">\n')
html_parts.append('<meta name="keywords" content="陳皮,新會,文化">\n')
html_parts.append('<meta name="author" content="滢滢">\n')
html_parts.append('<link rel="canonical" href="https://www.yiyichenpi.com/article-20260918-2050.html">\n')
html_parts.append('<meta name="geo.position" content="22.5317;113.0286">\n')
html_parts.append('<meta name="ICBM" content="22.5317, 113.0286">\n')
html_parts.append('<meta name="geo.placename" content="新會天馬村, 江門, 廣東">\n')
html_parts.append('<meta name="geo.region" content="CN-GD">\n')
html_parts.append('<meta property="og:type" content="article">\n')
html_parts.append(f'<meta property="og:title" content="{title}">\n')
html_parts.append(f'<meta property="og:description" content="{desc}">\n')
html_parts.append('<meta property="og:url" content="https://www.yiyichenpi.com/article-20260918-2050.html">\n')
html_parts.append('<meta property="og:image" content="images/article-20260918-1015.jpg">\n')
html_parts.append('<meta property="og:locale" content="zh_HK">\n')
html_parts.append('<meta property="article:published_time" content="2026-09-18T20:50:00+08:00">\n')
html_parts.append('<meta property="article:author" content="滢滢">\n')
html_parts.append('<meta name="twitter:card" content="summary_large_image">\n')
html_parts.append(f'<meta name="twitter:title" content="{title}">\n')
html_parts.append(f'<meta name="twitter:description" content="{desc}">\n')
html_parts.append('<meta name="twitter:image" content="images/article-20260918-1015.jpg">\n')
html_parts.append('<link rel="stylesheet" href="css/style.css">\n')
html_parts.append('</head>\n<body>\n<article>\n')
html_parts.append(f'<h1>{title}</h1>\n')

# Scene images
html_parts.append('''<figure class="article-inline-image no-source">
    <img src="images/article-20260918-1015-scene1.jpg" alt="老陳伯在天台曬皮">
</figure>

<p>清晨五點半，天還沒透亮，江門新會茶坑村的老陳伯就已經蹲在自家二樓的天台上了。他今年七十二歲，守這片柑園守了五十年。父親走的時候，拉著他的手說：「我這輩子最大的家當，不是這幾畝地，是樓上那幾罐陳皮。你要好好替我守著。」那幾罐陳皮，最老的，是一九四七年的。</p>

<h2>一、一片果皮，何以稱「陳」</h2>

<p>很多外地朋友不理解：不就是橘子皮？放幾年就能賣出金子價？這句話聽起來像笑話，但新會人聽了會認真搖頭。</p>

<p><strong>「不是所有橘子皮都叫陳皮。」</strong> 老陳伯一邊翻皮一邊說，<strong>「起碼得是新會核心產區的茶枝柑，三刀法開皮，自然生曬，起碼三年才能叫陳皮。烘過的、烤過的，加過添加劑的，統統不算。」</strong></p>

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

<p>然而，陳皮市場的亂象，是這幾年最讓老一輩新會人痛心的事。老陳伯的女兒從加拿大打來視頻：「爸，我在直播間看到九塊九包郵的『十五年老皮』，連運費都不夠，怎麼可能？」老陳伯說：「你別氣。氣壞了自己這二十年存的真皮也救不回來。」</p>

<figure class="article-inline-image no-source">
    <img src="images/article-20260918-1015-scene4.jpg" alt="陳皮莊園旅遊體驗">
</figure>

<h2>四、寫在最後</h2>

<p><strong>「你們年輕人啊，別把陳皮只當商品。它是時間的琥珀，是這片土地給我們的禮物。」</strong></p>

<p>是啊。這個世界上有些東西，是用錢買不到的。是用一輩子守出來的。就像一片好的新會陳皮。</p>

<h2>常見問題</h2>

<p><strong>Q1：三十五年的陳皮真的存在嗎？</strong> A：存在，但極為稀缺。三十五年陳化意味著每年百分之三至五的自然損耗，加上九十年代新會柑園面積遠不如現在，能完好保存至今的鳳毛麟角。</p>

<p><strong>Q2：直播間九塊九包郵的「十五年老皮」可信嗎？</strong> A：完全不可信。十五年陳皮的倉儲、損耗、资金成本遠超這個售價，正宗十五年新會陳皮售價通常在數千元一斤以上。</p>

<p><strong>Q3：普通家庭如何儲存陳皮？</strong> A：最佳方式是前三年的新皮在秋天和冬天反覆曬乾，待水分完全收乾後，第四年開始放進玻璃罐收藏，放置陰涼處，切忌密封、廚房或冰箱。</p>

<p><strong>Q4：陳皮可以入菜但有什麼禁忌？</strong> A：陳皮入菜最忌「多」，一隻老鴨湯放兩三片就夠了。孕婦和兒童應慎用，正在服藥的人士應先諮詢醫師意見，唔好將陳皮當成治療方案。</p>

<p><strong>Q5：如何驗證陳皮的年份和產地？</strong> A：最可靠的方法是選擇有完整溯源體系的品牌，查驗區塊鏈「一物一碼」溯源資訊，確認具體到村，並要求提供試喝樣皮。</p>

</article>
</body>
</html>''')

# Write the complete HTML
html_content = ''.join(html_parts)

# Verify it's valid UTF-8
test_decode = html_content.encode('utf-8').decode('utf-8')
print(f"HTML size: {len(html_content)}")
print(f"Round-trip OK: {html_content == test_decode}")

# Write to file
output = p / 'article-20260918-2050.html'
output.write_text(html_content, encoding='utf-8')
print(f"Written to: {output}")

# Verify raw bytes
with open(output, 'rb') as f:
    raw = f.read()

# Check title
idx = raw.find(b'<title>')
end = raw.find(b'</title>', idx)
title_bytes = raw[idx+7:end]
print(f"Title bytes hex: {title_bytes.hex()}")
print(f"Title bytes should be: e799bee5b9b4e696b0e69c83e999b3e79aaee79a84e69687e58c96e5ba95e897b4efbc9a...")
print(f"Match: {title_bytes.hex().startswith('e799bee5b9b4e696b0e69c83e999b3')}")
