# 📌 Pinterest Board Downloader Skill

<p align="center">
  <strong>一键下载 Pinterest 画板中的全部图片和视频</strong><br>
  <sub>npx Skills 标准格式 · AI 原生 · 图片 + 视频 + 高清化升级</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/npx%20skills-add-ready-blue" alt="npx skills" />
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</p>

---

## 🚀 安装

```bash
npx skills add https://github.com/ftly-yunshu/pinterest-board-downloader --skill pinterest-downloader
```

安装后，任何 AI 助手（WorkBuddy / CodeBuddy / 兼容的 Agent 框架）都能自动识别并使用此技能。

## 📖 使用方法

安装后，用户只需说：

> **"帮我下载这个 Pinterest 画板的所有图片：`https://www.pinterest.com/user/board-name/`"**

AI 会自动：
1. 识别触发词 → 加载此 Skill
2. 安装依赖（playwright + aiohttp）
3. 执行下载脚本 → 完成全量采集
4. 报告结果（图片数、视频数、文件大小）

### 手动运行（不通过 AI）

```bash
pip install playwright aiohttp
playwright install chromium

python3 skills/pinterest-downloader/scripts/pinterest_download.py https://www.pinterest.com/user/board-name/
```

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🖼️ **全量图片采集** | 自动滚动加载画板，提取所有 CDN 图片 URL |
| 🎬 **视频检测+下载** | 并发扫描 Pin 发现视频，优先下载 MP4 直链 |
| 🔍 **高清化升级** | 自动将小尺寸缩略图替换为高分辨率版本 |
| ⏭️ **断点续传** | 已下载文件自动跳过，支持中断后重跑 |

## 📁 仓库结构

```
pinterest-board-downloader/
├── skills/
│   └── pinterest-downloader/
│       ├── SKILL.md                    # 技能定义（触发词 + 工作流程）
│       └── scripts/
│           └── pinterest_download.py   # 核心下载脚本
├── README.md                           # 本文件
├── LICENSE                             # MIT 协议
├── requirements.txt                    # Python 依赖
└── .gitignore
```

## 🔧 工作原理

| 阶段 | 技术 | 说明 |
|------|------|------|
| 数据收集 | Playwright + Chromium | 浏览器自动化滚动加载 |
| 视频检测 | aiohttp 并发 HTTP | ~100x 比浏览器逐个打开快 |
| 图片下载 | urllib + CDN 变体回退 | originals→736x→564x→474x |
| 视频下载 | urllib MP4 直连 | 保存到 videos/ 子目录 |
| 高清化 | CDN 尺寸替换 | 自动升级小图到高分辨率 |

## ⚠️ 注意事项

- 私密画板可能需要登录才能访问
- 通常能获取 95%-98% 的 Pins
- 内置礼貌延迟避免被封 IP

## 📄 License

MIT — 自由使用、修改和分发。

---

<p align="center">
  安装命令：<code>npx skills add https://github.com/ftly-yunshu/pinterest-board-downloader --skill pinterest-downloader</code>
</p>
