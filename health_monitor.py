import os
import sys
import time
import shutil
import logging
import subprocess
import urllib.request
from typing import Dict, Any, List, Optional, Tuple

from cookie_manager import read_active_cookies, analyze_cookies_health
from updater_service import get_updater_status, get_current_ytdlp_version, get_latest_pypi_version, _parse_version_tuple

logger = logging.getLogger("health_monitor")


def _run_quick_cmd(cmd: List[str], timeout: int = 4) -> Tuple[bool, str]:
    """تشغيل أمر نظام سريع لجلب الإصدار مع حماية من التعليق."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode == 0:
            first_line = (proc.stdout.strip() or proc.stderr.strip()).splitlines()[0]
            return True, first_line
        return False, proc.stderr.strip() or "Non-zero exit code"
    except Exception as e:
        return False, str(e)


def check_deno_health() -> Dict[str, Any]:
    """فحص حالة محرك Deno لحل تحديات الجافاسكريبت."""
    deno_path = shutil.which("deno")
    if not deno_path:
        return {
            "name": "Deno JS Engine",
            "installed": False,
            "status": "warning",
            "version": None,
            "path": None,
            "message": "غير مثبت (سيتم الاعتماد على Node.js لحل التحديات)",
            "badge": "غياب اختياري"
        }
    
    ok, ver_str = _run_quick_cmd([deno_path, "--version"])
    return {
        "name": "Deno JS Engine",
        "installed": True,
        "status": "healthy",
        "version": ver_str if ok else "موجود",
        "path": deno_path,
        "message": "مثبت ويعمل بكفاءة لحل تحديات n-challenge",
        "badge": "سليم ومفعل"
    }


def check_node_health() -> Dict[str, Any]:
    """فحص حالة محرك Node.js والتأكد من دعمه للميزات الحديثة (--permission)."""
    node_path = shutil.which("node")
    if not node_path:
        return {
            "name": "Node.js Engine",
            "installed": False,
            "status": "critical",
            "version": None,
            "path": None,
            "message": "غير مثبت! يلزم وجود Node.js أو Deno لحل تشفير يوتيوب",
            "badge": "مفقود"
        }

    ok, ver_str = _run_quick_cmd([node_path, "-v"])
    version_clean = ver_str.replace("v", "").strip() if ok else ""
    major_ver = 0
    try:
        major_ver = int(version_clean.split(".")[0])
    except Exception:
        pass

    if major_ver >= 20:
        status = "healthy"
        msg = f"إصدار حديث ({ver_str}) يدعم كافة ميزات الأمان والتحديات البرمجية."
        badge = "حديث وممتاز"
    elif major_ver >= 18:
        status = "warning"
        msg = f"إصدار ({ver_str}) قد يواجه قيوداً في خاصية --permission. يُفضل الترقية لـ Node 20."
        badge = "إصدار قديم نسبياً"
    else:
        status = "warning"
        msg = f"إصدار ({ver_str})."
        badge = "مقبول"

    return {
        "name": "Node.js Engine",
        "installed": True,
        "status": status,
        "version": ver_str if ok else "موجود",
        "major_version": major_ver,
        "path": node_path,
        "message": msg,
        "badge": badge
    }


def check_ffmpeg_health() -> Dict[str, Any]:
    """فحص توفر مكتبة ffmpeg لدمج وتحويل مسارات الفيديو والصوتيات."""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return {
            "name": "FFmpeg Media Core",
            "installed": False,
            "status": "warning",
            "version": None,
            "path": None,
            "message": "غير مثبت (الروابط المباشرة ستعمل، لكن دمج الصوت والصورة محلياً لن يعمل)",
            "badge": "غير متوفر"
        }

    ok, ver_str = _run_quick_cmd([ffmpeg_path, "-version"])
    return {
        "name": "FFmpeg Media Core",
        "installed": True,
        "status": "healthy",
        "version": ver_str[:40] if ok else "موجود",
        "path": ffmpeg_path,
        "message": "مثبت وجاهز لمعالجة الوسائط المتعددة والدمج",
        "badge": "جاهز"
    }


def check_ytdlp_health() -> Dict[str, Any]:
    """فحص حالة مكتبة yt-dlp ومقارنتها بأحدث إصدار على PyPI."""
    status_data = get_updater_status()
    curr_v = status_data["current_ytdlp_version"]
    latest_v = status_data["latest_pypi_version"]
    is_up = status_data["is_up_to_date"]

    if is_up:
        badge = "أحدث إصدار ✓"
        status = "healthy"
        msg = f"تعمل على أحدث إصدار متاح ({curr_v})."
    else:
        badge = f"يتوفر تحديث ({latest_v})"
        status = "warning"
        msg = f"الإصدار الحالي {curr_v}، ويتوفر إصدار أحدث {latest_v} على PyPI."

    return {
        "name": "yt-dlp Core",
        "installed": True,
        "status": status,
        "current_version": curr_v,
        "latest_pypi_version": latest_v,
        "is_up_to_date": is_up,
        "auto_updater_schedule": "كل 12 ساعة تلقائياً",
        "message": msg,
        "badge": badge
    }


def check_cookies_component() -> Dict[str, Any]:
    """فحص حالة مكون الكوكيز المسجلة وصلاحيتها ومفاتيحها."""
    cookies, cookie_path = read_active_cookies()
    analysis = analyze_cookies_health(cookies)
    file_size = os.path.getsize(cookie_path) if cookie_path and os.path.exists(cookie_path) else 0

    status = analysis["status"]
    if status == "valid":
        comp_status = "healthy"
        badge = "صالحة ونشطة"
    elif status == "guest_only":
        comp_status = "warning"
        badge = "وضع الزائر"
    elif status == "expired":
        comp_status = "critical"
        badge = "منتهية الصلاحية"
    else:
        comp_status = "critical"
        badge = "غير متوفرة"

    return {
        "name": "YouTube Cookies Session",
        "status": comp_status,
        "file_path": cookie_path,
        "file_size_bytes": file_size,
        "total_cookies": analysis["total_cookies"],
        "has_auth": analysis["has_auth"],
        "auth_cookies_found": analysis["auth_cookies_found"],
        "days_until_expiry": analysis.get("days_until_expiry", 0),
        "earliest_expiry_readable": analysis.get("earliest_expiry_readable"),
        "message": analysis["message"],
        "badge": badge
    }


def check_youtube_connectivity() -> Dict[str, Any]:
    """فحص الاتصال المباشر بخوادم يوتيوب وقياس زمن الاستجابة واكتشاف أي حظر شبكي."""
    start_time = time.time()
    try:
        req = urllib.request.Request(
            "https://www.youtube.com/generate_204",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            latency_ms = round((time.time() - start_time) * 1000, 1)
            code = response.getcode()
            return {
                "name": "YouTube Network Connectivity",
                "status": "healthy",
                "connected": True,
                "latency_ms": latency_ms,
                "http_code": code,
                "message": f"الاتصال بخوادم يوتيوب مباشر وسريع ({latency_ms} ms)",
                "badge": f"{latency_ms} ms"
            }
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 1)
        return {
            "name": "YouTube Network Connectivity",
            "status": "critical",
            "connected": False,
            "latency_ms": latency_ms,
            "error": str(e),
            "message": f"فشل الاتصال بخوادم يوتيوب: {str(e)}",
            "badge": "تعذر الاتصال"
        }


def get_full_monitoring_report() -> Dict[str, Any]:
    """
    إنشاء تقرير شامل وموحد لمركز مراقبة كافة مكونات النظام
    """
    cookies_info = check_cookies_component()
    node_info = check_node_health()
    deno_info = check_deno_health()
    ffmpeg_info = check_ffmpeg_health()
    ytdlp_info = check_ytdlp_health()
    network_info = check_youtube_connectivity()

    components = [
        cookies_info,
        node_info,
        deno_info,
        ytdlp_info,
        ffmpeg_info,
        network_info
    ]

    # تقييم الحالة العامة للنظام
    criticals = [c for c in components if c["status"] == "critical"]
    warnings = [c for c in components if c["status"] == "warning"]

    if criticals:
        overall_status = "critical"
        overall_msg = f"يوجد {len(criticals)} مكون رئيسي بحاجة لتدخل (مثال: {criticals[0]['name']})."
        badge = "حرجة 🔴"
    elif warnings:
        overall_status = "warning"
        overall_msg = f"النظام يعمل، مع وجود {len(warnings)} تنبيهات ثانوية."
        badge = "تنبيه 🟡"
    else:
        overall_status = "healthy"
        overall_msg = "جميع مكونات ومحركات النظام تعمل بكفاءة تامة 100%!"
        badge = "ممتازة 🟢"

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "overall_status": overall_status,
        "overall_message": overall_msg,
        "overall_badge": badge,
        "system_info": {
            "python_version": sys.version.split()[0],
            "os_platform": sys.platform,
            "process_id": os.getpid(),
            "working_directory": os.getcwd()
        },
        "components": {
            "cookies": cookies_info,
            "node": node_info,
            "deno": deno_info,
            "ytdlp": ytdlp_info,
            "ffmpeg": ffmpeg_info,
            "network": network_info
        }
    }
