#!/usr/bin/env python3
"""
================================================================================
   Pinterest Board Downloader - Standalone Edition (v3.1)
================================================================================

一个独立的、零框架依赖的 Pinterest 画板批量下载工具。

兼容：Python 3.8+ | macOS / Linux / Windows
适用：任何 AI 工具（ChatGPT / Claude / Gemini / Copilot / Cursor 等）

Last Tested: 2026-04-20
Tested With: Python 3.9 / 3.11 / 3.12 | playwright 1.44+ | aiohttp 3.9+
Pinterest DOM Version: Infinite-scroll v2 (srcset-based feed cards)

--------------------------------------------------------------------------------
用法（简单）：
    python3 pinterest_download.py <画板URL>
    python3 pinterest_download.py <画板URL> <输出目录>

用法（完整）：
    python3 pinterest_download.py <URL> \\
        --output ./my_images \\
        --concurrency 8 \\
        --max-pins 500 \\
        --cookies cookies.txt \\
        --name-by pin \\
        --no-video

依赖安装（仅需一次）：
    pip install playwright aiohttp
    playwright install chromium

安全与隐私：
  本工具不会请求、存储或发送你的 Pinterest 账号密码。
  访问私密画板请使用浏览器导出的 cookies.txt（Netscape 格式），通过 --cookies 传入。

法律：
  请只下载你拥有或有权使用的内容。下载的素材版权归原作者所有，
  请遵守 Pinterest ToS 及目标国家/地区的版权法律，仅用于个人离线备份或学习。
--------------------------------------------------------------------------------
"""

import argparse
import asyncio
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from http.cookiejar import MozillaCookieJar
from pathlib import Path

__version__ = "3.1.0"
LAST_TESTED = "2026-04-20"  # Pinterest DOM: srcset-based feed cards

# ================================================================
# 默认参数（可通过 CLI 覆盖）
# ================================================================

DEFAULTS = {
    "scroll_pause": 1.5,           # 每次滚动后等待秒数
    "max_scrolls": 800,            # 最大滚动次数上限（保护）
    "stagnant_limit": 6,           # 连续 N 次无新内容则停止滚动
    "image_concurrency": 8,        # 图片并发下载数（保守：避免被封）
    "image_timeout": 30,           # 单次图片下载超时
    "image_retries": 3,            # 图片失败重试次数（指数退避）
    "video_concurrency": 20,       # 视频检测并发数（纯读 HTML）
    "video_http_timeout": 10,      # 视频 pin 页面请求超时
    "hq_rescue_threshold": 15 * 1024,  # 下载完成后小于此值的文件做"补救升级"
    "min_valid_bytes": 512,        # 小于此字节数的响应视为无效
}

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# Pinterest CDN 尺寸段（从大到小）；/originals/ 通常是最大，但不是所有图都有
CDN_SIZE_SEGMENTS = ["/originals/", "/1200x/", "/736x/", "/564x/", "/474x/", "/236x/"]


