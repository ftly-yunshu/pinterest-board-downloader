<p align="right">
  <a href="./README.md">中文</a> | <a href="./README_EN.md">English</a>
</p>

# 📌 Pinterest Board Downloader

<p align="center">
  <strong>一键下载 Pinterest 画板中的全部图片和视频到本地</strong><br>
  <sub>原图优先 · 并发下载 · 视频支持 · 断点续传</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.1.0-blue" alt="version" />
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/npx%20skills-compatible-orange" alt="npx skills" />
</p>

---

## 🚀 安装与使用

### 🤖 方式一：作为 AI Skill 安装（推荐）

如果你使用 **WorkBuddy / CodeBuddy / Cline / Cursor** 等 AI 编程工具：

```bash
npx skills add https://github.com/ftly-yunshu/pinterest-board-downloader --skill pinterest-downloader -y
```

安装后直接对 AI 说："帮我下载这个 Pinterest 画板：`https://pinterest.com/xxx/yyy/`"，AI 会自动处理一切。

> 💡 AI Skill 方式**不需要手动安装 Python 和依赖**，AI 会自动配置环境。

---

### 🍎 方式二：macOS 手动安装

打开**终端**（`Command + 空格` 搜索 "Terminal"），依次粘贴：

**第 1 步：下载脚本到桌面**
```bash
curl -o ~/Desktop/pinterest_download.py https://raw.githubusercontent.com/ftly-yunshu/pinterest-board-downloader/main/scripts/pinterest_download.py
```

**第 2 步：安装依赖（只需运行一次）**
```bash
pip3 install playwright aiohttp
```

> 如果报 `Permission denied`，改为：`pip3 install playwright aiohttp --break-system-packages`

**第 3 步：开始下载！**
```bash
python3 ~/Desktop/pinterest_download.py "https://www.pinterest.com/用户名/画板名/" --output ~/Desktop/Pinterest下载
```

下载完成后，在桌面找到 `Pinterest下载` 文件夹即可。

> 💡 脚本会自动使用系统已安装的 Chrome / Edge 浏览器，**无需额外安装浏览器内核**。

---

### 🪟 方式三：Windows 手动安装

按 `Win + R`，输入 `powershell`，回车打开 PowerShell。

**第 1 步：下载脚本到桌面**
```powershell
curl -o "$env:USERPROFILE\Desktop\pinterest_download.py" https://raw.githubusercontent.com/ftly-yunshu/pinterest-board-downloader/main/scripts/pinterest_download.py
```

**第 2 步：安装依赖（只需运行一次）**
```powershell
pip install playwright aiohttp
```

> 如果报 `No Python` → 去 [python.org](https://www.python.org/downloads/) 下载安装，安装时勾选 **"Add Python to PATH"**。
>
> 如果报 `Permission denied` → 以**管理员身份**重新打开 PowerShell 再运行。

**第 3 步：开始下载！**
```powershell
python "%USERPROFILE%\Desktop\pinterest_download.py" "https://www.pinterest.com/用户名/画板名/" --output "%USERPROFILE%\Desktop\Pinterest下载"
```

下载完成后，在桌面找到 `Pinterest下载` 文件夹即可。

> 💡 Windows 10/11 自带 Edge 浏览器，脚本会自动使用，**无需额外安装浏览器内核**。

---

### 💡 更多用法

```bash
# 先试 50 张看看效果
python3 pinterest_download.py <URL> --max-pins 50 --output ~/Desktop/测试下载

# 网络不好时，降低并发
python3 pinterest_download.py <URL> --concurrency 3 --scroll-pause 2.5 --output ~/Desktop/Pinterest下载

# 画板更新了，只下载新增内容（增量模式）
python3 pinterest_download.py <URL> --output ~/Desktop/Pinterest下载 --resume

# 查看所有参数
python3 pinterest_download.py --help
```

---

## ✨ 功能亮点

| 常见痛点 | 本工具 |
|----------|--------|
| 只能下载模糊的缩略图 | ✅ 自动获取高清原图 |
| 只能抓取首页可见的几张 | ✅ 自动滚动加载，下载全部内容 |
| 视频直接跳过 | ✅ 同时下载图片和视频（MP4） |
| 下载慢，500 张要等很久 | ✅ 并发下载，速度快 5-10 倍 |
| 画板更新后需要重新全部下载 | ✅ 增量模式，只下载新增内容 |

---

## ⚙️ 参数详解

| 参数 | 默认 | 说明 |
|------|------|------|
| `board_url` | — | Pinterest 画板 URL（必填） |
| `--output / -o` | `pinterest_{board}/` | 输出目录 |
| `--concurrency` | `8` | 图片并发下载数 |
| `--retries` | `3` | 每张图片最大重试次数 |
| `--max-pins` | `0` | 最多处理的 Pin 数量，0 = 不限 |
| `--cookies` | — | 传入 cookies 文件路径（高级用法，参见源码注释） |
| `--name-by` | `seq` | 文件命名：`seq` 纯序号 / `pin` 含 Pin ID |
| `--no-video` | — | 跳过视频检测与下载 |
| `--resume` | — | 增量模式：只下载新增图片 |
| `--scroll-pause` | `1.5` | 每次滚动后等待秒数 |

---

## 🔒 安全与隐私

- ❌ **永不请求**你的 Pinterest 账号或密码
- ❌ **不发送任何数据**到第三方服务器
- ✅ 所有操作均在**本地**完成
- ✅ 纯开源单文件，代码完全透明

---

## 🛠️ 故障排查

| 症状 | 解决方案 |
|------|---------|
| 收集到 0 张图片 | 检查 URL 格式；换网络环境重试 |
| HTTP 403 大量出现 | 脚本已自动退避重试；若持续请稍后再试 |
| 图片下载后大量很模糊 | 脚本会自动尝试高清补救；极端情况源图本身就小 |
| 视频检测为 0 但画板有视频 | 查 `videos_hls/m3u8_list.txt`，用 ffmpeg 下载 |
| `playwright install` 失败 | 脚本已自动使用系统浏览器，一般不需要此步骤 |
| Windows PermissionError | `--output "%USERPROFILE%\Desktop\Pinterest下载"` |

---

## ⚖️ 使用条款

- 下载的素材**版权归原作者所有**
- 本工具仅供**个人离线备份、学习研究**使用
- 禁止用于大规模二次传播、商业再分发、模型训练（未经授权）
- 请遵守 [Pinterest Terms of Service](https://policy.pinterest.com/en/terms-of-service) 及当地版权法律

---

## 📄 License

MIT © [ftly-yunshu](https://github.com/ftly-yunshu) — 自由使用、修改和分发。

---

<p align="center">
  ⭐ 如果觉得好用，欢迎 Star！<br>
  <sub>问题反馈请提 <a href="https://github.com/ftly-yunshu/pinterest-board-downloader/issues">Issue</a></sub>
</p>
