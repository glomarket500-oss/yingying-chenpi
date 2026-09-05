# 陈皮新文章标准模板 v1.0

> **生效日期：** 2026-09-06
> **对齐文章：** article-20260904-2247（央视曝光）+ article-20260906-0117（那一年的陈皮）

---

## 📂 默认模板

**最新默认模板：** `scripts/DEFAULT_TEMPLATE.md`  
**来源：** `2026-09-06-0255-那一年的陈皮，那一罐时光.md`（9月6日已发布文章）  
**模板字数：** 4048 字符 / 4幕场景 + 5条FAQ段落式  

**为什么用已发布的最佳文章作为模板？**
- ✅ 永远用最新的最佳结构
- ✅ 不会因为脚本里硬编码而与新文章脱节
- ✅ 每次新文章发布后，可以手动 `cp 已发布/最新.md scripts/DEFAULT_TEMPLATE.md` 升级模板

---

## 🎯 铁律清单（发布前必检）

| 编号 | 铁律 | 检查方法 |
|------|------|----------|
| 1 | **四幕场景结构** | 開場 → 客人到訪 → 滢瀅姐講解 → 離開之前 |
| 2 | **人物对话推动** | 滢瀅姐 + 客人，全文对话占比 > 40% |
| 3 | **当天热点融入** | 自然带入，不标签框 |
| 4 | **FAQ 段落式** | 至少 3-5 条，**不用** tip-box 包裹 |
| 5 | **时间精确到秒** | `xxxx年x月x日 xx:xx:xx` |
| 6 | **错别字** | 「滢瀅」不是「瀅瀅」「滢瀅」 |
| 7 | **SEO** | title/description/keywords/canonical/og:/twitter |
| 8 | **GEO** | geo.position/ICBM/geo.placename |
| 9 | **Schema** | BlogPosting + FAQPage + Person + LocalBusiness |
| 10 | **标签圆角胶囊** | 不要裸字符串、不要带引号 |

---

## 📐 页面结构（必须按顺序）

```
[导航栏 nav]  ← 引用外部 css/style.css
[面包屑 breadcrumb]  ← 「首頁 · 陳皮日記 · 文章标题」
[文章头部 article-header]
  ├── H1 标题
  ├── article-meta（📅 👤 📍 🕐）
  └── article-tags（5个圆角胶囊）
[文章正文 article-content]
  ├── ## 開場（场景描述）
  ├── ## 一、（第一幕 + 对话）
  ├── ## 二、（第二幕 + 对话）
  ├── ## 三、（第三幕 + 对话）
  ├── ## 四、（第四幕 + 对话）
  ├── ## 今日茶識小貼士（段落式）
  ├── ## 常見問題（5条 FAQ 段落式）
  └── ## 結語
[CTA cta-box]
[相关文章 related]
[页脚 footer]
```

---

## 🏷️ Frontmatter 模板

```yaml
---
title: "完整文章标题（含副标题）"
description: "120-160字摘要，含核心关键词 + 行动召唤"
keywords: "新会陈皮,陈皮收藏,陈皮年份,陈皮价格,陈皮储存,滢瀅姐,新会天马"
author: "瀅瀅"
date: "2026-09-XX"
display_date: "2026年09月XX日"
publish_time: "HH:MM:SS"
iso_date: "2026-09-XXTHH:MM:SS+08:00"
url: "https://yingying-chenpi.vercel.app/article-YYYYMMDD-HHMM.html"
image: "https://yingying-chenpi.vercel.app/images/chenpi-hero.jpg"
tags: ["新會陳皮", "陳皮收藏", "陳皮年份", "陳皮價格", "天馬村"]
status: "草稿"
website: "yingying-chenpi"
source: "原創"  # 或「热点改编」
---
```

---

## 💬 对话模板（CSS样式已就绪）

直接用 `「」` 引号包对话：

```markdown
「瀅瀅姐，我買嘅陳皮係咪真嘅？」客人問。

「你睇——」瀅瀅姐指住油室，「真新會皮嘅油室飽滿、大小不一。」
```

**不要用：**
- ❌ `**Q：xxx**` 这种清单格式
- ❌ `**第N招：xxx**` 这种列表格式
- ❌ `❓ Q&A` 这种区块

---

## 📋 FAQ 段落式模板

```markdown
## 常見問題

**Q1：xxx？**
A：xxx。

**Q2：xxx？**
A：xxx。
```

**会被自动提取到 FAQPage Schema**（生成HTML时正则在抽取）

---

