# -*- coding: utf-8 -*-
"""publish.py —— 陳皮網站唯一發布入口（閘門①）

用法：
    python publish.py --draft <草稿.md>                        # 一般文章（AI 生圖）
    python publish.py --draft <草稿.md> --video <影片.mp4>      # 指定影片（從該影片抽幀）
    python publish.py --draft <草稿.md> --dry-run               # 只渲染＋自檢，不推送
    python publish.py --draft <草稿.md> --slug 20261012-1400     # 指定 slug 時分

它會自動完成：
  1. 讀草稿 → 轉繁體（OpenCC s2hk）＋品牌名修正
  2. 解析結構（開場／幕N／常見問題／結語）→ 套用本站唯一模板
  3. 引號對話 → <div class="dialogue"> 對話框
  4. 配圖：封面 1 ＋ 每幕 1（AI 生圖 Z-Image-Turbo；--video 則從影片抽幀）
     自動裁掉「AI 生成」浮水印、壓到 200KB 以內、網址帶 ?v=1
  5. 更新 articles.html 卡片（含縮圖）＋ sitemap.xml
  6. 發布前自檢（finalize_article.py 的 25 項）—— 不過就中止
  7. git add 白名單 → commit → push（經過 pre-push 健康檢查）
  8. 等部署 → 線上驗證 → 歸檔到知識庫

任一關卡失敗 → 印出「❌ 發布錯誤：XXX」並中止，不會硬推上線。
"""
import argparse
import datetime
import html as H
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

WORK = Path(__file__).resolve().parent
REPO = Path(r'C:/Users/a/Desktop/chenpi-website')
IMG = REPO / 'images'
KB = Path(r'C:\Users\a\Desktop\MianAI知识库\MianAI知识库\vault\滢滢姐讲陈皮故事')
DONE = KB / '已发布'
BASE = 'https://www.yiyichenpi.com'
PY = sys.executable
# 有 opencc 的系統 Python（subprocess 的 python 會指到沒有 opencc 的解釋器）
SYS_PY = r'C:\Users\a\AppData\Local\Programs\Python\Python314\python.exe'
if not Path(SYS_PY).is_file():
    SYS_PY = 'python'


sys.path.insert(0, str(WORK))
from build_1001_lib import page  # noqa: E402

SILICONFLOW_KEY = os.environ.get(
    'SILICONFLOW_API_KEY', 'sk-jhgawfojcrxkourpckzgfkythreuamssqmrbjkffcpoeurxj')
SF_URL = 'https://api.siliconflow.cn/v1/images/generations'
NEG = ('people, person, human, hands, fingers, arms, faces, portrait, mannequin, text, watermark, '
       'logo, signature, label, chinese characters, blurry, low quality, cartoon, illustration, '
       '3d render, oversaturated, candied fruit, fresh orange slices')
SPEAKERS = ['梁阿婆', '阿婆', '梁師傅', '梁师傅', '梁偉', '梁伟', '老張', '老张', '老陳', '老陈',
            '滢滢姐', '滢滢', '吳小姐', '吴小姐', '張先生', '张先生', '陳伯', '陈伯', '周伯', '小年']
QUOTE = re.compile(r'[「“"]([^」”"]{2,})[」”"]')
SIMP_CHECK = ('东个仓会录视记车这陈频诚护丰监签题买卖价钱产业广张报数标热现经统营认让议识'
              '资软钟钱摄变场体传艺镜农树讲还开采丰观众条课带团赚过们为说时间长实际关评赞内药医书马鸟鱼')


def die(msg):
    print(f'\n❌ 發布錯誤：{msg}')
    sys.exit(1)


def step(n, msg):
    print(f'\n[{n}] {msg}')




def strip_front_matter(txt):
    """去掉 YAML frontmatter 與行首分隔線。"""
    txt = txt.lstrip('\ufeff')
    if txt.startswith('---'):
        parts = txt.split('---', 2)
        if len(parts) >= 3:
            txt = parts[2]
    txt = re.sub(r'(?m)^\s*---+\s*$', '', txt)
    return txt.lstrip('\n')


