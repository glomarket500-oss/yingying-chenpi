import os, re, datetime
import opencc

BASE = r'C:\Users\a\Desktop\chenpi-website'
converter = opencc.OpenCC('s2hk')

date_str = '20260819'
date_cn = '2026年8月19日'
title = '老陳皮裏的光陰故事'
tag = '陳皮知識'

# User's article content (will be converted to HK Traditional)
article_body = '''來，搬張竹椅坐下，泡一壺陳皮普洱，咱們慢慢聊。

你聞，這屋子裏飄的是什麼？不是香水，也不是熏香，是這塊新會老陳皮在陶罐裏睡了二十年後，一被熱水驚醒，釋放出的那種醇厚甘香。說來奇怪，同樣是一片橘子皮，離開了江門那片水土，就成了普通的果皮；只有落在新會那幾塊核心產區 —— 茶坑、梅江、東甲 —— 曬足了嶺南的日頭，吸飽了珠江三角洲的潮氣，再經過一年又一年的陳化，才能蜕變成「一兩陳皮一兩金」的寶貝。

老一輩人講，這規矩從宋代就有了。那時候廣東的商人把陳皮裝成簍，順着西江一路往西，走的是茶馬古道的支流；往東呢，從港澳碼頭上船，漂洋過海去東南亞。你爺爺那輩要是下南洋，包袱裏不塞幾片老陳皮，等於沒帶上故鄉的味道。新加坡、馬來西亞的老華僑家裏，哪個沒有個瓷罐藏着三十年、五十年的老皮？感冒咳嗽了掰一小片煮水，鄉愁犯了湊到鼻尖聞一聞 —— 這哪是藥材啊，這是漂在海外的廣東人拴住故土的一根線。

收藏這門學問

說起來，收陳皮跟藏酒一個理，急不得。你得給它找個好地方：江門那種老騎樓的二樓最合適，通風、避光、離地、離牆。每年翻曬兩回，梅雨季過了翻一次，中秋前後再翻一次。翻的時候手要輕，像給老相識拍灰 —— 太陽底下看，好的老陳皮油包飽滿，對着光一照，透亮，像琥珀裏的年輪。顏色呢，不會死黑死黑的，是深褐裏泛着紅，像老傢俱包漿的那種潤。

我跟你說個訣竅：拿起來搓一搓，聽聲音。三年以內的皮，乾脆，沙沙響；到了十年往上，聲音發悶，因為內瓤已經纖維化、脱落了，皮身輕薄卻韌勁十足。你再聞 —— 新皮是鮮烈的果香，像十七八歲的少年；五年以上的開始轉藥香，帶點薄荷涼；到了十五年往上，那種醇、那種甘，入肺入脾，沒法形容，只能說是「時間的味道」。

茶桌上的江湖

咱們廣東人喝茶，陳皮是重頭戲。早茶桌上，一盅兩件之間，老闆順手掰半片老皮丟進紫砂壺，跟普洱老茶頭同煮。港澳的老茶樓至今還守着這個傳統，你去看香港上環那些老字號，玻璃罐裏整整齊齊碼着不同年份的新會皮，跟酒單一樣標着價。至於東南亞的唐人街，陳皮白茶的喝法這些年又火回來了 —— 福鼎的白牡丹配上十年的新會皮，白茶的清鮮襯着陳皮的甘醇，夏天喝解暑，冬天喝暖胃，華僑們喝的不是茶，是小時候阿嬤在廚房煮水的那個下午。

鑑別老陳皮，記住四句話：看皮相、聞香氣、摸質地、品湯色。皮相要自然，那些黑得均勻、亮得反光的，多半是染色熏硫的；香氣要沉，不能衝鼻；質地輕、脆、薄，卻不斷；泡出來的湯色金黃透亮，不是醬油色。最關鍵的一點 —— 煮完水的皮，底還是活的，展開來看，脈絡清晰，油室還在呼吸。

說到這，我起身從裏屋捧出一個小鐵盒，神秘兮兮地掀開一條縫。

「你猜這是什麼？這是我上周從一位江門老藏家手裏收來的，據說是上世紀八十年代港澳回流的「古董皮」……」我故意頓了頓，瞥見你湊過來的眼神，笑着把蓋子合上。

「想知道這盒皮背後的故事？怎麼從東南亞輾轉回到廣東？怎麼鑑別這種回流老貨的真假？咱們得另找一天，搬兩把更好的竹椅，開一泡更老的茶，我再慢慢跟你說。」

（下期預告：港澳回流老陳皮的水有多深？教你幾招看破「做舊皮」的套路。）'''

