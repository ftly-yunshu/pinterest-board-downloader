---
name: pinterest-downloader
description: "下载 Pinterest 画板中的全部图片和视频。当用户要求爬取/抓取/下载 Pinterest 画板的图片或视频时触发，例如'帮我爬这个Pinterest画板''下载Pinterest画板的所有图片''把Pinterest画板保存到本地''Pinterest画板下载器''pinterest board download'等。支持自动提取高清图片、检测并下载MP4视频、缩略图升级为高清版。"
---

# Pinterest 画板下载器

一键将 Pinterest 画板中的**全部图片和视频**批量下载到本地。

## 触发条件

用户请求包含以下意图时使用此 Skill：

| 示例 | 关键词 |
|------|--------|
| "帮我爬这个 Pinterest 画板" | 爬取、抓取 |
| "下载 Pinterest 画板的所有图片" | 下载、保存 |
| "把这个 Pinterest 画板备份到本地" | 备份、本地化 |
| "Pinterest 画板下载" | 下载 |

## 前置依赖

运行前确保系统已安装必要依赖（仅需一次）：

```bash
pip install playwright aiohttp
playwright install chromium
```

检查 Python 版本（需要 3.8+）：
```bash
python3 --version
```

## 执行流程

### Step 1: 确定参数

从用户输入获取：

- **`board_url`** — 用户提供的 Pinterest 画板 URL（必填）
  - 格式：`https://www.pinterest.com/{user}/{board-name}/`
- **`output_dir`** — 输出目录（可选，默认为当前目录下 `pinterest_{board-name}/`）

### Step 2: 运行脚本

```bash
python3 <SKILL_PATH>/scripts/pinterest_download.py <BOARD_URL> [OUTPUT_DIR]
```

其中 `<SKILL_PATH>` 为 skill 安装后的实际路径。

### Step 3: 报告结果

向用户报告：

- 画板地址、成功下载的图片数量 / 失败数量
- 发现并下载的视频数量
- 小图高清化升级的数量
- 总文件大小和输出路径
- 如有异常情况（需登录、网络错误等）需说明

## 工作原理

脚本自动执行 5 个阶段：

1. **数据收集** — Playwright 浏览器滚动加载画板，从 DOM 提取图片 URL 和 Pin 链接
2. **视频检测** — aiohttp 并发请求每个 Pin 页面（~100x 比浏览器快），正则匹配 MP4/M3U8
3. **图片下载** — urllib 批量下载，多尺寸 CDN 变体回退（originals→736x→564x...），断点续传
4. **视频下载** — MP4 直链下载到 `videos/` 子目录
5. **高清化升级** — 自动替换 <15KB 的缩略图为更高分辨率版本

## 输出结构

```
output_dir/
├── pinterest_0001.jpg       # 图片
├── ...
├── videos/
│   └── video_001_xxx.mp4   # 视频
└── _*_cache.txt             # 缓存文件（可删）
```

## 已知限制

| 问题 | 说明 | 解决方案 |
|------|------|---------|
| 私密画板 | 可能需要登录才能访问 | 提示用户；可改 `headless=False` 手动登录 |
| 覆盖率 | 通常 95%-98%，少数遗漏 | 可重跑，已有文件自动跳过 |
| 仅 M3U8 视频 | 部分 Pin 只有 HLS 流 | 需要 `ffmpeg -i x.m3u8 -c copy out.mp4` |
| DNS 临时失败 | 网络波动 | 重跑即可 |

## 故障排查

- **0 张图片收集到**：页面被拦截或需登录，增加等待时间或检查 URL
- **图片全是小图 (<10KB)**：CDN 返回了缩略图，脚本会自动执行高清化阶段
- **Playwright 安装失败**：加 `--break-system-packages` 或使用 venv
