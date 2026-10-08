import os
import math
import logging
from typing import Dict, Any, List, Optional
import yt_dlp

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
COOKIES_FILE = os.getenv("COOKIES_FILE", DEFAULT_COOKIES_FILE)

# إذا تم تمرير الكوكيز كنص عبر متغير البيئة YOUTUBE_COOKIES في Railway
env_cookies = os.getenv("YOUTUBE_COOKIES")
if env_cookies:
    try:
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(env_cookies.strip())
        logger.info(f"Successfully written YOUTUBE_COOKIES to: {COOKIES_FILE}")
    except Exception as e:
        logger.warning(f"Could not write YOUTUBE_COOKIES to file: {e}")

def get_cookie_file_path() -> Optional[str]:
    """العثور على مسار ملف الكوكيز المؤكد."""
    candidates = [
        COOKIES_FILE,
        os.path.join(BASE_DIR, "cookies.txt"),
        os.path.join(os.getcwd(), "cookies.txt"),
        "/app/cookies.txt",
        "/tmp/cookies.txt",
    ]
    for path in candidates:
        if path and os.path.exists(path) and os.path.getsize(path) > 10:
            return path
    return None

def format_bytes(size_bytes: Optional[int]) -> Optional[str]:
    """تحويل حجم الملف بالبايت إلى صيغة مقروءة (MB, GB, إلخ)."""
    if size_bytes is None or size_bytes <= 0:
        return None
    units = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {units[i]}"

def format_duration(seconds: Optional[int]) -> Optional[str]:
    """تحويل مدة الفيديو بالثواني إلى صيغة دقيقة:ثانية أو ساعة:دقيقة:ثانية."""
    if seconds is None:
        return None
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def extract_youtube_info(url: str) -> Dict[str, Any]:
    """
    استخراج تفاصيل الفيديو والروابط المباشرة المؤقتة لجميع الجودات.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'no_color': True,
        'skip_download': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'js_runtimes': {'node': {}},
        'remote_components': ['ejs:github']
    }

    # إضافة ملف الكوكيز إذا كان متوفراً
    cookie_path = get_cookie_file_path()
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path
        logger.info(f"Using cookies from: {cookie_path}")
    else:
        logger.warning("No cookies.txt found! Requests may fail on datacenter IPs.")

    # دعم البروكسي اختياري في حال الحاجة
    proxy = os.getenv("YOUTUBE_PROXY") or os.getenv("HTTP_PROXY")
    if proxy:
        ydl_opts['proxy'] = proxy
        logger.info("Using configured proxy for requests.")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("تعذر جلب بيانات الفيديو من الرابط المرفق.")

    # استخراج البيانات الأساسية
    video_id = info.get("id")
    title = info.get("title")
    duration = info.get("duration")
    thumbnail = info.get("thumbnail")
    uploader = info.get("uploader")
    channel_url = info.get("channel_url")
    view_count = info.get("view_count")
    description = info.get("description", "")
    short_description = (description[:300] + "...") if description and len(description) > 300 else description

    raw_formats: List[Dict[str, Any]] = info.get("formats", [])

    video_with_audio: List[Dict[str, Any]] = []
    video_only: List[Dict[str, Any]] = []
    audio_only: List[Dict[str, Any]] = []

    for f in raw_formats:
        direct_url = f.get("url")
        if not direct_url:
            continue

        vcodec = f.get("vcodec") or "none"
        acodec = f.get("acodec") or "none"

        has_video = vcodec != "none"
        has_audio = acodec != "none"

        filesize = f.get("filesize") or f.get("filesize_approx")
        filesize_str = format_bytes(filesize)

        format_data = {
            "format_id": f.get("format_id"),
            "ext": f.get("ext"),
            "quality_note": f.get("format_note"),
            "resolution": f.get("resolution"),
            "width": f.get("width"),
            "height": f.get("height"),
            "fps": f.get("fps"),
            "filesize_bytes": filesize,
            "filesize_readable": filesize_str,
            "vcodec": vcodec,
            "acodec": acodec,
            "abr_kbps": f.get("abr"),  # audio bitrate
            "vbr_kbps": f.get("vbr"),  # video bitrate
            "container": f.get("container"),
            "protocol": f.get("protocol"),
            "url": direct_url,         # الرابط المباشر المؤقت
        }

        # تصنيف الروابط
        if has_video and has_audio:
            video_with_audio.append(format_data)
        elif has_video and not has_audio:
            video_only.append(format_data)
        elif has_audio and not has_video:
            audio_only.append(format_data)

    # ترتيب الجودات من الأعلى إلى الأدنى
    def sort_by_height(item):
        return item.get("height") or 0

    def sort_by_abr(item):
        return item.get("abr_kbps") or 0

    video_with_audio.sort(key=sort_by_height, reverse=True)
    video_only.sort(key=sort_by_height, reverse=True)
    audio_only.sort(key=sort_by_abr, reverse=True)

    return {
        "status": "success",
        "video_info": {
            "id": video_id,
            "title": title,
            "duration_seconds": duration,
            "duration_readable": format_duration(duration),
            "thumbnail": thumbnail,
            "uploader": uploader,
            "channel_url": channel_url,
            "view_count": view_count,
            "description_preview": short_description,
            "original_url": url,
        },
        "stats": {
            "total_formats": len(raw_formats),
            "video_with_audio_count": len(video_with_audio),
            "video_only_count": len(video_only),
            "audio_only_count": len(audio_only),
        },
        "streams": {
            # فيديوهات مدمجة بالصوت (عادة 720p و 360p) جاهزة للتشغيل المباشر
            "video_with_audio": video_with_audio,
            # فيديوهات فقط بدون صوت (1080p, 2K, 4K, 8K)
            "video_only": video_only,
            # ملفات صوتية فقط (m4a, webm, opus)
            "audio_only": audio_only,
        }
    }