## 🔍 SEO GEO 元数据（脚本自动生成）

脚本 `publish_chenpi.py --publish` 会自动生成：

### SEO Meta
- `<title>` 含核心关键词
- `<meta description>` 120-160字摘要
- `<meta keywords>` 5-8个相关词
- `<link rel="canonical">` 标准URL
- `og:title/description/image/url/locale/article:*`
- `twitter:card/title/description/image`

### GEO Meta
- `<meta name="geo.position" content="22.5317;113.0286">`
- `<meta name="geo.placename" content="新會, 江門, 廣東">`
- `<meta name="geo.region" content="CN-GD">`
- `<meta name="ICBM" content="22.5317, 113.0286">`

### Schema.org JSON-LD
1. **BlogPosting** — 文章主体结构化
2. **FAQPage** — FAQ部分自动提取
3. **Person** — 滢瀅姐作者权威
4. **LocalBusiness** — 新会天马村地理位置

---

## 🎨 排版细节

| 元素 | 样式 |
|------|------|
| 面包屑 | `0.82rem`，灰色 `#999`，链接棕色 `#8b4513` |
| H1 标题 | `1.6rem`，粗体，棕色，margin-bottom 16px |
| H2 场景标题 | `1.2rem`，棕色左边框 3px |
| H3 小标题 | `1.05rem`，深灰 `#444` |
| 段落 p | `0.96rem`，行高 1.8，两端对齐，颜色 `#444` |
| Blockquote | `#f5f0eb` 浅棕底，棕色左边框 3px，斜体 |
| Strong | 棕色 `#8b4513` |
| 表格 th | 棕底白字 |
| CTA | 棕色渐变背景，白色文字 |
| 标签 a | 浅棕底，棕色文字，hover棕底白字 |
| Meta span | 浅棕底圆角胶囊 |
| Footer | 居中，灰色，14号 |

---

## 📜 Markdown 语法规范

### 标题
```markdown
## 開場：標題
## 一、第一幕：標題
## 二、第二幕：標題
## 三、第三幕：標題
## 四、第四幕：標題
## 今日茶識小貼士
## 常見問題
## 結語
```

### 段落
直接写文字，**不要**用 `**第一招**` 之类的清单。

### 对话
```markdown
「瀅瀅姐，xxx？」客人問。
「xxx。」瀅瀅姐答。
```

### blockquote（可选）
```markdown
> 引文或角色回忆
```

### 表格（可选）
```markdown
| 項目 | 內容 |
|------|------|
| 核心產區 | 新會天馬、梅江、茶坑、東甲 |
```

---

## 🚀 发布流程

1. **生成/写稿** → 放 `vault/滢滢姐讲陈皮故事/草稿/`
2. **用户说「OK」/「确定」** → 确认内容
3. **运行发布**：
   ```bash
   python Desktop/chenpi-website/scripts/publish_chenpi.py --publish "草稿路径.md"
   ```
4. **脚本自动执行**：
   - ✅ Frontmatter 解析
   - ✅ Markdown → HTML
   - ✅ FAQ 自动提取 → FAQPage Schema
   - ✅ 完整 SEO/GEO Meta 生成
   - ✅ 发布前自检（错别字/标签引号/必备元素）
   - ✅ 生成 article-YYYYMMDD-HHMM.html
   - ✅ 更新 index.html featured + articles.html 列表
   - ✅ git add/commit/push（10次重试，5分钟间隔）
   - ✅ 移动草稿到「已发布」

---

## ⚠️ 不要做的事

- ❌ 直接写HTML标签（脚本会自动转）
- ❌ 使用「瀅瀅」字（错别字，会被自检拦下）
- ❌ 标签字符串带引号 `""`
- ❌ 段落用「第一招/第二招」清单格式
- ❌ 把FAQ包在 `tip-box` 或 `💡 陳皮小知識` 容器
- ❌ 时间只写 `xx:xx`（必须 `xx:xx:xx`）
- ❌ 跳过用户确认直接推送
- ❌ 在草稿里直接生成 `<style>` 内联CSS

---

## 📁 相关文件

- **发布脚本：** `scripts/publish_chenpi.py`
- **样式表：** `css/style.css`（统一外部CSS，零内联）
- **参考文章：**
  - `article-20260904-2247.html`（央视曝光，标准模板）
  - `article-20260906-0117.html`（那一年的陈皮，对话驱动）
- **草稿箱：** `vault/滢滢姐讲陈皮故事/草稿/`
- **已发布：** `vault/滢滢姐讲陈皮故事/已发布/`