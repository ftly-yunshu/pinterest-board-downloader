# 📌 Pinterest Board Downloader

<p align="center">
  <strong>一键下载 Pinterest 画板中的全部图片和视频到本地</strong><br>
  <sub>原图优先 · 并发下载 · 视频支持 · 断点续传 · 零依赖上手</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.1.0-blue" alt="version" />
  <img src="https://img.shields.io/badge/last%20tested-2026--04--20-brightgreen" alt="last tested" />
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/playwright-1.40+-purple" alt="playwright" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/npx%20skills-compatible-orange" alt="npx skills" />
</p>

> **Last Tested:** 2026-04-20 | Pinterest DOM: srcset-based feed cards
> **依赖版本:** playwright ≥ 1.40 · aiohttp ≥ 3.9 · Python ≥ 3.8

---

## ✨ 为什么选这个（常见 Pinterest 下载器的痛点对比）

社区里大量 Pinterest 下载器存在如下缺陷 —— 本工具针对性逐项修复：

| 常见痛点 | 其他工具表现 | 本工具 v3.1 |
|----------|-------------|-------------|
| **只下缩略图** | 下载到 236x 小图，清晰度差 | ✅ DOM 阶段读 `srcset` 最大项；下载阶段按 `/originals/ → /1200x/ → /736x/` 顺序尝试 |
| **不处理无限滚动** | 只抓首屏可见的几十张 | ✅ Playwright 自动滚动，stagnant 检测到底停止（默认最多 800 次滚动） |
| **失败不重试 / 403 直接放弃** | 一次超时/403 就放弃 | ✅ 3 次指数退避重试；**403 专项退避**，应对 CDN 临时鉴权拒绝；429/503 限流退避 |
| **串行下载慢** | 500 张要跑 10+ 分钟 | ✅ aiohttp 并发下载（默认 8，可调），500 张约 1-2 分钟 |
| **重跑全量扫描** | 每次都重新滚动全部画板 | ✅ `--resume` 增量模式：复用 `_urls_cache.txt`，只下载 `_manifest.txt` 里尚未记录的新图 |
| **不支持私密画板** | 只能下公开画板 | ✅ `--cookies cookies.txt` 支持 |
| **要求输入账号密码** | 第三方工具常见，极大安全隐患 | ✅ **永不索取密码**，仅支持 cookie |
| **视频完全不下载** | 画板里的 Idea Pin / 视频直接跳过 | ✅ 并发检测 + MP4 直链下载；HLS (m3u8) 导出清单供 ffmpeg |
| **反爬应对不足** | 固定 UA、固定间隔，容易被限 | ✅ UA 轮换、滚动抖动、请求间隔抖动 |
| **CDN 改版即失效** | 依赖易变的 CSS selector | ✅ 用 `a[href*="/pin/"] > img` + srcset，稳定性较好 |
| **版本依赖不明** | 不写 Last Tested，出错无法排查 | ✅ 头部标注 `Last Tested` 和兼容版本范围 |
| **Windows 路径权限崩溃** | 没有任何提示 | ✅ 启动时写入测试，权限失败给出具体排查建议 |

---

## 🚀 安装与使用（保姆级教程）

