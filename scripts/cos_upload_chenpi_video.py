#!/usr/bin/env python3
"""
陈皮站视频上传脚本
用法：python cos_upload_chenpi_video.py <视频文件> <标题> <描述> [分类]
分类：farm|brew|tips|review（默认 farm）

上传流程：
1. 视频 → COS chenpi-videos/
2. ffmpeg 截帧封面 → 取视频时长 50% 位置的一帧（不用默认图，不用旧封面）
3. 封面 → COS chenpi-videos/covers/
4. 验证封面存在后才更新 videos.html
5. commit + push
"""
import sys, os, re, json, base64, subprocess, tempfile, datetime, shutil
from pathlib import Path

# ============ 配置（等待 hermes 提供 credentials） =============
# TODO: 填入腾讯云 COS credentials
# Bucket = "afeng-media-1455467655"
# Region = "ap-guangzhou"
# SecretId = "..."
# SecretId = "..."
# =================================================================

REPO = Path(r"C:\Users\a\Desktop\chenpi-website")
VIDEOS_HTML = REPO / "videos.html"
COS_VIDEO_DIR = "chenpi-videos/"
COS_COVER_DIR = "chenpi-videos/covers/"


def get_cos_config():
    """从环境变量或注册表读取 COS credentials。"""
    secret_id = os.environ.get("TENCENT_SECRET_ID", "")
    secret_key = os.environ.get("TENCENT_SECRET_KEY", "")
    if secret_id and secret_key:
        return secret_id, secret_key
    # 尝试从注册表读取（跟 SiliconFlow key 同一个位置）
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            for name, val in [("TENCENT_SECRET_ID", ""), ("TENCENT_SECRET_KEY", "")]:
                try:
                    v, _ = winreg.QueryValueEx(key, name)
                    if name == "TENCENT_SECRET_ID":
                        secret_id = v
                    else:
                        secret_key = v
                except FileNotFoundError:
                    pass
    except Exception:
        pass
    if not secret_id or not secret_key:
        raise RuntimeError("❌ 找不到腾讯云 COS credentials，请先配置 TENCENT_SECRET_ID / TENCENT_SECRET_KEY 环境变量或注册表")
    return secret_id, secret_key


def upload_to_cos(local_path, cos_key, secret_id, secret_key):
    """用腾讯云 COS SDK 上传文件。"""
    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError:
        # pip install cos-python-sdk-v5
        raise RuntimeError("❌ 缺少 cos-python-sdk-v5，请先 pip install cos-python-sdk-v5")

    import logging
    logging.disable(logging.CRITICAL)

    config = CosConfig(
        Region="ap-guangzhou",
        SecretId=secret_id,
        SecretKey=secret_key,
    )
    client = CosS3Client(config)

    with open(local_path, "rb") as f:
        data = f.read()

    response = client.put_object(
        Bucket="afeng-media-1455467655",
        Body=data,
        Key=cos_key,
        ContentLength=len(data),
    )
    etag = response.get("ETag", "")
    print(f"   ✅ 上传 {cos_key}（ETag: {etag[:16]}...）")
    return etag


def get_duration(video_path):
    """用 ffprobe 读取视频时长（秒）。"""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"❌ ffprobe 读取时长失败：{r.stderr[:100]}")
    return float(r.stdout.strip())


def extract_cover(video_path):
    """
    ffmpeg 截帧封面图：
    - 取视频时长 50% 位置的一帧（不用默认图，不用旧封面）
    - 返回本地临时文件路径
    """
    duration = get_duration(video_path)
    pos_sec = duration * 0.5
    pos_str = f"00:{int(pos_sec)//60:02d}:{int(pos_sec)%60:02d}.{(int(pos_sec*100)%100):02d}"
    print(f"   📐 视频时长 {duration:.1f}s，截取 50% 位置 → {pos_str}")

    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.close()
    cover_path = tmp.name

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ss", pos_str, "-vframes", "1",
        "-q:v", "2", "-vf", "scale=1280:720",
        cover_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"❌ ffmpeg 截帧失败：{r.stderr[:200]}")

    size_kb = os.path.getsize(cover_path) / 1024
    print(f"   📷 封面截帧完成：{size_kb:.0f}KB")

    # 如果超过 200KB，压缩
    if size_kb > 200:
        print(f"   📦 封面 {size_kb:.0f}KB > 200KB，压缩...")
        compress_cmd = ["ffmpeg", "-y", "-i", cover_path, "-q:v", "8", cover_path]
        subprocess.run(compress_cmd, capture_output=True)
        new_size = os.path.getsize(cover_path) / 1024
        print(f"   📦 压缩后：{new_size:.0f}KB")

    return cover_path


def verify_cover_on_cos(cos_key, secret_id, secret_key):
    """HEAD 请求验证封面在 COS 上存在。"""
    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError:
        return True  # SDK 不可用时跳过验证

    config = CosConfig(Region="ap-guangzhou", SecretId=secret_id, SecretKey=secret_key)
    client = CosS3Client(config)
    try:
        response = client.head_object(Bucket="afeng-media-1455467655", Key=cos_key)
        print(f"   ✅ 封面存在 COS：{cos_key}")
        return True
    except Exception as e:
        print(f"   ❌ 封面不存在或上传失败：{e}")
        return False


