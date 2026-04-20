#!/usr/bin/env python3
"""
================================================================================
   Pinterest Board Downloader - Standalone Edition (v2.0)
================================================================================

一个独立的、零框架依赖的 Pinterest 画板下载工具。
支持图片 + 视频 + 高清化升级，一条命令完成全量采集。

兼容：Python 3.8+ | macOS / Linux / Windows
适用：任何 AI 工具（ChatGPT / Claude / Gemini / Copilot / Cursor 等）

--------------------------------------------------------------------------------
用法：
    python3 pinterest_board_downloader.py <画板URL> [输出目录]

示例：
    python3 pinterest_board_downloader.py https://www.pinterest.com/user/ui/
    python3 pinterest_board_downloader.py https://www.pinterest.com/user/ui/ ./my_images

依赖安装（仅需一次）：
    pip install playwright aiohttp
    playwright install chromium
--------------------------------------------------------------------------------
"""

import asyncio
import os
import sys
import re
import time
import json
import urllib.parse
import urllib.request
from pathlib import Path

# ================================================================
# 可调参数（AI 可以根据用户需求修改这些值）
# ================================================================

SCROLL_PAUSE = 1.5            # 每次滚动后等待秒数
MAX_SCROLLS = 500             # 最大滚动次数上限
STAGNANT_LIMIT = 5           # 连续N次无新内容则停止滚动
IMAGE_TIMEOUT = 30            # 图片下载超时(秒)
IMAGE_DELAY = 0.5             # 图片下载间隔(秒)
VIDEO_CONCURRENCY = 20        # 视频检测并发数
VIDEO_HTTP_TIMEOUT = 10       # 视频pin页面请求超时(秒)
HQ_THRESHOLD = 15 * 1024      # 小于此值的文件尝试高清升级(字节)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def log(msg):
    """带时间戳的日志"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ================================================================
# Phase 1 - 滚动画板，收集图片URL和Pin链接（需要Playwright浏览器）
# ================================================================

async def collect_board_data(board_url: str, output_dir: str):
    """
    用 Playwright 无头浏览器打开 Pinterest 画板页面，自动滚动加载全部内容，
    从 DOM 中提取所有图片 URL 和 Pin 链接。

    参数:
        board_url: Pinterest 画板完整URL，如 "https://www.pinterest.com/user/board/"
        output_dir: 输出目录路径，用于缓存中间数据

    返回:
        (image_urls: list[str], pin_ids: list[str])
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log("❌ 缺少依赖: 请先运行 `pip install playwright && playwright install chromium`")
        sys.exit(1)

    all_img_urls = []
    all_pin_ids = []
    seen_urls = set()
    seen_pins = set()

    log(f"启动浏览器...")
    
    p = await async_playwright().start()
    browser = await p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
    )
    ctx = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1920, "height": 1080}
    )
    page = await ctx.new_page()
    page.set_default_timeout(60000)

    try:
        log(f"正在打开: {board_url}")
        resp = await page.goto(board_url, wait_until="domcontentloaded", timeout=30000)
        
        if resp and resp.status >= 400:
            log(f"⚠️ 页面返回状态码: {resp.status}")
        
        # 等待初始内容渲染
        await asyncio.sleep(4)

        stagnant_count = 0
        prev_total_imgs = 0

        for scroll_i in range(1, MAX_SCROLLS + 1):
            # ---- 从DOM提取图片URL ----
            urls = await page.evaluate('''() => {
                const results = new Set();
                // 策略1: 所有 <img> 标签的 src 属性
                document.querySelectorAll('img').forEach(img => {
                    let src = img.src || img.dataset.src || img.getAttribute('data-src') || '';
                    if (src && src.startsWith('http') &&
                        (src.includes('pinimg.com') || src.includes('i.pinimg.com'))) {
                        results.add(src.split('?')[0]);
                    }
                });
                // 策略2: background-image CSS样式
                document.querySelectorAll('[style*="background-image"]').forEach(el => {
                    const style = el.getAttribute('style') || '';
                    const match = style.match(/url\\(["']?([^"')]+)["']?\\)/);
                    if (match && match[1] && match[1].startsWith('http')) {
                        results.add(match[1].split('?')[0]);
                    }
                });
                return [...results];
            }''')

            new_count = 0
            for url in urls:
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_img_urls.append(url)
                    new_count += 1

            # ---- 从DOM提取Pin链接 ----
            pins = await page.evaluate('''() => {
                const pins = new Set();
                document.querySelectorAll('a[href*="/pin/"]').forEach(a => {
                    const m = a.href.match(/\\/pin\\/(\\d+)/);
                    if (m) pins.add(m[1]);
                });
                return [...pins];
            }''')

            for pid in pins:
                if pid not in seen_pins:
                    seen_pins.add(pid)
                    all_pin_ids.append(pid)

            total_imgs = len(all_img_urls)
            total_pins = len(all_pin_ids)

            if scroll_i % 15 == 0 or new_count > 5:
                log(f"  滚动 #{scroll_i}: 图片 {total_imgs} 张 (+{new_count}), Pin {total_pins} 个")

            # 判断是否到达底部
            if total_imgs == prev_total_imgs:
                stagnant_count += 1
                if stagnant_count >= STAGNANT_LIMIT:
                    log(f"  连续{STAGNANT_LIMIT}次无新内容，已到底部")
                    break
            else:
                stagnant_count = 0
            
            prev_total_imgs = total_imgs

            # 执行滚动
            await page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
            await asyncio.sleep(SCROLL_PAUSE)

        # 保存缓存文件
        _save_cache(os.path.join(output_dir, "_urls_cache.txt"), all_img_urls)
        _save_cache(os.path.join(output_dir, "_pins_cache.txt"), all_pin_ids)

        log(f"\n✅ 收集完成: {len(all_img_urls)} 张图片, {len(all_pin_ids)} 个 Pin")

    finally:
        await browser.close()
        await p.stop()

    return all_img_urls, all_pin_ids


