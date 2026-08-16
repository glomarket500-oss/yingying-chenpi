import os, re, datetime

BASE = os.path.dirname(os.path.abspath(__file__))

def get_input(prompt, default=""):
    val = input(f"{prompt}: ")
    return val.strip() or default

def today_str():
    return datetime.date.today().strftime("%Y%m%d")

def today_cn():
    return datetime.date.today().strftime("%Y年%m月%d日")

def generate():
    print("=" * 40)
    print("溢丰堂陈皮日记发布工具")
    print("=" * 40)

    date_str = today_str()
    date_cn = today_cn()
    file_name = f"article-{date_str}.html"
    file_path = os.path.join(BASE, file_name)

    if os.path.exists(file_path):
        print(f"\n⚠️ 今天已经发布过了：{file_name}")
        overwrite = input("是否覆盖？输入 y 继续: ")
        if overwrite.lower() != 'y':
            return

    print("\n请填写以下内容（直接回车使用默认值）：\n")

    title = get_input("文章标题", f"溢丰堂的陈皮日记 · {date_cn}")
    tag = get_input("标签分类（如：陈皮知识/行业热点/生活故事/避坑知识/冲泡技巧）", "陈皮知识")
    tag_hash = f"#{tag}"

    print("\n请输入正文（第二人称，每段回车。输入空行即结束）：")
    paragraphs = []
    while True:
        line = input()
        if line.strip() == "" and len(paragraphs) > 0:
            break
        if line.strip():
            paragraphs.append(line.strip())

    if not paragraphs:
        print("❌ 正文不能为空")
        return

    # 生成摘要（前两段，每段前100字）
    summary = ""
    for p in paragraphs[:2]:
        summary += p[:100] + ("…" if len(p) > 100 else "")
        summary += ""
    summary = summary[:180] + "…"

    # 1. 生成文章详情页
    content_html = "\n".join([f"            <p>{p}</p>" for p in paragraphs])

    article_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 溢丰堂陈皮故事</title>
    <meta name="description" content="{paragraphs[0][:80]}……">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <nav class="nav">
        <a href="index.html" class="logo"><h1>溢丰堂</h1><span>滢滢家新会陈皮</span></a>
        <div class="nav-links">
            <a href="index.html">首页</a>
            <a href="articles.html" class="active">陈皮日记</a>
            <a href="videos.html">短视频</a>
            <a href="live.html">直播间</a>
            <a href="about.html">认识滢滢</a>
            <a href="contact.html">买陈皮</a>
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
            <a href="contact.html">买陈皮 →</a>
        </div>
    </article>

    <footer>
        <p>© 2024 溢丰堂 | <a href="articles.html">更多陈皮故事</a> | <a href="contact.html">买陈皮</a></p>
    </footer>
</body>
</html>"""

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(article_template)
    print(f"✅ 文章详情页已生成：{file_name}")

    # 2. 更新 articles.html（顶部插入新条目）
    articles_path = os.path.join(BASE, "articles.html")
    with open(articles_path, 'r', encoding='utf-8') as f:
        articles_content = f.read()

    new_item = f"""        <article class="article-item">
            <div class="article-meta">
                <span class="article-date">{date_cn}</span>
                <span class="article-tag">{tag}</span>
            </div>
            <h3><a href="{file_name}">{title}</a></h3>
            <p>{summary}</p>
            <a href="{file_name}" class="read-more">阅读全文 →</a>
        </article>

"""

    # 在第一个 <article class="article-item"> 之前插入
    insert_pos = articles_content.find('        <article class="article-item">')
    if insert_pos != -1:
        articles_content = articles_content[:insert_pos] + new_item + articles_content[insert_pos:]
        with open(articles_path, 'w', encoding='utf-8') as f:
            f.write(articles_content)
        print("✅ 文章列表已更新")
    else:
        print("⚠️ 未能找到插入位置，请手动更新 articles.html")

    # 3. 更新 index.html（替换今日更新区块）
    index_path = os.path.join(BASE, "index.html")
    with open(index_path, 'r', encoding='utf-8') as f:
        index_content = f.read()

    # 找到 article-featured 里面的内容替换
    pattern = r'(<article class="article-card article-featured">).*?(</article>)'
    
    def replace_home(match):
        return f'''{match.group(1)}
            <div class="article-meta">
                <span class="article-date">{date_cn}</span>
                <span class="article-tag">{tag_hash}</span>
            </div>
            <h3><a href="{file_name}">{title}</a></h3>
            <p>{paragraphs[0][:120]}…</p>
            <p>{paragraphs[1][:120] if len(paragraphs) > 1 else ""}…</p>
            <div class="article-cta">
                <a href="{file_name}" class="btn">读完整日记 →</a>
            </div>
        {match.group(2)}'''

    new_index = re.sub(pattern, replace_home, index_content, count=1, flags=re.DOTALL)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_index)
    print("✅ 首页今日更新已替换")

    print(f"\n🎉 全部完成！新文章地址：{file_name}")
    print("请刷新浏览器查看效果。")
    input("\n按回车键退出...")

if __name__ == "__main__":
    try:
        generate()
    except KeyboardInterrupt:
        print("\n\n已取消。")
    except Exception as e:
        print(f"\n❌ 出错：{e}")
        input("按回车键退出...")
