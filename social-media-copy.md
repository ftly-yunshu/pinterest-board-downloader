# Pinterest Board Downloader — 社交媒体推广文案

---

## 🐦 Twitter / X（中文版）

**推文 1 — 功能亮点版**

```
🎨 开源了一个 Pinterest 画板批量下载器，一键把整个 Board 的高清图+视频拉到本地

✅ 原图优先（srcset + /originals/ 六级回退）
✅ 8 并发下载，500 张图 1-2 分钟搞定
✅ 视频全支持（MP4 + HLS）
✅ 私密画板（cookies.txt）
✅ 断点续传 + 增量更新

实测 826 Pin 画板：733 张高清图 + 67 个视频，总大小 679MB，8 分钟全自动完成

GitHub: https://github.com/ftly-yunshu/pinterest-board-downloader
欢迎 Star ⭐

#Pinterest #开源 #Python #爬虫 #设计素材
```

**推文 2 — 痛点切入版**

```
收藏了 800+ 张 Pinterest 设计灵感，想本地备份？
之前试了几个工具，不是只下缩略图就是下一半就卡死……

自己做了一个，解决了这些痛点：
🔸 画质：自动拿最高清版本，不再全是模糊小图
🔸 数量：Playwright 自动滚动，不会只下前 50 张
🔸 视频：画板里的视频也能批量下载
🔸 效率：8 并发 + 自动重试，再不用手动一页页保存

开源免费，Python 一键运行 👇
https://github.com/ftly-yunshu/pinterest-board-downloader

#UI设计 #素材管理 #Pinterest
```

**推文 3 — 数据对比版（适合配图）**

```
同样的 Pinterest 画板（826 Pins），两个工具的下载结果对比：

旧工具 → 794 张图（66% 是缩略图）、13 个视频、88MB、耗时 40 分钟
我的工具 → 733 张高清图 + 67 个视频、679MB、耗时 8 分钟

缩略图比例从 66% 降到 16%，视频数量翻了 5 倍，速度快了 5 倍

画质和效率的差距，一目了然 📊
https://github.com/ftly-yunshu/pinterest-board-downloader

#开源项目 #效率工具
```

---

## 🐦 Twitter / X（英文版）

**Tweet 1 — Feature Highlights**

```
📦 Open-sourced a Pinterest Board Downloader — bulk download all HD images & videos from any public/private board

✅ Original quality (srcset + 6-tier CDN fallback)
✅ 8 concurrent downloads (500 images in ~2 min)
✅ Video support (MP4 + HLS)
✅ Private boards via cookies.txt
✅ Resume & incremental updates

Tested on 826-pin board: 733 HD images + 67 videos, 679MB, fully automated in 8 min

⭐ https://github.com/ftly-yunshu/pinterest-board-downloader

#Pinterest #OpenSource #Python #WebScraping
```

**Tweet 2 — Pain Point Hook**

```
Saved 800+ design references on Pinterest and want a local backup?

Most downloaders either:
❌ Only grab thumbnails (236px)
❌ Stop after the first 50 pins
❌ Crash on video pins

Built one that actually works:
✅ Original quality via srcset parsing
✅ Playwright auto-scroll to get ALL pins
✅ Concurrent download with retry
✅ Video pins fully supported

Free & open source 👇
https://github.com/ftly-yunshu/pinterest-board-downloader

#UIDesign #DesignResources
```

---

## 💬 微信公众号 / 知乎 / 掘金长文

**标题备选：**
- 「收藏了 800 张 Pinterest 灵感图，我写了个工具 8 分钟全部下载到本地」
- 「开源一个 Pinterest 画板批量下载器：原图 + 视频 + 并发 + 断点续传」
- 「从缩略图到原图：我是怎么让 Pinterest 下载器画质提升 7 倍的」

**正文大纲：**

```
【开篇 — 痛点】
作为 UI 设计师，Pinterest 是灵感素材的主要来源。
我的画板里有 800+ 张收藏，想要本地备份——
但市面上的下载工具问题太多：
· 只下缩略图（236px），画质模糊
· 只抓首屏几十张，大画板覆盖不全
· 遇到视频 Pin 直接跳过
· 串行下载，500 张要等 20 分钟

【方案 — 工具介绍】
于是我自己写了一个：pinterest-board-downloader

核心功能：
1️⃣ 原图优先
   从 DOM 的 srcset 属性读取最高分辨率 URL，
   下载时按 /originals/ → /1200x/ → /736x/ 逐级回退

2️⃣ 自动滚动 + 全量采集
   基于 Playwright 模拟浏览器滚动，
   stagnant 检测到底部自动停止，
   双重 URL 去重防止重复下载

3️⃣ 并发下载 + 智能重试
   aiohttp 8 并发，每张图 3 次指数退避，
   429/503/403 全覆盖

4️⃣ 视频全支持
   MP4 直链 + HLS(m3u8) 导出清单

5️⃣ 断点续传 + 增量模式
   _manifest.txt 持久化去重，
   --resume 参数跳过重新滚动只下新增

【效果 — 数据说话】
实测 ftlycold214/ui 画板（826 Pins）：

指标        │ 旧工具    │ 本工具
────────────┼──────────┼──────────
图片数量    │ 794      │ 733
视频数量    │ 13       │ 67
缩略图比例  │ 66%      │ 16%
总大小      │ 88 MB    │ 679 MB
耗时        │ ~40 分钟 │ ~8 分钟

缩略图比例从 66% 降到 16%，总体积翻了 7.7 倍。

【使用方式】
pip install playwright aiohttp
playwright install chromium
python3 pinterest_download.py <画板URL>

也支持 npx skills 安装为 AI Agent Skill：
npx skills add ftly-yunshu/pinterest-board-downloader

【结尾 — 开源地址】
GitHub: https://github.com/ftly-yunshu/pinterest-board-downloader
MIT 开源，欢迎 Star 和 PR ⭐
```

---

## 📱 小红书

**标题：**
```
Pinterest 灵感图太多？8 分钟全部下载到本地！
```

**正文：**

```
设计师必看！🎨

收藏了 800 多张 Pinterest 灵感图，
一直想保存到本地但找不到好工具……

自己做了一个开源下载器，实测效果绝了👇

✨ 画质炸裂
自动下载最高清原图，不再是模糊小图
（实测：总大小从 88MB → 679MB，7.7 倍提升）

⚡ 速度快
8 并发下载，826 张图+视频只要 8 分钟
（以前手动保存一张一张点，太痛苦了）

🎬 视频也能下
画板里的视频 Pin 全部支持下载

🔒 支持私密画板
通过 cookies 导入即可

一行命令搞定：
pip install playwright aiohttp
playwright install chromium

完全免费开源，GitHub 搜：
pinterest-board-downloader

#Pinterest #设计素材 #效率工具 #开源 #Python #UI设计
#设计灵感 #素材整理 #设计师工具
```

---

## 📌 GitHub README 顶部 Badge 更新建议

已在 README.md 中使用，效果预览：

```
![version](https://img.shields.io/badge/version-3.1.0-blue)
![last tested](https://img.shields.io/badge/last%20tested-2026--04--20-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
```

---

## 📂 文件清单

| 文件 | 用途 |
|------|------|
| `promo-banner.png` | 社交媒体配图（1200x630，适配 Twitter/OG 卡片） |
