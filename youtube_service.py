import os
import time
import math
import shutil
import logging
from typing import Dict, Any, List, Optional
import yt_dlp
from log_manager import YtDlpLogger
from cookie_manager import get_active_cookie_path, save_cookies_content, analyze_cookies_health, read_active_cookies

logger = logging.getLogger("youtube_service")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
COOKIES_FILE = os.getenv("COOKIES_FILE", DEFAULT_COOKIES_FILE)

# إذا تم تمرير الكوكيز كنص عبر متغير البيئة YOUTUBE_COOKIES (بأي صيغة: JSON أو Netscape)
env_cookies = os.getenv("YOUTUBE_COOKIES")
if env_cookies:
    try:
        res = save_cookies_content(env_cookies)
        logger.info(f"Successfully loaded and parsed YOUTUBE_COOKIES environment variable (Format: {res.get('detected_format')})")
    except Exception as e:
        logger.warning(f"Could not parse YOUTUBE_COOKIES environment variable: {e}")


def get_cookie_file_path() -> Optional[str]:
    """العثور على مسار ملف الكوكيز المؤكد مع التحقق من الحجم والصلاحية."""
    return get_active_cookie_path()


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


def _get_js_runtime_config() -> Dict[str, Any]:
    """اكتشاف محرك جافاسكريبت المتاح (Node.js) لحل تحديات البوت والتوقيع في يوتيوب."""
    node_path = shutil.which("node")
    if node_path:
        return {'node': {}}
    return {}


def _run_yt_dlp(url: str, use_cookies: bool = True, custom_clients: Optional[List[str]] = None) -> Dict[str, Any]:
    """تنفيذ استخراج yt-dlp بإعدادات متطورة وسجل مخصص وحل التحديات."""
    ydl_opts: Dict[str, Any] = {
        'quiet': False,
        'no_warnings': False,
        'skip_download': True,
        'extract_flat': False,
        'logger': YtDlpLogger(),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        },
        'remote_components': {'ejs:github'}
    }

    # إعداد محرك JavaScript إن وجد
    js_conf = _get_js_runtime_config()
    if js_conf:
        ydl_opts['js_runtimes'] = js_conf

    if use_cookies:
        cookie_path = get_cookie_file_path()
        if cookie_path:
            ydl_opts['cookiefile'] = cookie_path
            logger.info(f"Using cookies from: {cookie_path}")
        else:
            logger.info("Cookie file requested but none found on disk; proceeding as guest.")
    else:
        logger.info("Explicitly attempting extraction without cookies (guest mode).")

    if custom_clients:
        ydl_opts['extractor_args'] = {
            'youtube': {
                'player_client': custom_clients
            }
        }
        logger.info(f"Using custom player_clients: {custom_clients}")

    proxy = os.getenv("YOUTUBE_PROXY") or os.getenv("HTTP_PROXY")
    if proxy:
        ydl_opts['proxy'] = proxy
        logger.info("Using configured proxy.")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("No video data returned by yt-dlp.")
        return info


def extract_youtube_info(url: str) -> Dict[str, Any]:
    """
    استخراج تفاصيل الفيديو والروابط المباشرة المؤقتة مع آلية ذكية متعددة المراحل
    لتجاوز أخطاء البوت أو انتهاء الكوكيز بأفضل أداء ممكن.
    """
    info = None
    last_error = None
    strategy_used = "cookies"

    # الاستراتيجية الأولى: الاستخراج الكامل مع الكوكيز النشطة وحل التحديات عبر Node
    try:
        logger.info(f"Strategy 1: Full extraction with cookies for URL: {url}")
        info = _run_yt_dlp(url, use_cookies=True)
        strategy_used = "cookies_standard"
    except Exception as e:
        last_error = e
        err_str = str(e)
        logger.warning(f"Strategy 1 failed with error: {err_str}")

        # إذا كان الخطأ متعلق بإعادة تحميل الصفحة أو طلب تسجيل الدخول أو تحدي بوت
        if "The page needs to be reloaded" in err_str or "Sign in to confirm" in err_str or "Please sign in" in err_str:
            # الاستراتيجية الثانية: محاولة استخدام عملاء ويب مدمجين
            try:
                logger.info("Strategy 2: Retrying with web_embedded and android clients...")
                info = _run_yt_dlp(url, use_cookies=True, custom_clients=['web_embedded', 'android'])
                strategy_used = "cookies_fallback_client"
            except Exception as e2:
                last_error = e2
                logger.warning(f"Strategy 2 failed: {str(e2)}")

                # الاستراتيجية الثالثة: محاولة كزائر بدون كوكيز (غالباً تنجح للفيديوهات العامة حتى لو الكوكيز منتهية)
                try:
                    logger.info("Strategy 3: Retrying in guest mode without cookies...")
                    info = _run_yt_dlp(url, use_cookies=False)
                    strategy_used = "guest_no_cookies"
                except Exception as e3:
                    last_error = e3
                    logger.error(f"Strategy 3 failed: {str(e3)}")

    if not info:
        raise last_error or RuntimeError("Failed to extract video information.")

    # معالجة وتنظيم بيانات الفيديو والجودات
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
            "abr_kbps": f.get("abr"),
            "vbr_kbps": f.get("vbr"),
            "container": f.get("container"),
            "protocol": f.get("protocol"),
            "url": direct_url,
        }

        if has_video and has_audio:
            video_with_audio.append(format_data)
        elif has_video and not has_audio:
            video_only.append(format_data)
        elif has_audio and not has_video:
            audio_only.append(format_data)

    def sort_by_height(item):
        return item.get("height") or 0

    def sort_by_abr(item):
        return item.get("abr_kbps") or 0

    video_with_audio.sort(key=sort_by_height, reverse=True)
    video_only.sort(key=sort_by_height, reverse=True)
    audio_only.sort(key=sort_by_abr, reverse=True)

    return {
        "status": "success",
        "strategy_used": strategy_used,
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
            "video_with_audio": video_with_audio,
            "video_only": video_only,
            "audio_only": audio_only,
        }
    }


def test_cookie_health_live(test_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ") -> Dict[str, Any]:
    """
    إجراء فحص حي فوري للكوكيز المسجلة عبر طلب تجريبي وحساب وقت الاستجابة
    """
    start_time = time.time()
    try:
        data = extract_youtube_info(test_url)
        elapsed_sec = round(time.time() - start_time, 2)
        return {
            "success": True,
            "elapsed_seconds": elapsed_sec,
            "video_title": data["video_info"]["title"],
            "uploader": data["video_info"]["uploader"],
            "total_formats": data["stats"]["total_formats"],
            "strategy": data.get("strategy_used"),
            "message": f"تم الاتصال وفحص الروابط بنجاح في {elapsed_sec} ثانية! (عدد الجودات: {data['stats']['total_formats']})"
        }
    except Exception as e:
        elapsed_sec = round(time.time() - start_time, 2)
        return {
            "success": False,
            "elapsed_seconds": elapsed_sec,
            "error": str(e),
            "message": f"فشل الفحص الحي: {str(e)}"
        }