def md_tables_to_html(txt):
    """把 Markdown 表格轉成帶樣式的 HTML 表格（其餘原樣保留）。"""
    lines = txt.split('\n')
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('|') and i + 1 < len(lines) and re.match(r'^\s*\|?[\s:|-]+\|[\s:|-]*$', lines[i + 1]):
            head = [c.strip() for c in line.strip().strip('|').split('|')]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            th = ''.join(f'<th style="padding:8px 10px;border-bottom:2px solid #e3d5c0;text-align:left;font-weight:700">{c}</th>' for c in head)
            body = ''
            for r in rows:
                r = (r + [''] * len(head))[:len(head)]
                tds = ''.join(f'<td style="padding:8px 10px;border-bottom:1px solid #f0e8dc;vertical-align:top">{c}</td>' for c in r)
                body += f'<tr>{tds}</tr>'
            out.append('<div style="overflow-x:auto;margin:18px 0">'
                       '<table style="width:100%;border-collapse:collapse;font-size:.95em;background:#fffdf9">'
                       f'<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>')
            continue
        out.append(line)
        i += 1
    return '\n'.join(out)


# ---------------------------------------------------------------- 1. 讀草稿
def read_draft(path):
    p = Path(path)
    if not p.is_file():
        die(f'找不到草稿檔：{path}')
    raw = p.read_text(encoding='utf-8')
    if raw.startswith('\ufeff'):                   # 去掉 BOM（PowerShell 寫的檔案常帶）
        raw = raw.lstrip('\ufeff')
    tmp = WORK / '_draft_conv.md'
    tmp.write_text(raw, encoding='utf-8')
    try:
        from opencc import OpenCC                 # 本行程若有 opencc 就直接用
        tmp.write_text(OpenCC('s2hk').convert(raw), encoding='utf-8')
    except Exception:
        r = subprocess.run([SYS_PY, str(WORK / 'convert_hk.py'), str(tmp), str(tmp)],
                           capture_output=True, text=True, encoding='utf-8')
        if r.returncode != 0:
            last = (r.stderr or '').strip().splitlines()[-1][:150] if r.stderr else ''
            die(f'繁體轉換失敗（請確認 {SYS_PY} 已安裝 opencc）：{last}')
    txt = tmp.read_text(encoding='utf-8')
    txt = txt.replace('瀅瀅', '滢滢').replace('盈盈姐', '滢滢姐')
    txt = re.sub(r'(?<!滢)滢姐(?!滢)', '滢滢姐', txt)
    txt = strip_front_matter(txt)
    txt = md_tables_to_html(txt)
    return txt


# ---------------------------------------------------------------- 2. 解析結構
def split_sections(txt):
    """回傳 [(標題, 內容)]；標題前後綴【】。## 之後的第一段（無標題）視為開場。"""
    out, cur_title, buf = [], None, []
    for line in txt.split('\n'):
        m = re.match(r'^\s*#{1,3}\s*(?:【)?(.+?)(?:】)?\s*$', line)
        if m:
            title = m.group(1).strip()
            if title and title not in ('常見問題',) or True:
                out.append((cur_title, '\n'.join(buf).strip()))
                cur_title, buf = title, []
                continue
        buf.append(line)
    out.append((cur_title, '\n'.join(buf).strip()))
    return [(t, b) for t, b in out if b]