> 以下教程默认将文件下载到**桌面**。如果你熟悉命令行，可以跳过直接看 [参数详解](#-参数详解)。

### 🍎 macOS 用户

打开**终端**（在「启动台」搜索"终端"或按 `Command + 空格` 搜索 "Terminal"），依次复制粘贴以下命令：

**第 1 步：下载脚本到桌面**
```bash
curl -o ~/Desktop/pinterest_download.py https://raw.githubusercontent.com/ftly-yunshu/pinterest-board-downloader/main/scripts/pinterest_download.py
```

**第 2 步：安装依赖（只需运行一次）**
```bash
pip3 install playwright aiohttp
```

> 如果报 `Permission denied`，改为：
> ```bash
> pip3 install playwright aiohttp --break-system-packages
> ```

**第 3 步：安装浏览器内核（只需运行一次）**
```bash
python3 -m playwright install chromium
```

**第 4 步：开始下载！**
```bash
python3 ~/Desktop/pinterest_download.py "https://www.pinterest.com/用户名/画板名/" --output ~/Desktop/Pinterest下载
```

下载完成后，在桌面找到 `Pinterest下载` 文件夹即可。

---

### 🪟 Windows 用户

按 `Win + R`，输入 `powershell`，回车打开 PowerShell。

**第 1 步：下载脚本到桌面**
```powershell
curl -o "$env:USERPROFILE\Desktop\pinterest_download.py" https://raw.githubusercontent.com/ftly-yunshu/pinterest-board-downloader/main/scripts/pinterest_download.py
```

**第 2 步：安装依赖（只需运行一次）**
```powershell
pip install playwright aiohttp
```

> 如果报 `No Python` 或红字错误，说明还没装 Python → 去 [python.org](https://www.python.org/downloads/) 下载安装，安装时勾选 **"Add Python to PATH"**。
>
> 如果报 `Permission denied`，以**管理员身份**重新打开 PowerShell 再运行。

**第 3 步：安装浏览器内核（只需运行一次）**
```powershell
python -m playwright install chromium
```

**第 4 步：开始下载！**
```powershell
python "%USERPROFILE%\Desktop\pinterest_download.py" "https://www.pinterest.com/用户名/画板名/" --output "%USERPROFILE%\Desktop\Pinterest下载"
```

下载完成后，在桌面找到 `Pinterest下载` 文件夹即可。

---

### 🤖 作为 AI Skill 安装（高级）

如果你使用 WorkBuddy / CodeBuddy / Cline / Cursor 等 AI 工具：

```bash
npx skills add https://github.com/ftly-yunshu/pinterest-board-downloader --skill pinterest-downloader -y
```

安装后直接对 AI 说："帮我下载这个 Pinterest 画板：`https://pinterest.com/xxx/yyy/`"

---

### 💡 更多用法示例

```bash
# 先试 50 张看看效果
python3 pinterest_download.py <URL> --max-pins 50 --output ~/Desktop/测试下载

# 网络不太好的时候，降低并发
python3 pinterest_download.py <URL> --concurrency 3 --scroll-pause 2.5 --output ~/Desktop/Pinterest下载

# 画板更新了新内容，只想下载新增的（增量模式）
python3 pinterest_download.py <URL> --output ~/Desktop/Pinterest下载 --resume

# 查看所有可用参数
python3 pinterest_download.py --help
```

---

## ⚙️ 参数详解

| 参数 | 默认 | 说明 |
|------|------|------|
| `board_url` | — | Pinterest 画板 URL（必填） |
| `--output / -o` | `pinterest_{board}/` | 输出目录 |
| `--concurrency` | `8` | 图片并发下载数 |
| `--retries` | `3` | 每张图片最大重试次数（指数退避，含 403/429/503） |
| `--max-pins` | `0` | 最多处理的 Pin 数量，0 = 不限 |
| `--cookies` | — | 传入 cookies 文件路径（高级用法，参见源码注释） |
| `--name-by` | `seq` | 文件命名：`seq` 纯序号 / `pin` 含 Pin ID |
| `--no-video` | — | 跳过视频检测与下载 |
| `--resume` | — | 增量模式：复用上次缓存跳过重新滚动，只下载新增图片 |
| `--scroll-pause` | `1.5` | 每次滚动后等待秒数 |

---

## 📂 输出结构

```
output_dir/
├── pinterest_0001.jpg            # 或 pin_{pinid}_0001.jpg
├── pinterest_0002.jpg
├── ...
├── videos/
│   └── video_001_{pinid}.mp4     # MP4 视频
├── videos_hls/
│   └── m3u8_list.txt             # HLS 流清单（需 ffmpeg 处理）
├── _urls_cache.txt               # 采集到的 URL（含 pin_id）
├── _pins_cache.txt               # 所有 Pin ID
├── _video_list.txt               # 视频检测结果
└── _manifest.txt                 # 已下载清单（断点续传依据，勿删）
```

---

## 🔒 安全与隐私

- ❌ **永不请求**你的 Pinterest 账号或密码
- ❌ **不发送任何数据**到第三方服务器
- ✅ 所有操作均在**本地**完成（除了必要的 Pinterest CDN 请求）
- ✅ 纯开源单文件，代码完全透明，可自行审计

---

## 🪟 Windows 用户须知

### 没装 Python？

脚本需要 Python 3.8+。如果第 2 步报错 `No Python`：

1. 打开 [python.org/downloads](https://www.python.org/downloads/)
2. 下载最新的 Python 3 安装包
3. 安装时**务必勾选** `Add Python to PATH`
4. 安装完成后重新打开 PowerShell 再试

### 安装报 "Access Denied"？

以**管理员身份**打开 PowerShell：
- 按 `Win` 键，搜索 "PowerShell"
- 右键 → **以管理员身份运行**
- 再执行 `pip install playwright aiohttp`

### 输出路径

脚本默认下载到当前目录。教程中已使用 `--output` 指定到桌面，你也可以改成任意路径：

```powershell
--output "D:\我的素材\Pinterest"
```

---

## 🔬 深度验证（下载质量自检三步）

运行完成后，通过以下步骤验证质量：

**Step 1 · 验证画质（原图 vs 缩略图）**
```bash
# macOS/Linux
ls -lh <output_dir>/pinterest_*.jpg | sort -k5 -rh | head -10
# 正常原图应在 200KB ~ 2MB 之间
# 如果大量文件 < 50KB，说明 CDN 降级，可重跑
```

**Step 2 · 验证数量（对比 Pinterest 网页）**

打开画板网页，标题附近会显示总 Pin 数（如 "825 Pins"）。
对比命令：
```bash
ls <output_dir>/pinterest_*.jpg | wc -l
```
通常能达到 95%+ 覆盖率（Pinterest 实时动态会有误差）。

**Step 3 · 验证增量更新（--resume 工作流）**

画板更新了新内容时，无需重跑全量滚动：
```bash
# 第一次：正常运行（生成缓存）
python3 pinterest_download.py <URL> --output ./out

# 画板新增图片后的第二次：增量模式
python3 pinterest_download.py <URL> --output ./out --resume
# 只会下载 _manifest.txt 里尚未记录的新图，不会重跑 800 次滚动
```

---

## ⚖️ 使用条款与法律声明

请仔细阅读：

- 下载的素材**版权归原作者所有**
- 本工具仅供**个人离线备份、学习研究**使用
- 禁止用于大规模二次传播、商业再分发、模型训练（未经授权）
- 请遵守 [Pinterest Terms of Service](https://policy.pinterest.com/en/terms-of-service) 及所在国家/地区的版权法律
- 作者不对使用本工具产生的任何纠纷负责

---

## 🔧 工作原理

5 阶段流水线：

| 阶段 | 技术 | 作用 |
|------|------|------|
| **1. 滚动收集** | Playwright + Chromium | 自动滚动画板，从 `srcset` 读取高清 URL + 采集 Pin ID |
| **2. 视频检测** | aiohttp 并发 HTTP GET | 对每个 Pin 页面做正则匹配 MP4/m3u8（比浏览器逐个打开快约 100 倍） |
| **3. 图片下载** | aiohttp 并发 + 指数退避 | 按 `/originals/ → /1200x/ → /736x/` 顺序尝试，自动处理 429/503 |
| **4. 视频下载** | urllib + Referer 头 | MP4 直链保存到 `videos/`；HLS 输出清单供 ffmpeg |
| **5. 高清化补救** | URL 尺寸段替换 | 扫描仍 < 15KB 的图片，尝试更大尺寸覆盖 |

---

## 🧪 如何验证下载质量

运行后用这三步自检：

1. **查原图**：随机打开一张 JPG，查分辨率。常见原图应在 1000px 宽以上（具体取决于源图）
2. **查数量**：对比 Pinterest 网页上画板的显示数量（画板头部有计数）
3. **查完整性**：若 `_manifest.txt` 行数 ≈ `_urls_cache.txt` 行数，说明基本无遗漏

---

## 🛠️ 故障排查

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| 收集到 0 张图片 | 画板需登录 / URL 错误 / 网络限制 | 检查 URL 格式；换网络环境重试 |
| HTTP 403 大量出现 | CDN 临时鉴权拒绝 | 脚本已自动退避重试；若持续请稍后再试 |
| HTTP 429 / 503 大量出现 | 并发太激进 | `--concurrency 3 --scroll-pause 3` |
| 图片下载后大量 < 50KB | CDN 返回了缩略图 | 脚本阶段 5 会自动补救；极端情况下该 Pin 的源图本身就小 |
| 视频检测为 0 但画板有视频 | 全是 HLS 流 | 查 `videos_hls/m3u8_list.txt`，用 `ffmpeg -i <URL> -c copy out.mp4` |
| `playwright install` 失败 | 系统 Python 受保护 | macOS: `--break-system-packages`；Windows: 管理员 PowerShell |
| Windows PermissionError | 输出目录权限不足 | `--output "%USERPROFILE%\Desktop\Pinterest下载"` |
| 中断后再跑是否会重复下载 | — | 不会；`_manifest.txt` 会跳过已完成的 URL |
| 画板新增了内容，不想全量重跑 | — | `--resume` 增量模式，只下新图，跳过重新滚动 |

---

## 📁 仓库结构

```
pinterest-board-downloader/
├── skills/
│   └── pinterest-downloader/
│       ├── SKILL.md                 # Skill 定义（供 AI 读取）
│       └── pinterest_download.py    # 核心脚本
├── scripts/
│   └── pinterest_download.py        # 同文件副本（供纯 CLI 用户）
├── README.md                        # 本文件
├── LICENSE                          # MIT
├── requirements.txt                 # Python 依赖
└── .gitignore
```

---

## 🤝 贡献

欢迎 PR 与 issue，特别欢迎：

- 针对 Pinterest DOM 改版的兼容性修复
- 更稳健的 HLS 下载方案（内置 m3u8 合并）
- 其他语言（英语）文档

---

## 📄 License

MIT © [ftly-yunshu](https://github.com/ftly-yunshu) — 自由使用、修改和分发。

---

<p align="center">
  作为 AI Skill 安装：<br>
  <code>npx skills add https://github.com/ftly-yunshu/pinterest-board-downloader --skill pinterest-downloader -y</code>
</p>
