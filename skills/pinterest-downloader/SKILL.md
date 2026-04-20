---
name: pinterest-downloader
description: "下载 Pinterest 画板中的全部图片和视频到本地。当用户要求爬取/抓取/下载/保存/备份 Pinterest 画板的图片或视频时触发，例如'帮我爬这个Pinterest画板''下载Pinterest画板的所有图片''把Pinterest画板保存到本地''Pinterest画板下载器''pinterest board download''Pinterest原图下载''Pinterest高清下载''批量保存Pinterest''私密画板下载'等。特性：优先抓取 /originals/ 原图、并发下载+重试退避、视频 MP4 自动下载、HLS(m3u8) 清单导出、Netscape cookies 支持私密画板、断点续传、自动去重。"
version: 3.0.0
license: MIT
---

# Pinterest 画板下载器

一键将 Pinterest 画板中的**全部图片和视频**批量下载到本地。

## 何时触发此 Skill

用户意图示例（任一匹配即可触发）：

| 中文表述 | 英文表述 |
|----------|----------|
| 爬/抓/下载 Pinterest 画板 | scrape / crawl / download pinterest board |
| 把这个 Pinterest 画板保存/备份到本地 | save / backup pinterest board |
| Pinterest 原图下载 / 高清下载 | pinterest original / high-res download |
| 下载 Pinterest 视频 | download pinterest video |
| 私密画板下载 | private board / secret board download |

## 关键能力（v3.0）

- ✅ **原图优先**：滚动阶段从 `srcset` 读最大尺寸，下载阶段按 `/originals/ → /1200x/ → /736x/ …` 顺序尝试
- ✅ **并发下载**：默认 8 并发，每张 3 次指数退避重试，应对 429/503 限流
- ✅ **断点续传**：`_manifest.txt` 持久化记录，重跑自动跳过已完成
- ✅ **视频支持**：MP4 直链自动下载；HLS (m3u8) 导出清单供 ffmpeg 处理
- ✅ **私密画板**：`--cookies cookies.txt`（Netscape 格式，浏览器扩展导出即可）
- ✅ **反爬避免**：UA 轮换、滚动节奏抖动、请求间隔抖动
- ✅ **去重**：URL 归一化为原图猜测值作为 key，跨次运行也能去重

## 前置依赖（一次性）

```bash
pip install playwright aiohttp
playwright install chromium
```

要求 Python 3.8+。

## 执行流程（给 AI 的指令）

### Step 1 · 确定参数

从用户输入提取：

| 参数 | 必填 | 说明 |
|------|------|------|
| `board_url` | ✅ | `https://www.pinterest.com/{user}/{board}/` |
| `output` | ❌ | 输出目录，默认 `pinterest_{board-name}/` |
| `cookies` | ❌ | 私密画板时要求用户提供 `cookies.txt` |
| `concurrency` | ❌ | 若用户说"快一点"可调到 12-16；说"温和一点"降到 3-5 |
| `max_pins` | ❌ | 用户说"先试 50 张"时传入 |

### Step 2 · 运行脚本

基础用法：
```bash
python3 <SKILL_PATH>/pinterest_download.py <BOARD_URL>
```

带参数：
```bash
python3 <SKILL_PATH>/pinterest_download.py <BOARD_URL> \
    --output ./my_images \
    --concurrency 8 \
    --cookies cookies.txt \
    --name-by pin
```

`<SKILL_PATH>` 是 skill 安装后的实际路径（在 npx skills 标准下通常为 `~/.agents/skills/pinterest-downloader/`）。

### Step 3 · 报告结果

向用户汇报（都由脚本结尾自动输出）：

- 画板地址、输出目录
- 图片成功/失败数
- 视频：MP4 下载成功数 + HLS 待处理数（如有）
- 高清化补救升级数
- 总文件数 + 总大小
- 异常情况（需登录、网络失败等）说明

## 常见场景映射

| 用户说 | 推荐命令 |
|--------|----------|
| "下载这个画板" | 默认参数即可 |
| "画板很大，先试 50 张看看" | `--max-pins 50` |
| "快一点" | `--concurrency 12 --retries 2` |
| "网速一般别太激进" | `--concurrency 3 --scroll-pause 2.5` |
| "这个画板是私密的" | 引导用户用浏览器扩展（如 Get cookies.txt LOCALLY）导出 `cookies.txt`，然后 `--cookies cookies.txt` |
| "不要视频" | `--no-video` |
| "用 Pin ID 命名文件" | `--name-by pin` |

## 输出结构

```
output_dir/
├── pinterest_0001.jpg       # 或 pin_{pinid}_0001.jpg（取决于 --name-by）
├── pinterest_0002.jpg
├── ...
├── videos/
│   └── video_001_{pinid}.mp4
├── videos_hls/
│   └── m3u8_list.txt        # 用 ffmpeg 自行转换
├── _urls_cache.txt          # 采集到的 URL（含 pin_id）
├── _pins_cache.txt          # 所有 Pin ID
├── _video_list.txt          # 视频检测结果
└── _manifest.txt            # 已下载清单（断点续传依据，勿删）
```

## 安全与隐私声明（务必告知用户）

- 本工具**不会**请求、存储或发送 Pinterest 账号密码
- 私密画板仅通过用户主动提供的 `cookies.txt` 访问；cookie 文件始终保留在用户本地
- 下载素材版权归原作者所有，请仅用于**个人离线备份 / 学习研究**，遵守 Pinterest ToS 与当地版权法律
- 不要用于大规模二次传播或商业再分发

## 已知限制与解决方案

| 限制 | 说明 | 解决方案 |
|------|------|---------|
| 私密画板 | 未登录会被重定向 | `--cookies cookies.txt`（Netscape 格式） |
| HLS 视频 | 部分视频仅有 m3u8 流 | 导出到 `videos_hls/m3u8_list.txt`，用 `ffmpeg -i URL -c copy out.mp4` 处理 |
| 超大画板 | 1000+ Pin 滚动耗时 | 用 `--max-pins` 分批，或单独跑 |
| CDN 返回缩略图 | 少数图片没有 /originals/ 版本 | 自动回退到 1200x/736x；阶段 5 再做补救升级 |
| 429/503 限流 | 并发太高触发 | 脚本已自动指数退避；可降低 `--concurrency` |
| Pinterest 改版 | CSS/DOM 变动 | 用 `<a href="/pin/...">` + `srcset` 双路径，兼容性较好；如失效请提 issue |

## 故障排查

| 症状 | 排查 |
|------|------|
| 收集到 0 张图片 | 检查画板 URL；可能需要 cookies；国家/地区网络限制 |
| 大量图片 < 10KB | 脚本的 Phase 5 会自动补救；若仍有则该 pin 源图真的是小图 |
| 频繁 HTTP 429 | 降并发：`--concurrency 3 --scroll-pause 3` |
| Playwright 安装失败 | 用 venv 或 `pip install --break-system-packages` |
| 视频检测 0 个但画板明显有视频 | 视频常为 HLS；查看 `_video_list.txt` 中的 m3u8 条目 |