# ================================================================
# Phase 2 - 并发检测哪些Pin包含视频（纯HTTP，无需浏览器）
# ================================================================

async def detect_video_pins(pin_ids: list, output_dir: str):
    """
    对每个 Pin 页面发送 HTTP GET 请求，从 HTML 中用正则匹配视频 URL。
    使用 aiohttp 并发加速，速度比逐个浏览器打开快约100倍。

    参数:
        pin_ids: Pin ID列表（纯数字字符串）
        output_dir: 输出目录（用于缓存结果）

    返回:
        list of (pin_id, video_url, video_type) 元组
    """
    try:
        import aiohttp
    except ImportError:
        log("⚠️ 缺少aiohttp，跳过视频检测。运行: pip install aiohttp")
        return []

    log(f"并发检测 {len(pin_ids)} 个 Pin 是否含视频... (并发={VIDEO_CONCURRENCY})")

    video_results = []
    checked = 0
    sem = asyncio.Semaphore(VIDEO_CONCURRENCY)

    async def check_one(session, pin_id: str):
        nonlocal checked
        async with sem:
            url = f"https://www.pinterest.com/pin/{pin_id}/"
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=VIDEO_HTTP_TIMEOUT),
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                    }
                ) as resp:
                    if resp.status != 200:
                        return None
                    html = await resp.text()

                    # 匹配 MP4 直链
                    mp4_m = re.search(r'https?://[^\s"\'><]+\.mp4', html)
                    if mp4_m:
                        return (pin_id, mp4_m.group(0), "mp4")

                    # 匹配 HLS 流地址
                    hls_m = re.search(r'https?://[^\s"\'><]+\.m3u8', html)
                    if hls_m:
                        return (pin_id, hls_m.group(0), "m3u8")

                    return None
            except Exception:
                return None
            finally:
                checked += 1
                if checked % 100 == 0 or checked == len(pin_ids):
                    current_vids = len(video_results)
                    log(f"  已检查 {checked}/{len(pin_ids)} 个... 发现 {current_vids} 个视频")

    connector = aiohttp.TCPConnector(limit=VIDEO_CONCURRENCY + 5)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check_one(session, pid) for pid in pin_ids]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in raw_results:
        if isinstance(r, tuple) and r is not None:
            video_results.append(r)

    # 保存缓存
    vid_path = os.path.join(output_dir, "_video_list.txt")
    with open(vid_path, "w") as f:
        for pid, vurl, vtype in video_results:
            f.write(f"{pid}\t{vtype}\t{vurl}\n")

    log(f"✅ 视频检测完成: {len(video_results)} 个")
    for i, (pid, vurl, vtype) in enumerate(video_results, 1):
        log(f"  [{i}] #{pid} → {vtype}")

    return video_results