def log(msg: str) -> None:
    """带时间戳的日志"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def pick_ua() -> str:
    return random.choice(USER_AGENTS)


# ================================================================
# Cookie 工具 —— 支持 Netscape 格式（浏览器扩展常见导出格式）
# ================================================================

def load_cookies(cookies_path: str):
    """
    读取 Netscape 格式 cookies.txt，返回 (jar, dict_for_playwright_context)。
    失败时返回 (None, None)，不中断流程。
    """
    if not cookies_path or not os.path.exists(cookies_path):
        return None, None
    try:
        jar = MozillaCookieJar(cookies_path)
        jar.load(ignore_discard=True, ignore_expires=True)
        pw_cookies = []
        for c in jar:
            if "pinterest" not in (c.domain or "").lower():
                continue
            pw_cookies.append({
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path or "/",
                "secure": bool(c.secure),
                "httpOnly": False,
                "sameSite": "Lax",
            })
        log(f"🔐 已加载 {len(pw_cookies)} 条 Pinterest cookies")
        return jar, pw_cookies
    except Exception as e:
        log(f"⚠️ 加载 cookies 失败: {e}，将以匿名模式继续")
        return None, None


def cookie_header_from_jar(jar) -> str:
    if not jar:
        return ""
    parts = []
    for c in jar:
        if "pinterest" in (c.domain or "").lower():
            parts.append(f"{c.name}={c.value}")
    return "; ".join(parts)


# ================================================================
# Phase 1 — 滚动收集（Playwright）
# ================================================================

async def collect_board_data(board_url: str, output_dir: str, cfg: dict,
                             resume: bool = False):
    """
    用 Playwright 打开画板，自动滚动收集：
      - 原始高清 image URL（优先读 srcset 里最大的那张）
      - Pin ID（用于后续视频检测与命名）

    resume=True：若本地已有 _urls_cache.txt + _pins_cache.txt，
                  直接加载缓存跳过重新滚动（增量模式）。
    """
    # ---- 增量模式：直接读缓存，不重新滚动 ----
    urls_cache = os.path.join(output_dir, "_urls_cache.txt")
    pins_cache = os.path.join(output_dir, "_pins_cache.txt")
    if resume and os.path.exists(urls_cache) and os.path.exists(pins_cache):
        log("⏩ --resume 模式：读取本地缓存，跳过滚动阶段")
        image_records = []
        with open(urls_cache) as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    pid, url, og = parts[0], parts[1], parts[2]
                    image_records.append((pid if pid != "-" else None, url, og))
                elif len(parts) == 1 and parts[0]:
                    # 兼容旧版单列格式
                    image_records.append((None, parts[0], parts[0]))
        pin_ids = []
        with open(pins_cache) as f:
            pin_ids = [l.strip() for l in f if l.strip()]
        log(f"✅ 从缓存恢复: {len(image_records)} 张图片, {len(pin_ids)} 个 Pin")
        return image_records, pin_ids
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log("❌ 缺少依赖: pip install playwright && playwright install chromium")
        sys.exit(1)

    image_records = []  # [(pin_id_or_none, original_url), ...] 保留顺序与出现关系
    seen_urls = set()
    pin_ids = []
    seen_pins = set()

    log("启动浏览器 ...")
    p = await async_playwright().start()
    # 优先使用系统浏览器，无需额外安装 Chromium
    import shutil, platform
    channel = None
    if platform.system() == "Darwin":
        mac_chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(mac_chrome):
            channel = "chrome"
    elif platform.system() == "Windows":
        edge_paths = [
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        ]
        chrome_paths = [
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        ]
        for ep in edge_paths:
            if os.path.exists(ep):
                channel = "msedge"
                break
        if not channel:
            for cp in chrome_paths:
                if os.path.exists(cp):
                    channel = "chrome"
                    break
    else:
        if shutil.which("google-chrome"):
            channel = "chrome"
        elif shutil.which("microsoft-edge"):
            channel = "msedge"

    browser = None
    if channel:
        try:
            log(f"  ✓ 检测到系统浏览器（{channel}），直接使用")
            browser = await p.chromium.launch(
                headless=True, channel=channel,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                      "--disable-blink-features=AutomationControlled"],
            )
        except Exception as e:
            log(f"  ⚠ 系统 {channel} 启动失败（{e}），回退到 Playwright Chromium")

    if browser is None:
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                      "--disable-blink-features=AutomationControlled"],
            )
        except Exception as e:
            log("  ✗ 未检测到系统浏览器，Playwright Chromium 也未安装")
            log("  💡 请先安装 Google Chrome 或运行以下命令：")
            log("     python3 -m playwright install chromium")
            await p.stop()
            raise SystemExit(1)
    ctx = await browser.new_context(
        user_agent=pick_ua(),
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )

    # 注入 cookies（私密画板）
    _, pw_cookies = cfg["_pw_cookies"], cfg["_pw_cookies"]
    if pw_cookies:
        try:
            await ctx.add_cookies(pw_cookies)
        except Exception as e:
            log(f"⚠️ 注入 cookies 失败: {e}")

    page = await ctx.new_page()
    page.set_default_timeout(60000)

    try:
        log(f"正在打开: {board_url}")
        resp = await page.goto(board_url, wait_until="domcontentloaded", timeout=30000)
        if resp and resp.status >= 400:
            log(f"⚠️ 页面返回状态码 {resp.status}；如是 403/404 请检查画板链接或登录态")

        # 等待 network 相对稳定 + 一些内容渲染
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        await asyncio.sleep(2)

        stagnant = 0
        prev_total = 0

        # JS：一次性返回图片（pin_id + 最高分辨率 url） + 所有 pin_id
        js_extract = r"""
        () => {
            // 把 /XXXx/ 段升级成 /originals/（去重用）
            const toOriginal = (u) => {
                if (!u) return u;
                // 匹配各种 CDN 尺寸路径：/236x/, /736x/, /originals/ 等
                // 也处理带 /r/.../ 前缀的情况
                const m = u.match(/(\/\d+x\/|\/originals\/)/);
                if (!m) return u;
                return u.replace(m[1], '/originals/');
            };

            // 纯文件名去重 key：只保留最后一个 / 之后的内容
            const fileKey = (u) => {
                if (!u) return u;
                return u.split('?')[0].split('/').filter(Boolean).slice(-1)[0] || u;
            };

            const imgs = [];
            const seenU = new Set();    // by originalGuess
            const seenF = new Set();    // by filename (兜底)

            // 1) 遍历所有 <a href="/pin/xxx/"> 这类卡片，从卡片内部找 <img>
            document.querySelectorAll('a[href*="/pin/"]').forEach(a => {
                const pinMatch = a.href.match(/\/pin\/(\d+)/);
                const pid = pinMatch ? pinMatch[1] : null;
                const imgEl = a.querySelector('img');
                if (!imgEl) return;

                // 优先 srcset 最高分辨率
                let best = null;
                const srcset = imgEl.srcset || imgEl.getAttribute('srcset') || '';
                if (srcset) {
                    // srcset: "url1 1x, url2 2x" 或 "url1 236w, url2 474w"
                    const parts = srcset.split(',').map(s => s.trim()).filter(Boolean);
                    let maxW = 0;
                    for (const p of parts) {
                        const [u, d] = p.split(/\s+/);
                        if (!u) continue;
                        const w = d ? parseFloat(d) : 0;
                        if (w >= maxW) { maxW = w; best = u; }
                    }
                }
                if (!best) best = imgEl.src || imgEl.getAttribute('data-src') || '';
                if (!best || !best.startsWith('http')) return;
                if (!/pinimg\.com/.test(best)) return;

                best = best.split('?')[0];
                const originalGuess = toOriginal(best);
                if (seenU.has(originalGuess)) return;
                // 双重去重：文件名也检查，防止不同 CDN 路径同一文件
                const fk = fileKey(best);
                if (seenF.has(fk)) return;
                seenU.add(originalGuess);
                seenF.add(fk);

                imgs.push({ pin: pid, url: best, orig_guess: originalGuess });
            });

            // 2) 兜底：画板首屏 background-image 样式
            document.querySelectorAll('[style*="background-image"]').forEach(el => {
                const style = el.getAttribute('style') || '';
                const m = style.match(/url\(["']?([^"')]+)["']?\)/);
                if (!m) return;
                const u = m[1];
                if (!u.startsWith('http') || !/pinimg\.com/.test(u)) return;
                const clean = u.split('?')[0];
                const og = toOriginal(clean);
                if (seenU.has(og)) return;
                const fk = fileKey(clean);
                if (seenF.has(fk)) return;
                seenU.add(og);
                seenF.add(fk);
                imgs.push({ pin: null, url: clean, orig_guess: og });
            });

            // 3) 所有 pin 链接（包括可能没有可见 <img> 的）
            const pins = new Set();
            document.querySelectorAll('a[href*="/pin/"]').forEach(a => {
                const m = a.href.match(/\/pin\/(\d+)/);
                if (m) pins.add(m[1]);
            });

            return { imgs: imgs, pins: [...pins] };
        }
        """

        for scroll_i in range(1, cfg["max_scrolls"] + 1):
            data = await page.evaluate(js_extract)
            new_imgs = 0
            for item in data.get("imgs", []):
                og = item["orig_guess"]
                if og in seen_urls:
                    continue
                seen_urls.add(og)
                image_records.append((item.get("pin"), item.get("url"), og))
                new_imgs += 1

            for pid in data.get("pins", []):
                if pid not in seen_pins:
                    seen_pins.add(pid)
                    pin_ids.append(pid)

            total = len(image_records)
            if scroll_i % 10 == 0 or new_imgs > 5:
                log(f"  滚动 #{scroll_i}: 图片 {total} (+{new_imgs}), Pin {len(pin_ids)}")

            if total == prev_total:
                stagnant += 1
                if stagnant >= cfg["stagnant_limit"]:
                    log(f"  连续 {cfg['stagnant_limit']} 次无新内容，视为到达底部")
                    break
            else:
                stagnant = 0
            prev_total = total

            # 智能 Pin 数量上限检测
            # 如果图片数远超 Pin 数，说明 Pinterest 注入了推荐内容，提前停止
            if len(pin_ids) > 0 and total > len(pin_ids) * 1.3:
                log(f"  ⚠️ 图片数({total})明显超过 Pin 数({len(pin_ids)})，")
                log(f"     可能进入了 Pinterest 推荐区域，提前停止滚动")
                break

            # 随机抖动滚动节奏
            await page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
            await asyncio.sleep(cfg["scroll_pause"] + random.uniform(0.0, 0.6))

        # 写缓存，便于排查
        _save_cache(os.path.join(output_dir, "_urls_cache.txt"),
                    [f"{pid or '-'}\t{u}\t{og}" for pid, u, og in image_records])
        _save_cache(os.path.join(output_dir, "_pins_cache.txt"), pin_ids)

        log(f"✅ 收集完成: {len(image_records)} 张图片, {len(pin_ids)} 个 Pin")
    finally:
        await browser.close()
        await p.stop()

    return image_records, pin_ids


# ================================================================
# Phase 2 — 并发检测视频 Pin
# ================================================================

async def detect_video_pins(pin_ids, output_dir: str, cfg: dict):
    try:
        import aiohttp
    except ImportError:
        log("⚠️ 缺少 aiohttp，跳过视频检测。pip install aiohttp")
        return []

    if not pin_ids:
        return []

    log(f"并发检测 {len(pin_ids)} 个 Pin 是否含视频（并发 {cfg['video_concurrency']}）...")

    video_results = []
    checked = 0
    sem = asyncio.Semaphore(cfg["video_concurrency"])
    cookie_header = cfg.get("_cookie_header", "")

    async def check_one(session, pin_id: str):
        nonlocal checked
        async with sem:
            url = f"https://www.pinterest.com/pin/{pin_id}/"
            headers = {
                "User-Agent": pick_ua(),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
            if cookie_header:
                headers["Cookie"] = cookie_header
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=cfg["video_http_timeout"]),
                    headers=headers,
                ) as resp:
                    if resp.status != 200:
                        return None
                    html = await resp.text()
                    # 先 MP4 直链
                    mp4 = re.search(r'https?://[^\s"\'><]+\.mp4', html)
                    if mp4:
                        return (pin_id, mp4.group(0), "mp4")
                    # HLS
                    m3u8 = re.search(r'https?://[^\s"\'><]+\.m3u8', html)
                    if m3u8:
                        return (pin_id, m3u8.group(0), "m3u8")
                    return None
            except Exception:
                return None
            finally:
                checked += 1
                if checked % 100 == 0 or checked == len(pin_ids):
                    log(f"  已检查 {checked}/{len(pin_ids)}，发现视频 {len(video_results)}")

    connector = aiohttp.TCPConnector(limit=cfg["video_concurrency"] + 5)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_one(session, pid) for pid in pin_ids]
        raw = await asyncio.gather(*tasks, return_exceptions=True)

    for r in raw:
        if isinstance(r, tuple):
            video_results.append(r)

    vid_cache = os.path.join(output_dir, "_video_list.txt")
    with open(vid_cache, "w") as f:
        for pid, vurl, vtype in video_results:
            f.write(f"{pid}\t{vtype}\t{vurl}\n")

    log(f"✅ 视频检测完成: {len(video_results)} 个")
    mp4_cnt = sum(1 for _, _, t in video_results if t == "mp4")
    hls_cnt = sum(1 for _, _, t in video_results if t == "m3u8")
    if hls_cnt:
        log(f"  其中 MP4 直链: {mp4_cnt}, HLS(m3u8): {hls_cnt}（HLS 需 ffmpeg 处理，见 README）")
    return video_results


# ================================================================
# Phase 3 — 并发下载图片（先试原图，失败再降级）
# ================================================================

def _build_variant_urls(original_url: str):
    """
    基于 URL 中的尺寸段，按"原图优先"的顺序生成候选。
    保证：首个候选是 /originals/（如果能构造出来）。
    """
    variants = []
    seen = set()

    def _push(u):
        if u and u not in seen:
            seen.add(u)
            variants.append(u)

    # 找到 URL 里的尺寸段
    seg_found = None
    for seg in CDN_SIZE_SEGMENTS:
        if seg in original_url:
            seg_found = seg
            break

    if seg_found:
        # 按 CDN_SIZE_SEGMENTS 的顺序生成候选（大 -> 小）
        for seg in CDN_SIZE_SEGMENTS:
            _push(original_url.replace(seg_found, seg))
    _push(original_url)
    return variants


async def download_images_async(image_records, output_dir: str, cfg: dict, name_by: str):
    """
    并发下载所有图片。每个 URL：
      1. 生成候选列表（原图优先）
      2. 对每个候选执行 `image_retries` 次指数退避重试
      3. 记录成功/失败
    """
    try:
        import aiohttp
    except ImportError:
        log("❌ 需要 aiohttp: pip install aiohttp")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    sem = asyncio.Semaphore(cfg["image_concurrency"])
    cookie_header = cfg.get("_cookie_header", "")

    # 已下载清单（持久化去重）
    manifest_path = os.path.join(output_dir, "_manifest.txt")
    done_keys = set()
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            for line in f:
                k = line.strip().split("\t")[0]
                if k:
                    done_keys.add(k)

    log(f"开始下载 {len(image_records)} 张图片（并发 {cfg['image_concurrency']}，每张最多重试 {cfg['image_retries']} 次）")

    success = 0
    fail = 0
    skipped = 0
    lock = asyncio.Lock()

    async def download_one(session, idx: int, pin_id, original_url: str, orig_guess: str):
        nonlocal success, fail, skipped

        # 使用 orig_guess 作为去重 key（最稳定的表示）
        key = orig_guess
        if key in done_keys:
            async with lock:
                skipped += 1
            return

        ext = _guess_ext(original_url)
        if name_by == "pin" and pin_id:
            filename = f"pin_{pin_id}_{idx:04d}{ext}"
        else:
            filename = f"pinterest_{idx:04d}{ext}"
        save_path = os.path.join(output_dir, filename)

        # 磁盘存在 + 大于最小阈值 => 视为已完成
        if os.path.exists(save_path) and os.path.getsize(save_path) > cfg["min_valid_bytes"]:
            async with lock:
                done_keys.add(key)
                with open(manifest_path, "a") as f:
                    f.write(f"{key}\t{filename}\t{os.path.getsize(save_path)}\n")
                skipped += 1
            return

        candidates = _build_variant_urls(original_url)
        # 额外尝试 orig_guess（若与首个候选不同）
        if orig_guess not in candidates:
            candidates.insert(0, orig_guess)

        best_ok = False
        last_err = ""

        async with sem:
            for var_url in candidates:
                for attempt in range(cfg["image_retries"]):
                    headers = {
                        "User-Agent": pick_ua(),
                        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
                        "Referer": "https://www.pinterest.com/",
                    }
                    if cookie_header:
                        headers["Cookie"] = cookie_header
                    try:
                        async with session.get(
                            var_url,
                            timeout=aiohttp.ClientTimeout(total=cfg["image_timeout"]),
                            headers=headers,
                        ) as resp:
                            if resp.status == 404:
                                break  # 这个尺寸不存在，换下一个
                            if resp.status >= 400:
                                last_err = f"HTTP {resp.status}"
                                if resp.status in (429, 503):
                                    # 限流：指数退避后重试
                                    await asyncio.sleep(2 ** attempt + random.uniform(0, 1.0))
                                    continue
                                if resp.status == 403:
                                    # 403 可能是临时的 CDN 鉴权问题，退避后最多再试一次
                                    if attempt < cfg["image_retries"] - 1:
                                        await asyncio.sleep(1.5 ** attempt + random.uniform(0, 0.5))
                                        continue
                                # 其他 4xx（400/401/410 等）：当前尺寸无效，换下一个
                                break
                            data = await resp.read()
                            if len(data) < cfg["min_valid_bytes"]:
                                last_err = f"too small ({len(data)}B)"
                                break
                            # 写盘
                            with open(save_path, "wb") as f:
                                f.write(data)
                            best_ok = True
                            async with lock:
                                done_keys.add(key)
                                with open(manifest_path, "a") as mf:
                                    mf.write(f"{key}\t{filename}\t{len(data)}\n")
                                success_local = None
                            break
                    except asyncio.TimeoutError:
                        last_err = "timeout"
                    except Exception as e:
                        last_err = str(e)[:80]
                    # 重试前退避
                    await asyncio.sleep(0.5 * (2 ** attempt) + random.uniform(0, 0.3))
                if best_ok:
                    break

        async with lock:
            if best_ok:
                success += 1
                if success <= 3 or success % 50 == 0:
                    sz = os.path.getsize(save_path)
                    log(f"  ✓ [{idx}] {filename} ({sz//1024}KB)")
            else:
                fail += 1
                log(f"  ✗ [{idx}] {original_url[:70]} - {last_err}")
        # 礼貌延迟（抖动）
        await asyncio.sleep(random.uniform(0.05, 0.2))

    connector = aiohttp.TCPConnector(limit=cfg["image_concurrency"] + 5,
                                     ssl=False)  # Pinterest CDN 有时证书链奇怪
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            download_one(session, idx, pid, url, og)
            for idx, (pid, url, og) in enumerate(image_records, 1)
        ]
        await asyncio.gather(*tasks)

    log(f"\n图片结果: ✓{success} ✗{fail} ⊘{skipped}")
    return success, fail


# ================================================================
# Phase 4 — 下载视频（MP4 直链）
# ================================================================

def download_videos(video_results, output_dir: str, cfg: dict):
    videos_dir = os.path.join(output_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)

    hls_dir = os.path.join(output_dir, "videos_hls")

    success = 0
    fail = 0
    hls_pending = 0

    for idx, (pin_id, video_url, video_type) in enumerate(video_results, 1):
        if video_type == "m3u8":
            # 不直接下 HLS（需要 ffmpeg）；但记录到文件供后续处理
            os.makedirs(hls_dir, exist_ok=True)
            with open(os.path.join(hls_dir, "m3u8_list.txt"), "a") as f:
                f.write(f"{pin_id}\t{video_url}\n")
            hls_pending += 1
            continue

        filename = f"video_{idx:03d}_{pin_id}.mp4"
        save_path = os.path.join(videos_dir, filename)
        if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
            log(f"  ⊘ [{idx}] 已存在: {filename}")
            success += 1
            continue

        ok = _sync_download(
            video_url, save_path,
            extra_headers={"Referer": "https://www.pinterest.com/",
                           "Accept": "video/mp4,*/*"},
            timeout=120, retries=3,
            cookie_header=cfg.get("_cookie_header", ""),
        )
        if ok:
            log(f"  ✓ [{idx}] {filename} ({os.path.getsize(save_path)//1024}KB)")
            success += 1
        else:
            log(f"  ✗ [{idx}] 视频: {video_url[:60]}")
            fail += 1
        time.sleep(random.uniform(0.3, 0.7))

    log(f"\n视频结果: ✓{success} ✗{fail}")
    if hls_pending:
        log(f"  HLS(m3u8) 待处理: {hls_pending} 个；清单：{hls_dir}/m3u8_list.txt")
        log(f"  处理示例: ffmpeg -i <m3u8_url> -c copy out.mp4")
    return success, fail


# ================================================================
# Phase 5 — 补救式高清化（给没走到 /originals/ 的漏网之鱼）
# ================================================================

def upgrade_small_images(output_dir: str, cfg: dict):
    cache_file = os.path.join(output_dir, "_urls_cache.txt")
    if not os.path.exists(cache_file):
        return 0
    urls = []
    with open(cache_file) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                urls.append(parts[1])

    small_files = []
    for fname in sorted(os.listdir(output_dir)):
        if not (fname.startswith("pinterest_") or fname.startswith("pin_")):
            continue
        fpath = os.path.join(output_dir, fname)
        if not os.path.isfile(fpath) or os.path.getsize(fpath) >= cfg["hq_rescue_threshold"]:
            continue
        # 解析序号：取文件名里的最后一组 4 位数字
        m = re.search(r"(\d{4})(?=\.[a-zA-Z]+$)", fname)
        if not m:
            continue
        try:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(urls):
                small_files.append((fname, fpath, urls[idx]))
        except ValueError:
            pass

    if not small_files:
        return 0

    log(f"发现 {len(small_files)} 张可能为缩略图，尝试补救式高清化...")
    upgraded = 0
    for fname, fpath, url in small_files:
        cur_sz = os.path.getsize(fpath)
        best = None
        best_sz = cur_sz
        for v in _build_variant_urls(url)[:5]:
            try:
                req = urllib.request.Request(v, headers={
                    "User-Agent": pick_ua(),
                    "Referer": "https://www.pinterest.com/",
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                    if data and len(data) > best_sz * 1.15:
                        best = data
                        best_sz = len(data)
            except Exception:
                continue
        if best:
            with open(fpath, "wb") as f:
                f.write(best)
            upgraded += 1
            if upgraded <= 10 or upgraded % 20 == 0:
                log(f"  ↑ {fname}: {cur_sz//1024}KB → {best_sz//1024}KB")
    log(f"高清化补救: {upgraded}/{len(small_files)} 张已升级")
    return upgraded


# ================================================================
# 内部工具
# ================================================================

def _save_cache(filepath: str, lines):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w") as f:
        for item in lines:
            f.write(str(item) + "\n")


def _guess_ext(url: str) -> str:
    lower = url.lower().split("?")[0]
    for ext in (".png", ".gif", ".webp", ".jpg", ".jpeg"):
        if lower.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def _sync_download(url: str, save_path: str, extra_headers=None,
                   timeout=30, retries=1, cookie_header: str = "") -> bool:
    headers = {"User-Agent": pick_ua(), "Accept": "*/*"}
    if extra_headers:
        headers.update(extra_headers)
    if cookie_header:
        headers["Cookie"] = cookie_header
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if len(data) >= 512:
                    with open(save_path, "wb") as f:
                        f.write(data)
                    return True
            return False
        except Exception:
            if attempt < retries - 1:
                time.sleep(1.5 * (2 ** attempt) + random.uniform(0, 0.5))
    return False


# ================================================================
# CLI 入口
# ================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Pinterest Board Downloader v3.0 —— 一键下载画板图片+视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 pinterest_download.py https://www.pinterest.com/user/board/
  python3 pinterest_download.py https://www.pinterest.com/user/board/ --output ./out --concurrency 10
  python3 pinterest_download.py https://www.pinterest.com/user/board/ --cookies cookies.txt --name-by pin

环境变量兼容：
  若只提供两个位置参数 (URL  OUTPUT_DIR)，将沿用旧版行为。
        """,
    )
    parser.add_argument("board_url", help="Pinterest 画板 URL")
    parser.add_argument("output_positional", nargs="?", default=None,
                        help="（兼容旧版）输出目录")
    parser.add_argument("--output", "-o", default=None, help="输出目录（覆盖位置参数）")
    parser.add_argument("--concurrency", type=int, default=DEFAULTS["image_concurrency"],
                        help=f"图片并发数（默认 {DEFAULTS['image_concurrency']}）")
    parser.add_argument("--retries", type=int, default=DEFAULTS["image_retries"],
                        help="单张图片最大重试次数")
    parser.add_argument("--max-pins", type=int, default=0,
                        help="限制最多处理的 Pin 数量（0=不限）")
    parser.add_argument("--cookies", default=None,
                        help="Netscape 格式 cookies.txt（访问私密画板时使用）")
    parser.add_argument("--name-by", choices=["seq", "pin"], default="seq",
                        help="文件命名：seq=序号（默认），pin=包含 Pin ID")
    parser.add_argument("--no-video", action="store_true", help="跳过视频检测与下载")
    parser.add_argument("--scroll-pause", type=float, default=DEFAULTS["scroll_pause"],
                        help="每次滚动后的等待秒数")
    parser.add_argument("--resume", action="store_true",
                        help="增量模式：复用上次的 _urls_cache.txt，跳过重新滚动（只下载尚未在 _manifest.txt 中的图）")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__} (Last Tested: {LAST_TESTED})")
    return parser.parse_args()