def render_paragraphs(txt, dialogues=True):
    chunks = []
    for raw in [x.strip() for x in txt.split('\n') if x.strip()]:
        if raw.startswith('<div style="overflow-x:auto') or raw.startswith('<table'):
            chunks.append(raw)
            continue
        if re.match(r'^\*\*.+\*\*$', raw):      # 純粗體小標題
            chunks.append(f'<p><strong>{raw.strip("*")}</strong></p>')
            continue
        if raw.startswith('!['):                 # 草稿自帶圖片 → 略過（一律重新生圖）
            continue
        if dialogues:
            who = None
            for sp in SPEAKERS:
                if re.search(re.escape(sp) + r'(說|说|問|问|道|點頭|点头|插話|插话|嘆|叹|解釋|解释|笑|喊)', raw):
                    who = sp.replace('梁师傅', '梁師傅').replace('梁伟', '梁偉')
                    break
            # 補充：形如「某某（動作）：『…』」— 取冒號前的名字（含動作描述也能認）
            if not who:
                m2 = re.match(r'^(.{2,24}?)[：:]\s*[「“"]', raw)
                if m2:
                    cand = m2.group(1)
                    nm = re.match(r'^([\u4e00-\u9fff]{2,4})', cand)
                    who = nm.group(1) if nm else cand[:4]
                    who = re.sub(r'(笑|說|说|問|问|道|着|著|搖頭|摇头|沉默|嘆氣|叹气|點頭|点头|插話|插话)+$', '', who) or who
            quotes = QUOTE.findall(raw)
            if who and quotes:
                rest = QUOTE.sub('', raw)
                rest = re.sub(r'^[\s，。：、」」]*', '', rest).strip()
                for q in quotes:
                    chunks.append('<div class="dialogue">\n'
                                  f'                        <div class="who">{who}</div>\n'
                                  f'                        <p>「{q}」</p>\n                    </div>')
                if len(rest) > 8:
                    chunks.append(f'<p>{rest}</p>')
                continue
        chunks.append(f'<p>{raw}</p>')
    return '\n                    '.join(chunks)


