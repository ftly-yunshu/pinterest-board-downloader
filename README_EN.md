<p align="right">
  <a href="./README.md">中文</a> | <a href="./README_EN.md">English</a>
</p>

# 📌 Pinterest Board Downloader

<p align="center">
  <strong>Download all images and videos from a Pinterest board to your local machine</strong><br>
  <sub>HD First · Concurrent Downloads · Video Support · Resume Downloads</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.1.0-blue" alt="version" />
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/npx%20skills-compatible-orange" alt="npx skills" />
</p>

---

## 🚀 Installation & Usage

### 🤖 Option 1: Install as AI Skill (Recommended)

If you use **WorkBuddy / CodeBuddy / Cline / Cursor** or similar AI coding tools:

```bash
npx skills add https://github.com/ftly-yunshu/pinterest-board-downloader --skill pinterest-downloader -y
```

After installation, just tell the AI: "Download this Pinterest board for me: `https://pinterest.com/xxx/yyy/`" — the AI handles everything.

> 💡 No need to install Python or dependencies manually — the AI configures everything.

---

### 🍎 Option 2: macOS Manual Install

Open **Terminal** (`Command + Space`, search "Terminal"), then paste each command:

**Step 1: Download script to Desktop**
```bash
curl -o ~/Desktop/pinterest_download.py https://raw.githubusercontent.com/ftly-yunshu/pinterest-board-downloader/main/scripts/pinterest_download.py
```

**Step 2: Install dependencies (run once)**
```bash
pip3 install playwright aiohttp
```

> If you get `Permission denied`, use: `pip3 install playwright aiohttp --break-system-packages`

**Step 3: Install browser engine (run once)**
```bash
python3 -m playwright install chromium
```

**Step 4: Start downloading!**
```bash
python3 ~/Desktop/pinterest_download.py "https://www.pinterest.com/username/board-name/" --output ~/Desktop/Pinterest
```

Find the downloaded files in the `Pinterest` folder on your Desktop.

---

### 🪟 Option 3: Windows Manual Install

Press `Win + R`, type `powershell`, press Enter.

**Step 1: Download script to Desktop**
```powershell
curl -o "$env:USERPROFILE\Desktop\pinterest_download.py" https://raw.githubusercontent.com/ftly-yunshu/pinterest-board-downloader/main/scripts/pinterest_download.py
```

**Step 2: Install dependencies (run once)**
```powershell
pip install playwright aiohttp
```

> If you get `No Python` → Download from [python.org](https://www.python.org/downloads/), check **"Add Python to PATH"** during install.
>
> If you get `Permission denied` → Reopen PowerShell as **Administrator**.

**Step 3: Install browser engine (run once)**
```powershell
python -m playwright install chromium
```

**Step 4: Start downloading!**
```powershell
python "%USERPROFILE%\Desktop\pinterest_download.py" "https://www.pinterest.com/username/board-name/" --output "%USERPROFILE%\Desktop\Pinterest"
```

Find the downloaded files in the `Pinterest` folder on your Desktop.

---

### 💡 More Examples

```bash
# Try 50 pins first
python3 pinterest_download.py <URL> --max-pins 50 --output ~/Desktop/Pinterest

# Slow network? Reduce concurrency
python3 pinterest_download.py <URL> --concurrency 3 --scroll-pause 2.5 --output ~/Desktop/Pinterest

# Board updated? Download only new content (incremental mode)
python3 pinterest_download.py <URL> --output ~/Desktop/Pinterest --resume

# View all options
python3 pinterest_download.py --help
```

---

## ✨ Features

| Common Pain Point | This Tool |
|-------------------|-----------|
| Only downloads blurry thumbnails | ✅ Automatically fetches HD originals |
| Only scrapes the first visible page | ✅ Auto-scrolls to load and download everything |
| Videos are skipped entirely | ✅ Downloads both images and videos (MP4) |
| Slow downloads, 500 pins takes forever | ✅ Concurrent downloads, 5-10x faster |
| Must re-download everything on updates | ✅ Incremental mode, only downloads new content |

---

## ⚙️ Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `board_url` | — | Pinterest board URL (required) |
| `--output / -o` | `pinterest_{board}/` | Output directory |
| `--concurrency` | `8` | Concurrent download count |
| `--retries` | `3` | Max retries per image |
| `--max-pins` | `0` | Max pins to process, 0 = unlimited |
| `--cookies` | — | Path to cookies file (advanced, see source comments) |
| `--name-by` | `seq` | Naming: `seq` sequential / `pin` with Pin ID |
| `--no-video` | — | Skip video detection and download |
| `--resume` | — | Incremental mode: only download new images |
| `--scroll-pause` | `1.5` | Seconds to wait after each scroll |

---

## 🔒 Security & Privacy

- ❌ **Never asks** for your Pinterest credentials
- ❌ **Doesn't send** any data to third-party servers
- ✅ All operations run **locally**
- ✅ Open-source single file, fully auditable code

---

## 🛠️ Troubleshooting

| Symptom | Solution |
|---------|----------|
| 0 images collected | Check URL format; try a different network |
| Frequent HTTP 403 errors | Auto-retries are built in; wait and retry if persistent |
| Downloaded images are blurry | Auto upscaling is attempted; source may be low-res |
| Videos detected as 0 but board has videos | Check `videos_hls/m3u8_list.txt`, use ffmpeg |
| `playwright install` fails | macOS: add `--break-system-packages`; Windows: use Admin PowerShell |
| Windows PermissionError | Use `--output "%USERPROFILE%\Desktop\Pinterest"` |

---

## ⚖️ Terms of Use

- Downloaded content **belongs to the original creators**
- This tool is for **personal offline backup and study** only
- Do not redistribute commercially or use for unauthorized model training
- Please comply with [Pinterest Terms of Service](https://policy.pinterest.com/en/terms-of-service) and local copyright laws

---

## 📄 License

MIT © [ftly-yunshu](https://github.com/ftly-yunshu) — Free to use, modify, and distribute.

---

<p align="center">
  ⭐ If you find this useful, please Star!<br>
  <sub>Bug reports? <a href="https://github.com/ftly-yunshu/pinterest-board-downloader/issues">Open an Issue</a></sub>
</p>