async def main():
    args = parse_args()

    board_url = args.board_url.strip().rstrip("/")
    if "pinterest.com" not in board_url.lower():
        log("❌ 请提供有效的 Pinterest 画板 URL")
        sys.exit(1)

    output_dir = args.output or args.output_positional
    if not output_dir:
        board_name = board_url.rstrip("/").split("/")[-1] or "board"
        output_dir = os.path.join(os.getcwd(), f"pinterest_{board_name}")

    # Windows 路径安全检查
    try:
        os.makedirs(output_dir, exist_ok=True)
        # 写入测试文件确认有写权限
        test_file = os.path.join(output_dir, "_write_test.tmp")
        with open(test_file, "w") as _tf:
            _tf.write("ok")
        os.remove(test_file)
    except PermissionError:
        log(f"❌ 没有写入权限: {output_dir}")
        log("   Windows 用户请避免使用 C:\\Program Files 等系统目录")
        log("   建议改为: --output C:\\Users\\<你的用户名>\\Downloads\\pinterest")
        sys.exit(1)
    except OSError as e:
        log(f"❌ 无法创建输出目录: {e}")
        log("   Windows 用户注意：路径中不能包含 / \\ : * ? \" < > | 等特殊字符")
        sys.exit(1)

    # 组合 cfg
    cfg = dict(DEFAULTS)
    cfg["image_concurrency"] = max(1, args.concurrency)
    cfg["image_retries"] = max(1, args.retries)
    cfg["scroll_pause"] = args.scroll_pause

    # Cookie
    jar, pw_cookies = load_cookies(args.cookies)
    cfg["_pw_cookies"] = pw_cookies
    cfg["_cookie_header"] = cookie_header_from_jar(jar)

    print(f"\n{'='*64}")
    print(f"  🎨 Pinterest Board Downloader v{__version__}  (Last Tested: {LAST_TESTED})")
    print(f"{'='*64}")
    print(f"  📍 画板:   {board_url}")
    print(f"  📂 输出:   {output_dir}")
    print(f"  ⚙️  并发:   {cfg['image_concurrency']} | 重试 {cfg['image_retries']} | 命名 {args.name_by}")
    if args.cookies:
        print(f"  🔐 Cookie: {args.cookies}")
    if args.max_pins:
        print(f"  🔢 限制:   最多 {args.max_pins} 个 Pin")
    if args.no_video:
        print(f"  🎬 视频:   已跳过")
    if args.resume:
        print(f"  ⏩ 模式:   --resume 增量（复用缓存，跳过重新滚动）")
    print(f"{'='*64}\n")

    # Phase 1
    log("📋 [1/5] 滚动画板收集数据...")
    image_records, pin_ids = await collect_board_data(
        board_url, output_dir, cfg, resume=args.resume
    )

    if args.max_pins > 0:
        image_records = image_records[: args.max_pins]
        pin_ids = pin_ids[: args.max_pins]
        log(f"已按 --max-pins 截断到 {args.max_pins}")

    if not image_records and not pin_ids:
        log("⚠️ 未收集到任何内容。可能原因：")
        log("    · 画板需要登录 → 使用 --cookies 传入 cookies.txt")
        log("    · 画板 URL 错误 / 画板被删除")
        log("    · 网络/地域限制 → 检查是否能正常访问 pinterest.com")
        sys.exit(2)

    # Phase 2
    if args.no_video:
        video_results = []
        log("\n🎬 [2/5] 已跳过视频检测（--no-video）")
    else:
        log(f"\n🎬 [2/5] 检测视频 Pin（{len(pin_ids)} 个）...")
        video_results = await detect_video_pins(pin_ids, output_dir, cfg)

    # 剔除视频 Pin 的封面图（视频 Pin 的封面图是缩略图，不应下载）
    if video_results:
        video_pin_ids = {pid for pid, _, _ in video_results}
        before = len(image_records)
        image_records = [rec for rec in image_records if rec[0] not in video_pin_ids]
        removed = before - len(image_records)
        if removed:
            log(f"  🔀 已剔除 {removed} 张视频封面图（这些 Pin 已有视频下载）")

    # Phase 3
    log(f"\n🖼️ [3/5] 下载图片（{len(image_records)} 张）...")
    img_s, img_f = await download_images_async(image_records, output_dir, cfg, args.name_by)

    # Phase 4
    if video_results:
        log(f"\n🎥 [4/5] 下载视频（{len(video_results)} 个）...")
        vid_s, vid_f = download_videos(video_results, output_dir, cfg)
    else:
        log("\n🎥 [4/5] 无视频，跳过")
        vid_s = vid_f = 0

    # Phase 5
    log(f"\n🔍 [5/5] 补救式高清化...")
    upgraded = upgrade_small_images(output_dir, cfg)

    # 汇总
    total_files = img_s + vid_s
    total_bytes = 0
    if os.path.isdir(output_dir):
        for dp, _, fns in os.walk(output_dir):
            for f in fns:
                if f.startswith("_"):
                    continue
                try:
                    total_bytes += os.path.getsize(os.path.join(dp, f))
                except OSError:
                    pass

    print(f"\n{'='*64}")
    print(f"  ✅ 全部完成!")
    print(f"{'='*64}")
    print(f"  📂 目录:   {output_dir}")
    print(f"  🖼️ 图片:   {img_s} 成功, {img_f} 失败")
    if video_results:
        print(f"  🎬 视频:   {vid_s} 成功, {vid_f} 失败")
    if upgraded:
        print(f"  ⬆️ 升级:   {upgraded} 张小图已高清化")
    print(f"  📦 总计:   {total_files} 文件, {total_bytes / 1024 / 1024:.1f} MB")
    print(f"{'='*64}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("\n⏹️ 用户中断。已下载文件保留在输出目录，重跑会自动断点续传。")
        sys.exit(130)
