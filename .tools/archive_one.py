# -*- coding: utf-8 -*-
"""archive_one.py <slug.html> —— 把已發布文章歸檔到知識庫「已发布」。
   從 HTML 還原 Markdown（含對話、FAQ、圖片連結），加上 YAML frontmatter。"""
import html as H
import re
import sys
from pathlib import Path

BASE = 'https://www.yiyichenpi.com'
REPO = Path(r'C:/Users/a/Desktop/chenpi-website')
DONE = Path(r'C:\Users\a\Desktop\MianAI知识库\MianAI知识库\vault\滢滢姐讲陈皮故事\已发布')


def inline(s):
    s = re.sub(r'<strong>(.*?)</strong>', r'**\1**', s, flags=re.S)
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    return H.unescape(s).strip()


def main(slug):
    p = REPO / slug
    if not p.is_file():
        print(f'  找不到 {slug}')
        return 1
    art = p.read_text(encoding='utf-8')
    title = re.search(r'<title>(.*?)\s*[|｜]', art).group(1).strip()
    desc = re.search(r'<meta name="description" content="([^"]*)"', art).group(1)
    kw = re.search(r'<meta name="keywords" content="([^"]*)"', art).group(1)
    pub = re.search(r'article:published_time" content="([^"]+)"', art)
    iso = pub.group(1) if pub else ''
    disp = re.search(r'<span[^>]*>\s*(20\d\d年\d+月\d+日[^<]*)</span>', art)
    display = disp.group(1).strip() if disp else ''
    body = re.search(r'<div class="article-body">([\s\S]*?)\n            </div>', art)
    if not body:
        print('  找不到 article-body')
        return 1
    body = body.group(1)

    md = []
    for m in re.finditer(r'<section class="scene">([\s\S]*?)</section>', body):
        blk = m.group(1)
        h2 = re.search(r'<h2>(.*?)</h2>', blk, re.S)
        if h2:
            md.append(f'## {inline(h2.group(1))}\n')
        pat = (r'<figure[^>]*>([\s\S]*?)</figure>|<div class="tip-box">([\s\S]*?)</div>'
               r'|<div class="dialogue">\s*<div class="who">(.*?)</div>\s*<p>([\s\S]*?)</p>\s*</div>'
               r'|<p[^>]*>([\s\S]*?)</p>')
        for part in re.finditer(pat, blk, re.S):
            f, tip, who, dl, para = part.groups()
            if f is not None:
                im = re.search(r'<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"', f)
                if im:
                    md.append(f'![{im.group(2)}]({BASE}/{im.group(1)})\n')
            elif tip is not None:
                for q in re.finditer(r'<p>([\s\S]*?)</p>', tip, re.S):
                    tt = inline(q.group(1))
                    tt = re.sub(r'^\*\*(.+?)\*\*', r'**\1**\n', tt)
                    md.append(f'{tt}\n')
            elif who is not None:
                md.append(f'**{inline(who)}**：{inline(dl)}\n')
            elif para is not None:
                tt = inline(para)
                if tt:
                    md.append(f'{tt}\n')
    # 開場（scene 之前）
    head = body.split('<section class="scene">')[0]
    opening = [inline(x) for x in re.findall(r'<p[^>]*>([\s\S]*?)</p>', head, re.S)]
    opening = [o for o in opening if o]

    date = iso[:10] if iso else ''
    hhmm = iso[11:16].replace(':', '') if iso else '0000'
    fm = ['---', f'title: "{title}"', f'date: "{date}"', f'display_date: "{display or date}"',
          f'publish_time: "{iso[11:19] if iso else ""}"', f'iso_date: "{iso}"',
          f'keywords: "{kw}"', f'description: "{desc}"', 'author: "滢滢"',
          'category: "陈皮故事"', 'status: 已发布', 'website: yiyichenpi',
          f'url: "{BASE}/{slug}"', '---', '', f'# {title}', '']
    safe = re.sub(r'[《》/\\:*?"<>|]', '', title)[:40]
    out = DONE / f'{date}-{hhmm}-{safe}.md'
    out.write_text('\n'.join(fm) + ('\n'.join(opening) + '\n\n' if opening else '') + '\n'.join(md) + '\n',
                   encoding='utf-8')
    tt = out.read_text(encoding='utf-8')
    print(f'  歸檔 {out.name}  {out.stat().st_size/1024:.1f} KB  '
          f'h2={len(re.findall(chr(94) + "## ", tt, re.M))}  圖={tt.count("![")}  '
          f'對話={len(re.findall(chr(94) + r"\\*\\*.+?\\*\\*：", tt, re.M))}')
    print(f'  已发布 總數: {len(list(DONE.glob("*.md")))} 檔')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ''))
