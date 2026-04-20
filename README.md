# 📌 Pinterest Board Downloader

<p align="center">
  <strong>一键下载 Pinterest 画板中的全部图片和视频</strong><br>
  <sub>零框架依赖 · AI 友好 · 图片 + 视频 + 高清化升级</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg" alt="Platform" />
</p>

---

## ✨ 特性

- 🖼️ **全量图片下载** — 自动滚动加载画板，提取所有 CDN 图片 URL
- 🎬 **视频自动检测** — 并发扫描 Pin，发现并下载 MP4 视频
- 🔍 **高清化升级** — 自动将小尺寸缩略图替换为高分辨率版本
- ⏭️ **断点续传** — 已下载文件自动跳过，支持中断后重跑
- 🤖 **AI 友好** — 可被任何主流 AI 工具直接调用执行

## 🚀 快速开始

### 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Chromium 浏览器（仅需一次）
playwright install chromium
```

### 一条命令下载

```bash
python3 pinterest_board_downloader.py https://www.pinterest.com/user/board-name/
```

### 指定输出目录

```bash
python3 pinterest_board_downloader.py https://www.pinterest.com/user/board-name/ ./my_downloads
```

## 📖 使用示例

```
$ python3 pinterest_board_downloader.py https://www.pinterest.com/user/ui/

================================================================================
  🎨 Pinterest Board Downloader v2.0
================================================================================
  📍 画板:  https://www.pinterest.com/user/ui/
  📂 输出:  ./pinterest_ui
================================================================================

[12:00:00] 📋 [1/5] 滚动画板收集数据...
[12:01:30]   滚动 #150: 图片 794 张 (+12), Pin 1348 个
[12:02:00] ✅ 收集完成: 794 张图片, 1348 个 Pin

[12:02:00] 🎬 [2/5] 检测视频Pin (1348个)...
[12:02:30] ✅ 视频检测完成: 13 个

[12:02:30] 🖼️ [3/5] 下载图片 (794张)...
[12:05:00] 图片结果: ✓794 ✗0 ⊘0

[12:05:00] 🎥 [4/5] 下载视频 (13个)...
[12:06:00] 视频结果: ✓13 ✗0

[12:06:00] 🔍 [5/5] 小图高清化升级...
[12:07:00] 高清化完成: 118/137 张已升级

================================================================================
  ✅ 全部完成!
================================================================================
  📂 目录:   ./pinterest_ui
  🖼️ 图片:   794 成功, 0 失败
  🎬 视频:   13 成功, 0 失败
  ⬆️ 升级:   118 张小图已高清化
  📦 总计:   807 文件, 88.0 MB
```

## 📁 输出结构

```
pinterest_ui/
├── pinterest_0001.jpg          # 图片（按序号命名）
├── pinterest_0002.jpg
├── ...
├── videos/
│   ├── video_001_333125703.mp4 # 视频
│   └── video_002_333125704.mp4
├── _urls_cache.txt             # 缓存（可删除）
├── _pins_cache.txt             # 缓存（可删除）
└── _video_list.txt             # 缓存（可删除）
```

## ⚙️ 可调参数

编辑脚本顶部的常量即可调整行为：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `SCROLL_PAUSE` | `1.5` | 滚动等待时间（秒）|
| `VIDEO_CONCURRENCY` | `20` | 视频检测并发数 |
| `IMAGE_DELAY` | `0.5` | 图片下载间隔（秒）|
| `HQ_THRESHOLD` | `15360` | 小图阈值（字节），低于此值触发高清化 |

## 🤖 给 AI 的使用说明

本工具设计为 **AI 原生**，任何主流 AI 工具均可使用：

1. 将 `pinterest_board_downloader.py` 和本 README 发给任意 AI
2. AI 会读取文档、安装依赖并执行脚本
3. 向用户报告完整的下载结果

**兼容的 AI 工具：**
ChatGPT · Claude · Gemini · GitHub Copilot · Cursor · Windsurf · WorkBuddy · 其他支持代码执行的 AI

## 🔧 技术实现

| 阶段 | 技术 | 说明 |
|------|------|------|
| 数据采集 | Playwright + Chromium | 模拟滚动加载画板 DOM |
| 视频检测 | aiohttp 并发 HTTP | 正则从 Pin 页面 HTML 匹配视频 URL |
| 图片下载 | urllib 多尺寸回退 | originals → 736x → 564x → 474x |
| 视频下载 | urllib 直连 | 优先 MP4，支持 M3U8（需 ffmpeg）|
| 高清化 | CDN 尺寸替换 | 同一 hash 不同尺寸路径替换 |

## ⚠️ 注意事项

- 私密画板可能需要登录才能访问
- 通常能获取 95%-98% 的 Pins，少数可能遗漏
- 内置礼貌延迟以避免被封 IP
- 网络波动时重跑即可，已下载文件会自动跳过

## 📄 License

MIT License — 自由使用、修改和分发。

---

<p align="center">
  ⭐ 如果这个工具有帮助，欢迎给个 Star！
</p>