# Convert to HK Traditional
article_body_hk = converter.convert(article_body)
paragraphs = [p for p in article_body_hk.strip().split('\n\n') if p.strip()]

# 1. Generate article HTML
content_html = '\n'.join([f'            <p>{p}</p>' for p in paragraphs])

article_html = f'''<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 溢豐堂陳皮故事</title>
    <meta name="description" content="{paragraphs[0][:80]}……">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <nav class="nav">
        <a href="index.html" class="logo"><h1>溢豐堂</h1><span>瀅瀅家新會陳皮</span></a>
        <div class="nav-links">
            <a href="index.html">首頁</a>
            <a href="articles.html" class="active">陳皮日記</a>
            <a href="videos.html">短視頻</a>
            <a href="live.html">直播間</a>
            <a href="about.html">認識瀅瀅</a>
            <a href="contact.html">買陳皮</a>
        </div>
    </nav>

    <article class="article-detail">
        <h2>{title}</h2>
        
        <div class="article-meta">
            <span class="article-date">{date_cn}</span>
            <span class="article-tag">{tag}</span>
        </div>

        <div class="article-content">
{content_html}
        </div>

        <div class="article-nav">
            <a href="articles.html">← 返回文章列表</a>
            <a href="contact.html">買陳皮 →</a>
        </div>
    </article>

    <footer>
        <p>© 2024 溢豐堂 | <a href="articles.html">更多陳皮故事</a> | <a href="contact.html">買陳皮</a></p>
    </footer>
</body>
</html>'''

file_path = os.path.join(BASE, f'article-{date_str}.html')
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(article_html)
print(f'✅ article-{date_str}.html created')

# 2. Update articles.html
articles_path = os.path.join(BASE, 'articles.html')
with open(articles_path, 'r', encoding='utf-8') as f:
    articles_content = f.read()

summary = paragraphs[0][:100] + '…'

new_item = f'''        <article class="article-item">
            <div class="article-meta">
                <span class="article-date">{date_cn}</span>
                <span class="article-tag">{tag}</span>
            </div>
            <h3><a href="article-{date_str}.html">{title}</a></h3>
            <p>{summary}</p>
            <a href="article-{date_str}.html" class="read-more">閱讀全文 →</a>
        </article>

'''

insert_pos = articles_content.find('        <article class="article-item">')
if insert_pos != -1:
    articles_content = articles_content[:insert_pos] + new_item + articles_content[insert_pos:]
    with open(articles_path, 'w', encoding='utf-8') as f:
        f.write(articles_content)
    print('✅ articles.html updated')
else:
    print('⚠️ articles.html insert failed')

# 3. Update index.html
index_path = os.path.join(BASE, 'index.html')
with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

pattern = r'(<article class="article-card article-featured">).*?(</article>)'

def replace_home(match):
    return f'''{match.group(1)}
            <div class="article-meta">
                <span class="article-date">{date_cn}</span>
                <span class="article-tag">#{tag}</span>
            </div>
            <h3><a href="article-{date_str}.html">{title}</a></h3>
            <p>{paragraphs[0][:120]}…</p>
            <p>{paragraphs[1][:120] if len(paragraphs) > 1 else ""}…</p>
            <div class="article-cta">
                <a href="article-{date_str}.html" class="btn">讀完整日記 →</a>
            </div>
        {match.group(2)}'''

new_index = re.sub(pattern, replace_home, index_content, count=1, flags=re.DOTALL)
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(new_index)
print('✅ index.html updated')

print('\n🎉 全部完成！')