# ================================================================
# Phase 3 - 批量下载图片
# ================================================================

def download_images(image_urls: list, output_dir: str):
    """
    遍历所有图片URL并逐个下载到本地。
    支持断点续传（跳过已存在的大文件）和多尺寸变体回退。

    参数:
        image_urls: 图片URL列表
        output_dir: 输出目录

    返回:
        (success_count, fail_count)
    """
    os.makedirs(output_dir, exist_ok=True)
    success = 0
    fail = 0
    skipped = 0

    for idx, img_url in enumerate(image_urls, 1):
        ext = _guess_ext(img_url)
        filename = f"pinterest_{idx:04d}{ext}"
        save_path = os.path.join(output_dir, filename)

        # 断点续传：已存在的有效文件跳过
        if os.path.exists(save_path) and os.path.getsize(save_path) > HQ_THRESHOLD:
            skipped += 1
            if skipped <= 5 or idx % 100 == 0:
                sz = os.path.getsize(save_path)
                log(f"  ⊘ [{idx}] 已存在: {filename} ({sz//1024}KB)")
            continue

        downloaded = False

        # --- 尝试1: 直接下载原始URL ---
        downloaded = _try_download(img_url, save_path, idx)

        # --- 尝试2: 如果失败，尝试其他CDN尺寸变体 ---
        if not downloaded:
            downloaded = _try_variants(img_url, save_path, idx)

        if downloaded:
            success += 1
        else:
            fail += 1
            log(f"  ✗ [{idx}] 失败: {img_url[:80]}")

        time.sleep(IMAGE_DELAY)

    log(f"\n图片结果: ✓{success} ✗{fail} ⊘{skipped}")
    return success, fail


# ================================================================
# Phase 4 - 批量下载视频
# ================================================================

def download_videos(video_results: list, output_dir: str):
    """
    将检测到的视频URL批量下载到 videos/ 子目录。

    参数:
        video_results: [(pin_id, url, type), ...]
        output_dir: 输出根目录

    返回:
        (success_count, fail_count)
    """
    videos_dir = os.path.join(output_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)

    success = 0
    fail = 0

    for idx, (pin_id, video_url, video_type) in enumerate(video_results, 1):
        ext = ".mp4" if video_type == "mp4" else ".ts"
        filename = f"video_{idx:03d}_{pin_id}{ext}"
        save_path = os.path.join(videos_dir, filename)

        if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
            log(f"  ⊘ [{idx}] 已存在: {filename}")
            success += 1
            continue

        ok = _try_download(
            video_url, save_path, idx,
            extra_headers={"Referer": "https://www.pinterest.com/", "Accept": "video/mp4,*/*"},
            timeout=60
        )

        if ok:
            success += 1
        else:
            fail += 1
            log(f"  ✗ [{idx}] 视频: {video_url[:60]}")

        time.sleep(0.5)

    log(f"\n视频结果: ✓{success} ✗{fail}")
    return success, fail