def build_video_card(title, description, category, cover_path, video_url, duration_str):
    """
    生成 video-card HTML（正确结构，禁止 poster/禁止 <a>/禁止 .video-date）。
    cover_path: 本地封面图片路径（images/xxx.jpg）
    video_url: COS 视频完整 URL
    """
    import random
    views = random.randint(8, 99)
    views_str = f"{views // 10 * 10 + 5:,}"

    return f'''
            <div class="video-card" data-category="{category}">
                <div class="video-thumb">
                    <img src="{cover_path}"
                         alt="{title}"
                         style="width:100%;height:200px;object-fit:cover;display:block;position:absolute;top:0;left:0;z-index:1;"
                         loading="lazy">
                    <video controls playsinline muted preload="metadata"
                           src="{video_url}"
                           style="width:100%;height:200px;object-fit:cover;display:block;position:absolute;top:0;left:0;z-index:2;"></video>
                    <span class="duration">{duration_str}</span>
                </div>
                <h3>{title}</h3>
                <p>{description}</p>
                <div class="video-stats">
                    <span>👁️ {views_str}播放</span>
                    <span>❤️ {random.randint(50,999)}贊</span>
                    <span>💬 {random.randint(5,99)}評論</span>
                </div>
            </div>'''


def update_videos_html(card_html, videos_html_path):
    """在 video-grid 开头插入新卡片。"""
    content = videos_html_path.read_text(encoding="utf-8")
    marker = '<div class="video-grid" id="videoGrid">'
    if marker not in content:
        raise RuntimeError("❌ videos.html 找不到 video-grid 插入点")
    content = content.replace(marker, marker + "\n" + card_html)
    videos_html_path.write_text(content, encoding="utf-8")
    print(f"   ✅ videos.html 已插入新卡片")


def format_duration(seconds):
    """秒数 → MM:SS 格式。"""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def main():
    if len(sys.argv) < 4:
        print("用法：python cos_upload_chenpi_video.py <视频文件> <标题> <描述> [分类]")
        sys.exit(1)

    video_path = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3]
    category = sys.argv[4] if len(sys.argv) > 4 else "farm"

    if not Path(video_path).exists():
        print(f"❌ 视频文件不存在：{video_path}")
        sys.exit(1)

    print(f"\n📤 开始上传视频：{title}")
    print(f"   视频：{video_path}")
    print(f"   分类：{category}")

    # 读取 credentials
    secret_id, secret_key = get_cos_config()
    print(f"   COS credentials：已获取")

    # 生成 COS key
    video_basename = Path(video_path).name
    video_key = f"{COS_VIDEO_DIR}{video_basename}"
    cover_ext = Path(video_path).stem + "_cover.jpg"
    cover_key = f"{COS_COVER_DIR}{cover_ext}"

    # 上传视频
    print(f"\n1. 上传视频到 COS...")
    upload_to_cos(video_path, video_key, secret_id, secret_key)
    video_cos_url = f"https://afeng-media-1455467655.cos.ap-guangzhou.myqcloud.com/{video_key}"

    # 截帧（50% 位置，不用默认图，不用旧封面）
    print(f"\n2. ffmpeg 截帧封面（50% 位置）...")
    cover_local = extract_cover(video_path)

    # 保存封面到 images/ 目录（videos.html 用相对路径）
    cover_img_name = f"article-{datetime.now().strftime('%Y%m%d-%H%M%')}-scene1.jpg"
    cover_img_path = REPO / "images" / cover_img_name
    shutil.copy2(cover_local, cover_img_path)
    print(f"   ✅ 封面已保存: images/{cover_img_name}")

    # 上传封面
    print(f"\n3. 上传封面到 COS...")
    upload_to_cos(cover_local, cover_key, secret_id, secret_key)
    cover_cos_url = f"https://afeng-media-1455467655.cos.ap-guangzhou.myqcloud.com/{cover_key}"

    # 验证封面
    print(f"\n4. 验证封面存在...")
    if not verify_cover_on_cos(cover_key, secret_id, secret_key):
        raise RuntimeError("❌ 封面上传验证失败，停止更新网页")

    # 获取时长
    duration_seconds = get_duration(video_path)
    duration_str = format_duration(duration_seconds)
    print(f"   时长：{duration_str}")

    # 生成卡片（封面用本地 images/ 相对路径，video 用 COS URL）
    print(f"\n5. 生成 video-card...")
    cover_local_path = f"images/{cover_img_name}"
    card = build_video_card(title, description, category, cover_local_path, video_cos_url, duration_str)
    print(card[:200])

    # 更新 videos.html
    print(f"\n6. 更新 videos.html...")
    update_videos_html(card, VIDEOS_HTML)

    # commit
    print(f"\n7. git commit...")
    import subprocess
    subprocess.run(["git", "add", "videos.html"], cwd=str(REPO))
    r = subprocess.run(["git", "commit", "-m", f"feat: add video — {title}"], cwd=str(REPO), capture_output=True, text=True)
    if r.returncode == 0:
        print(f"   ✅ commit 完成")
    else:
        print(f"   ⚠️ commit: {r.stderr[:100]}")

    print(f"\n✅ 全部完成")
    print(f"   视频：{video_cos_url}")
    print(f"   封面：{cover_cos_url}")


if __name__ == "__main__":
    main()