# ---------------------------------------------------------------- 3. AI 生圖
def ai_image(prompt, out_name, tmpdir):
    payload = {'model': 'Tongyi-MAI/Z-Image-Turbo', 'prompt': prompt, 'image_size': '1024x576',
               'batch_size': 1, 'num_inference_steps': 8, 'negative_prompt': NEG}
    for _ in range(3):
        try:
            req = urllib.request.Request(SF_URL, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                                         headers={'Authorization': f'Bearer {SILICONFLOW_KEY}',
                                                  'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=300) as resp:
                r = json.load(resp)
            if not r.get('images'):
                time.sleep(4)
                continue
            raw = Path(tmpdir) / (Path(out_name).stem + '.png')
            raw.write_bytes(urllib.request.urlopen(r['images'][0]['url'], timeout=240).read())
            im = Image.open(raw).convert('RGB')
            W, H = im.size
            im = im.crop((0, 0, int(W * 0.88), int(H * 0.92)))     # 裁掉「AI 生成」浮水印
            W2, H2 = im.size
            band = int(W2 * 9 / 16)
            if band <= H2:
                top = (H2 - band) // 2
                im = im.crop((0, top, W2, top + band))
            im = im.resize((1280, 720), Image.LANCZOS)
            out = IMG / out_name
            for q in (84, 80, 76, 72, 68, 64, 60, 56):
                im.save(out, 'JPEG', quality=q, optimize=True, progressive=True)
                if out.stat().st_size <= 200 * 1024:
                    break
            print(f'      {out_name}  {out.stat().st_size/1024:.0f} KB')
            return True
        except urllib.error.HTTPError as e:
            print(f'      HTTP {e.code}')
        except Exception as e:
            print(f'      {type(e).__name__}')
        time.sleep(4)
    return False


def video_frame(video, ts, out_name, tmpdir, size=(1280, 720)):
    raw = Path(tmpdir) / f'v_{Path(out_name).stem}.png'
    ct = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=color_transfer',
                         '-of', 'csv=p=0', str(video)], capture_output=True, text=True).stdout
    hdr = any(k in ct for k in ('arib', 'smpte2084', 'bt2020'))
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', str(ts), '-i', str(video)]
    if hdr:
        cmd += ['-vf', ('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,'
                        'tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p')]
    cmd += ['-frames:v', '1', '-y', str(raw)]
    if subprocess.run(cmd, check=False).returncode != 0 or not raw.exists():
        return False
    im = Image.open(raw).convert('RGB')
    W, H = im.size
    band = int(W * size[1] / size[0])
    if band <= H:
        im = im.crop((0, (H - band) // 2, W, (H - band) // 2 + band))
    im = im.resize(size, Image.LANCZOS)
    out = IMG / out_name
    for q in (84, 80, 76, 72, 68, 64, 60, 56):
        im.save(out, 'JPEG', quality=q, optimize=True, progressive=True)
        if out.stat().st_size <= 200 * 1024:
            break
    print(f'      {out_name}（影片抽幀）  {out.stat().st_size/1024:.0f} KB')
    return True


def scene_prompt(title, body, idx, total):
    """把幕的內容轉成 AI 生圖提示（物件與場景為主，避開人手人臉文字）。"""
    style = ('Realistic documentary photograph, Xinhui Guangdong China, natural light, '
             'objects and scenery only, no people, no text. ')
    kw = []
    text = title + ' ' + body
    for k, p in [
        ('賬|账|算|成本|價格|价格', 'an open lined notebook with columns of numbers, a calculator, a pen '
                                    'and a small pile of dried tangerine peel on a dark wooden table'),
        ('圈枝|駁枝|驳枝|油室|品種|品种', 'two pieces of dried tangerine peel side by side on a slate surface, '
                                        'one thick with dense raised oil cells, the other thinner and paler'),
        ('倉|仓|存|陳化|陈化|三年', 'rows of large sealed ceramic jars and stacked cardboard boxes inside a '
                                    'clean dry storage warehouse, a humidity meter on the wall'),
        ('收購|收购|交易|市場|市场|議價|议价', 'a produce trading yard with parked trucks and stacked crates of '
                                              'fresh green tangerines, a platform scale, morning light'),
        ('曬|晒|月光|夜', 'rows of drying tangerine peel laid out on bamboo mats in an open yard, '
                          'soft light, quiet atmosphere'),
        ('柑園|柑园|果樹|果树|採摘|采摘|掉果|颱風|台风', 'a tangerine orchard in October with green-yellow fruit '
                                                       'on the trees and fallen fruit on the grass, misty morning'),
        ('茶|泡|飲|饮', 'a clay teapot and two glass cups of clear amber tangerine peel tea on a wooden tray, steam rising'),
        ('青皮|二紅|二红|大紅|大红|三段|三個階段|三个阶段', 'three shallow dishes of tangerine peel in three colours side by side on a dark wood table, pale green-brown, amber-red and deep red-brown, natural light'),
        ('開皮|开皮|一果兩剪|一果两剪|刀|三瓣', 'a freshly opened tangerine peel spread into three even petals on a bamboo tray, the fruit separated, oil cells visible, clean bright light'),
        ('倉|仓|翻倉|翻仓|防霉|蟲|虫|儲存|储存|陳化|陈化', 'rows of large ceramic jars and stacked cardboard boxes in a dry storage room, humidity meter and hygrometer on the wall, cool even light'),
        ('店|門店|门店|客戶|客户|定制', 'a tidy dried-goods shop counter with glass jars of tangerine peel of '
                                        'different ages and plain brown paper bags, warm wood shelving'),
    ]:
        if re.search(k, text):
            kw.append(p)
    if not kw:
        kw = ['a bamboo tray of sun-dried Xinhui tangerine peel in a courtyard']
    picked = kw[idx % len(kw)]
    return style + picked


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--draft', required=True)
    ap.add_argument('--video', default=None, help='指定影片時，場景圖改從該影片抽幀')
    ap.add_argument('--slug', default=None, help='YYYYMMDD-HHMM')
    ap.add_argument('--title', default=None)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--skip-images', action='store_true',
                    help='沿用已存在的圖片（不重新生成）')
    args = ap.parse_args()

    now = datetime.datetime.now()
    slug_time = args.slug or now.strftime('%Y%m%d-%H%M')
    SD = f'article-{slug_time}'
    SLUG = SD + '.html'
    if (REPO / SLUG).exists():
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', SLUG], cwd=REPO,
                                 capture_output=True, text=True).returncode == 0
        if tracked:
            die(f'{SLUG} 已存在且已提交，換一個 --slug')
        (REPO / SLUG).unlink()
        print(f'    （清掉上次未完成的 {SLUG}）')
    ISO = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    DISPLAY = now.strftime('%Y年%m月%d日 %H:%M:%S')

    step(1, '讀取草稿並轉繁體')
    txt = read_draft(args.draft)
    left = sorted({c for c in SIMP_CHECK if c in txt})
    print(f'    {len(txt)} 字元；簡體殘留：{left or "無 ✓"}')
    if left:
        die(f'草稿仍有簡體字：{left}')

    step(2, '解析結構')
    secs = split_sections(txt)
    h1 = re.search(r'^\s*#\s+(.+)$', txt, re.M)
    title = args.title or (h1.group(1).strip() if h1 else '')
    title = re.sub(r'^【|】$', '', title).strip()
    if not title or len(title) < 6:
        die('抓不到文章標題（草稿請用 # 標題 開頭）')
    body_secs = [(t, b) for t, b in secs if (t is None) or (t != title and title[:8] not in t)]
    acts = [(t, b) for t, b in body_secs
            if re.search(r'幕|場景|场景|^[一二三四五六七八九十]+[、.．]', t or '') 
            and not re.search(r'常見問題|常见问题|FAQ|結語|结语', t or '')]
    faq_sec = next((b for t, b in body_secs if re.search(r'常見問題|常见问题|FAQ', t or '')), '')
    opening = next((b for t, b in body_secs if t is None), '')
    if not opening:
        same = [b for t, b in secs if t == title and b]
        opening = same[0] if same else ''
    closing = next((b for t, b in body_secs if re.search(r'結語|结语', t or '')), '')
    print(f'    標題：{title}')
    print(f'    開場 {len(opening)} 字；幕 {len(acts)} 個；FAQ {len(faq_sec)} 字；結語 {len(closing)} 字')
    if not acts:
        die('解析不到任何「幕」——請確認草稿用 ## 幕一／幕二… 分段')

    step(3, f'配圖（{"沿用既有 AI 圖" if args.skip_images else ("影片抽幀" if args.video else "AI 生圖")}）：封面 1 ＋ 每幕 1 = {len(acts)+1} 張')
    tmpdir = WORK / '_ai_tmp'
    tmpdir.mkdir(exist_ok=True)
    ok = 0
    cover_prompt = ''
    if args.skip_images:
        need = [f'{SD}-1900.jpg'] + [f'{SD}-scene{i}.jpg' for i in range(1, len(acts) + 1)]
        ok = sum(1 for n in need if (IMG / n).is_file())
        print(f'      既有圖片 {ok}/{len(need)} 張')
        if ok != len(need):
            die(f'沿用模式下缺圖：{[n for n in need if not (IMG/n).is_file()]}')
        cover_prompt = ''
    cover_prompt = cover_prompt or scene_prompt(title, opening, 5, 8)
    if not args.skip_images:
        if args.video:
            ok += video_frame(args.video, 3.0, f'{SD}-1900.jpg', tmpdir)
        else:
            ok += ai_image(cover_prompt, f'{SD}-1900.jpg', tmpdir)
    for i, (t, b) in enumerate(acts, 1):
        name = f'{SD}-scene{i}.jpg'
        if args.skip_images:
            continue
        if args.video:
            ok += video_frame(args.video, 3.0 + i * 4, name, tmpdir)
        else:
            ok += ai_image(scene_prompt(t, b, i, len(acts)), name, tmpdir)
    if ok != len(acts) + 1:
        die(f'配圖只成功 {ok}/{len(acts)+1} 張')

    step(4, '套用模板渲染')
    fig = ('<figure class="article-inline-image no-source">\n'
           '                        <img src="images/{}?v=1" alt="{}" loading="lazy">\n'
           '                    </figure>')
    parts = []
    if opening:
        parts.append(render_paragraphs(opening))
    for i, (t, b) in enumerate(acts, 1):
        parts.append('<section class="scene">\n'
                     f'                    <h2>{re.sub(r"^【|】$", "", t)}</h2>\n'
                     '                    ' + fig.format(f'{SD}-scene{i}.jpg',
                                                     re.sub(r'[【】]', '', t)[:40]) + '\n'
                     '                    ' + render_paragraphs(b) + '\n'
                     '                </section>')
    if faq_sec:
        faqs = re.findall(r'\*\*(.+?)\*\*\s*\n\s*([\s\S]*?)(?=\n\*\*|\Z)', faq_sec)
        fh = [f'<p><strong>{q.strip()}</strong>{" ".join(x.strip() for x in a.split(chr(10)) if x.strip())}</p>'
              for q, a in faqs]
        parts.append('<section class="scene">\n                    <h2>常見問題</h2>\n'
                     '                    <div class="tip-box">\n                        '
                     + '\n                        '.join(fh) + '\n                    </div>\n                </section>')
    if closing:
        parts.append('<section class="scene">\n                    <h2>結語</h2>\n                    '
                     + render_paragraphs(closing) + '\n                </section>')
    body = '            <div class="article-body">\n\n                ' + '\n\n                '.join(parts) + '\n\n            </div>\n'

    faq_list = re.findall(r'\*\*(.+?)\*\*\s*\n\s*([\s\S]*?)(?=\n\*\*|\Z)', faq_sec)
    FAQ = [(q.strip(), ' '.join(x.strip() for x in a.split('\n') if x.strip())) for q, a in faq_list]
    if len(FAQ) < 5:
        die(f'FAQ 只有 {len(FAQ)} 條，規範要求 >= 5（請在草稿補足）')
    raw_links = re.findall(r'\[([^\]]+)\]\((article-[^)]+\.html)\)', txt)
    if len(raw_links) < 2:
        die(f'內鏈只有 {len(raw_links)} 條，規範要求 >= 2（請在結語加兩條相關文章連結）')
    links = []
    for label, href in raw_links[:4]:
        lab = label.strip('《》')
        blurb = '相關閱讀'
        tgt = REPO / href
        if tgt.is_file():
            m2 = re.search(r'<meta name="description" content="([^"]*)"', tgt.read_text(encoding='utf-8'))
            if m2 and m2.group(1):
                blurb = m2.group(1)[:36] + '…'
        links.append((href, lab, blurb))

    desc = next((ln.strip() for ln in txt.split('\n')
                 if 40 < len(ln.strip()) < 300 and not ln.strip().startswith(('#', '*', '!', '|'))), title)
    doc = page(SLUG, title,
               desc[:180],
               '新會陳皮,' + ','.join(dict.fromkeys(re.findall(r'[\u4e00-\u9fff]{2,6}', title)))[:120],
               ['新會陳皮', '陳皮故事', '新會', '陳皮村', '養生'],
               ISO, DISPLAY, body, FAQ, links)
    doc = doc.replace(f'images/{SD}-1900.jpg"', f'images/{SD}-1900.jpg?v=1"')
    (REPO / SLUG).write_text(doc, encoding='utf-8')
    print(f'    {SLUG}  {len(doc)} 字元  對話={doc.count(chr(34)+"dialogue"+chr(34))}  figure={doc.count(chr(60)+"figure")}')

    step(5, '更新卡片與 sitemap，並執行 25 項自檢')
    r = subprocess.run([PY, str(WORK / 'finalize_article.py'), SLUG, title,
                        f'{DISPLAY} | 新會陳皮 · 陳皮故事', desc[:160],
                        str(len(acts)), ISO, DISPLAY], capture_output=True, text=True, encoding='utf-8')
    out = (r.stdout or '') + (r.stderr or '')
    print('    ' + '\n    '.join(out.strip().split('\n')[-6:]))
    if 'RESULT:' not in out or 'passed' not in out:
        die('自檢未回報結果')
    m = re.search(r'RESULT:\s*(\d+)/(\d+)\s*passed', out)
    if not m or m.group(1) != m.group(2):
        die(f'自檢未全過：{m.group(0) if m else out[-200:]}')

    if args.dry_run:
        print('\n✅ dry-run 完成：文章已渲染並通過自檢，未提交也未推送。')
        print(f'   檔案：{REPO / SLUG}')
        return

    step(6, '提交（只加白名單檔案）')
    files = [SLUG, 'articles.html', 'sitemap.xml'] + \
            [f'images/{SD}-1900.jpg'] + [f'images/{SD}-scene{i}.jpg' for i in range(1, len(acts) + 1)]
    subprocess.run(['git', 'add'] + files, cwd=REPO, check=False)
    msg = (f'feat: 發布《{title}》\n\n'
           f'由 publish.py 自動發布（閘門①）：\n'
           f'- 草稿：{Path(args.draft).name}\n'
           f'- 結構：開場 ＋ {len(acts)} 幕 ＋ FAQ {len(FAQ)} 條 ＋ 結語\n'
           f'- 配圖：{"影片抽幀" if args.video else "AI 生圖（Z-Image-Turbo，已去浮水印）"}'
           f'，封面 1 ＋ 每幕 1，網址帶 ?v=1\n'
           f'- 自檢：{m.group(0)}\n')
    (WORK / '_commitmsg.txt').write_text(msg, encoding='utf-8')
    subprocess.run(['git', 'commit', '-F', str(WORK / '_commitmsg.txt')], cwd=REPO, check=False)

    step(7, '推送（會經過 pre-push 健康檢查）')
    pushed = False
    for i in range(1, 21):
        p = subprocess.run(['git', 'push', 'origin', 'main'], cwd=REPO,
                           capture_output=True, text=True, encoding='utf-8')
        blob = (p.stdout or '') + (p.stderr or '')
        if p.returncode == 0 and not re.search(r'fatal|rejected|error', blob):
            pushed = True
            print('    PUSH OK' + (f'（第 {i} 次）' if i > 1 else ''))
            break
        if '❌ 新增問題' in blob:
            die('pre-push 健康檢查發現新問題：\n' + blob[-800:])
        if 'rejected' in blob:
            subprocess.run(['git', 'fetch', 'origin'], cwd=REPO, check=False)
            subprocess.run(['git', 'rebase', 'origin/main'], cwd=REPO, check=False)
        time.sleep(12)
    if not pushed:
        die('推送失敗（20 次重試）')

    step(8, '等部署並線上驗證')
    okv = False
    for _ in range(40):
        time.sleep(20)
        try:
            req = urllib.request.Request(f'{BASE}/{SLUG}?nc={int(time.time())}',
                                         headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=40) as x:
                h = x.read().decode('utf-8', 'replace')
            if title[:12] in h and f'-scene1.jpg' in h:
                imgs = re.findall(r'<img[^>]*src="(images/[^"]+)"', h)
                bad = [i for i in imgs if not _head(f'{BASE}/{i}')]
                print(f'    線上 figure={h.count("<figure")}  <img>={len(imgs)}  壞圖={len(bad)}')
                okv = not bad
                break
        except Exception:
            pass
    if not okv:
        print('    ⚠ 線上驗證未在時限內通過（可能部署延遲），請稍後人工確認')

    step(9, '歸檔到知識庫')
    try:
        subprocess.run([PY, str(WORK / 'archive_one.py'), SLUG], check=False)
    except Exception as e:
        print(f'    歸檔失敗：{e}')

    print(f'\n✅ 發布完成：{BASE}/{SLUG}')
    print(f'   自檢：{m.group(0)}')


def _head(u):
    try:
        r = urllib.request.Request(u, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status == 200
    except Exception:
        return False


if __name__ == '__main__':
    main()