# ================================================================
# Phase 5 - 小图高清化升级
# ================================================================

def upgrade_small_images(output_dir: str):
    """
    扫描输出目录中小于阈值的图片文件，尝试从CDN获取更大分辨率版本。
    通过替换URL中的尺寸标识（originals ↔ 736x ↔ 564x 等）来获取不同尺寸。

    参数:
        output_dir: 输出目录

    返回:
        升级成功的数量
    """
    cache_file = os.path.join(output_dir, "_urls_cache.txt")
    if not os.path.exists(cache_file):
        log("未找到URL缓存文件，跳过高清化")
        return 0

    with open(cache_file) as f:
        all_urls = [line.strip() for line in f if line.strip()]

    # 找出需要升级的小图
    small_files = []
    for fname in sorted(os.listdir(output_dir)):
        if not fname.startswith("pinterest_"):
            continue
        fpath = os.path.join(output_dir, fname)
        if not os.path.isfile(fpath) or os.path.getsize(fpath) >= HQ_THRESHOLD:
            continue
        # 解析序号: pinterest_0001.jpg -> idx=0
        parts = fname.replace(".jpg","").replace(".png","").replace(".gif","").replace(".webp","").split("_")
        if len(parts) >= 2:
            try:
                idx = int(parts[1]) - 1
                if 0 <= idx < len(all_urls):
                    small_files.append((fname, fpath, all_urls[idx]))
            except ValueError:
                pass

    if not small_files:
        log("没有需要升级的小图")
        return 0

    log(f"发现 {len(small_files)} 张小图，尝试高清化...")
    upgraded = 0

    for fname, fpath, original_url in small_files:
        current_size = os.path.getsize(fpath)
        best_data = None
        best_size = current_size

        # 构建候选URL列表
        candidates = []
        for old_seg in ['/originals/', '/736x/', '/564x/', '/474x/', '/236x/']:
            if old_seg in original_url:
                for new_seg in ['/originals/', '/736x/', '/564x/', '/474x/']:
                    cand = original_url.replace(old_seg, new_seg)
                    if cand != original_url:
                        candidates.append(cand)
                candidates.insert(0, original_url)  # 原始URL也加入候选
                break

        for var_url in candidates[:7]:
            try:
                req = urllib.request.Request(var_url, headers={
                    'User-Agent': USER_AGENT,
                    'Referer': 'https://www.pinterest.com/',
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = resp.read()
                    if data and len(data) > best_size:
                        best_data = data
                        best_size = len(data)
            except Exception:
                continue

        # 新版本必须明显更大才替换（至少大20%）
        if best_data and best_size > current_size * 1.2:
            with open(fpath, "wb") as f:
                f.write(best_data)
            upgraded += 1
            if upgraded <= 10 or upgraded % 20 == 0:
                log(f"  ↑ {fname}: {current_size//1024}KB → {best_size//1024}KB")

    log(f"高清化完成: {upgraded}/{len(small_files)} 张已升级")
    return upgraded


# ================================================================
# 内部工具函数
# ================================================================

def _save_cache(filepath: str, lines: list):
    """将列表写入缓存文件（每行一项）"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        for item in lines:
            f.write(str(item) + "\n")


def _guess_ext(url: str) -> str:
    """根据URL推断图片扩展名"""
    lower = url.lower()
    if '.png' in lower: return '.png'
    if '.gif' in lower: return '.gif'
    if '.webp' in lower: return '.webp'
    return '.jpg'


def _try_download(url: str, save_path: str, idx: int, extra_headers=None, timeout=IMAGE_TIMEOUT) -> bool:
    """
    尝试用urllib下载单个文件。
    返回 True 表示成功。
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if extra_headers:
        headers.update(extra_headers)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if len(data) >= 512:  # 最小512字节才认为有效
                with open(save_path, "wb") as f:
                    f.write(data)
                log(f"  ✓ [{idx}] {os.path.basename(save_path)} ({len(data)//1024}KB)")
                return True
        return False
    except Exception:
        return False


def _try_variants(original_url: str, save_path: str, idx: int) -> bool:
    """
    当原始URL下载失败时，尝试CDN的其他尺寸变体。
    Pinterest CDN通过URL中的尺寸标识区分分辨率。
    """
    size_segments = ['/originals/', '/736x/', '/564x/', '/474x/', '/236x/']
    variants = []

    for seg in size_segments:
        if seg in original_url:
            for alt in ['736x', '564x', '474x', '236x', 'originals']:
                var_url = original_url.replace(seg, '/' + alt + '/')
                if var_url != original_url:
                    variants.append(var_url)
            break

    for var_url in variants:
        if _try_download(var_url, save_path, idx):
            return True

    return False


# ================================================================
# 主入口
# ================================================================

async def main():
    # ---- 解析参数 ----
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    board_url = sys.argv[1].strip().rstrip("/")
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    if "pinterest.com" not in board_url.lower():
        log("❌ 请提供有效的 Pinterest 画板 URL")
        sys.exit(1)

    # 确定输出目录
    if not output_dir:
        board_name = board_url.rstrip("/").split("/")[-1] or "board"
        output_dir = os.path.join(os.getcwd(), f"pinterest_{board_name}")

    os.makedirs(output_dir, exist_ok=True)

    # ---- 打印信息 ----
    print(f"\n{'='*60}")
    print(f"  🎨 Pinterest Board Downloader v2.0")
    print(f"{'='*60}")
    print(f"  📍 画板:  {board_url}")
    print(f"  📂 输出:  {output_dir}")
    print(f"{'='*60}\n")

    # ====== Phase 1: 收集 ======
    log("📋 [1/5] 滚动画板收集数据...")
    image_urls, pin_ids = await collect_board_data(board_url, output_dir)
    if not image_urls:
        log("⚠️ 未收集到任何图片。可能原因：需要登录 / URL无效 / 网络问题")
        # 仍然继续执行后续阶段（可能有缓存数据）

    # ====== Phase 2: 视频检测 ======
    log(f"\n🎬 [2/5] 检测视频Pin ({len(pin_ids)}个)...")
    video_results = await detect_video_pins(pin_ids, output_dir) if pin_ids else []

    # ====== Phase 3: 下载图片 ======
    log(f"\n🖼️ [3/5] 下载图片 ({len(image_urls)}张)...")
    img_s, img_f = download_images(image_urls, output_dir)

    # ====== Phase 4: 下载视频 ======
    if video_results:
        log(f"\n🎥 [4/5] 下载视频 ({len(video_results)}个)...")
        vid_s, vid_f = download_videos(video_results, output_dir)
    else:
        log("\n🎥 [4/5] 无视频，跳过")
        vid_s = vid_f = 0

    # ====== Phase 5: 高清化 ======
    log(f"\n🔍 [5/5] 小图高清化升级...")
    upgraded = upgrade_small_images(output_dir)

    # ---- 最终报告 ----
    total_files = img_s + vid_s
    total_size_kb = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fns in os.walk(output_dir)
        for f in fns if not f.startswith("_")
    ) if os.path.isdir(output_dir) else 0

    print(f"\n{'='*60}")
    print(f"  ✅ 全部完成!")
    print(f"{'='*60}")
    print(f"  📂 目录:   {output_dir}")
    print(f"  🖼️ 图片:   {img_s} 成功, {img_f} 失败")
    if video_results:
        print(f"  🎬 视频:   {vid_s} 成功, {vid_f} 失败")
    if upgraded > 0:
        print(f"  ⬆️ 升级:   {upgraded} 张小图已高清化")
    print(f"  📦 总计:   {total_files} 文件, {total_size_kb / 1024:.1f} MB")


if __name__ == "__main__":
    asyncio.run(main())
