import os
import sys
import shutil
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from log_manager import get_recent_logs, clear_logs
from youtube_service import extract_youtube_info, get_cookie_file_path, test_cookie_health_live
from cookie_manager import (
    read_active_cookies,
    analyze_cookies_health,
    save_cookies_content,
    clear_cookies_file,
    get_active_cookie_path
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(BASE_DIR, "static", "dashboard.html")

app = FastAPI(
    title="YouTube Direct Links Extractor & Cookie Hub API",
    description="API متطور لاستخراج الروابط المباشرة المؤقتة لجميع جودات فيديو اليوتيوب مع إدارة شاملة لكوكيز الدخول بجميع الصيغ (JSON, Netscape) وتشخيص حي.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    url: str = Field(..., description="رابط فيديو اليوتيوب")


class CookieUpdateRequest(BaseModel):
    cookies_text: str = Field(..., description="نص الكوكيز بأي صيغة (JSON أو Netscape أو Header)")
    test_immediately: Optional[bool] = Field(False, description="إجراء فحص حي فوري بعد الحفظ")


class CookieTestRequest(BaseModel):
    url: Optional[str] = Field("https://www.youtube.com/watch?v=dQw4w9WgXcQ", description="رابط فيديو للاختبار")


@app.get("/", tags=["Dashboard & Health"])
def root_endpoint(request: Request):
    """عرض لوحة التحكم عند الفتح في المتصفح، أو إرجاع معلومات الـ API لطلبات JSON."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists(DASHBOARD_FILE):
        return FileResponse(DASHBOARD_FILE, media_type="text/html")

    return {
        "status": "online",
        "service": "YouTube Direct Links Extractor & Cookie Hub API",
        "dashboard": "/dashboard",
        "documentation": "/docs",
        "endpoints": {
            "GET /dashboard": "لوحة التحكم التفاعلية الشاملة",
            "GET /api/cookies/status": "فحص حالة وصلاحية الكوكيز المسجلة",
            "POST /api/cookies/update": "تحديث الكوكيز بأي صيغة (JSON أو Netscape)",
            "POST /api/cookies/test": "فحص حي للكوكيز الحالية",
            "DELETE /api/cookies": "مسح الكوكيز والتحويل لوضع الزائر",
            "POST /api/extract": "استخراج الروابط المباشرة (JSON body)",
            "GET /api/extract": "استخراج الروابط المباشرة (Query param)",
            "GET /api/logs": "سجل العمليات والأخطاء الحية",
            "GET /api/debug": "فحص بيئة السيرفر والأدوات"
        }
    }


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard & Health"])
def get_dashboard():
    """عرض لوحة التحكم التفاعلية المباشرة لإدارة الكوكيز واستخراج الروابط"""
    if os.path.exists(DASHBOARD_FILE):
        return FileResponse(DASHBOARD_FILE, media_type="text/html")
    raise HTTPException(status_code=404, detail="Dashboard file not found.")


# ===================== COOKIES MANAGEMENT ENDPOINTS =====================

@app.get("/api/cookies/status", tags=["Cookie Hub"])
def get_cookie_status():
    """فحص حالة الكوكيز المسجلة على السيرفر وتواريخ انتهائها ومفاتيح المصادقة"""
    cookies, cookie_path = read_active_cookies()
    health = analyze_cookies_health(cookies)
    file_size = os.path.getsize(cookie_path) if cookie_path and os.path.exists(cookie_path) else 0

    return {
        **health,
        "file_path": cookie_path,
        "file_size_bytes": file_size,
    }


@app.post("/api/cookies/update", tags=["Cookie Hub"])
def update_cookies(payload: CookieUpdateRequest):
    """
    تحديث الكوكيز على السيرفر بقبول أي صيغة:
    - مصفوفة JSON من Cookie-Editor أو EditThisCookie
    - أسطر Netscape (ملف cookies.txt)
    - نص ترويسة HTTP (Cookie: ...)
    """
    try:
        result = save_cookies_content(payload.cookies_text)
        test_result = None

        if payload.test_immediately:
            test_result = test_cookie_health_live()

        return {
            "status": "success",
            "message": f"تم حفظ {result['cookies_count']} كوكيز بنجاح وتفعيلها في السيرفر.",
            "detected_format": result["detected_format"],
            "cookies_count": result["cookies_count"],
            "file_path": result["file_path"],
            "file_size_bytes": result["file_size_bytes"],
            "health": result["health"],
            "test_result": test_result
        }
    except Exception as e:
        logger.error(f"Failed to update cookies: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"فشل معالجة وحفظ الكوكيز: {str(e)}"
        )


@app.post("/api/cookies/test", tags=["Cookie Hub"])
def test_cookies_live(payload: Optional[CookieTestRequest] = None):
    """إجراء فحص حي فوري للكوكيز الحالية على فيديو يوتيوب لقياس زمن الاستجابة وصلاحية الجلسة"""
    target_url = (payload.url if payload and payload.url else "https://www.youtube.com/watch?v=dQw4w9WgXcQ").strip()
    return test_cookie_health_live(target_url)


@app.delete("/api/cookies", tags=["Cookie Hub"])
def delete_cookies():
    """مسح ملف الكوكيز الحالي والتحويل الفوري لوضع الزائر (Guest Mode)"""
    success = clear_cookies_file()
    if success:
        return {"status": "success", "message": "تم تفريغ ملف الكوكيز بنجاح والتحويل لوضع الزائر."}
    raise HTTPException(status_code=500, detail="فشل مسح ملف الكوكيز.")


# ===================== DIAGNOSTICS & LOGS ENDPOINTS =====================

@app.get("/api/debug", tags=["Diagnostics"])
def debug_info():
    """فحص تشخيصي شامل للنظام وبيئة التشغيل دون أي انهيار"""
    try:
        import yt_dlp.version
        ytdlp_ver = yt_dlp.version.__version__
    except Exception:
        ytdlp_ver = "unknown"

    try:
        cookie_path = get_cookie_file_path()
        return {
            "status": "ok",
            "yt_dlp_version": ytdlp_ver,
            "python_version": sys.version,
            "cookies_found": cookie_path is not None,
            "cookies_path": cookie_path,
            "cookies_size_bytes": os.path.getsize(cookie_path) if cookie_path and os.path.exists(cookie_path) else 0,
            "node_installed": shutil.which("node") is not None,
            "node_path": shutil.which("node"),
            "ffmpeg_installed": shutil.which("ffmpeg") is not None,
            "ffmpeg_path": shutil.which("ffmpeg"),
            "current_directory": os.getcwd(),
            "environment_cookies_set": bool(os.getenv("YOUTUBE_COOKIES")),
            "files_in_current_dir": [f for f in os.listdir(os.getcwd()) if not f.startswith('.')]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/logs", tags=["Diagnostics"])
def view_logs(raw: bool = Query(False, description="عرض كـ نص خام للنسخ المباشر")):
    """عرض سجلات العمليات والأخطاء الحية المسجلة أثناء فحص الروابط"""
    logs = get_recent_logs()
    if raw:
        text_lines = [f"[{l['timestamp']}] [{l['level']}] [{l['logger']}] {l['message']}" for l in logs]
        return Response(content="\n".join(text_lines), media_type="text/plain; charset=utf-8")
    return {
        "total_records": len(logs),
        "logs": logs
    }


@app.delete("/api/logs", tags=["Diagnostics"])
def delete_logs():
    """مسح سجل العمليات الحية"""
    clear_logs()
    return {"status": "logs cleared"}


# ===================== VIDEO EXTRACTION ENDPOINTS =====================

def handle_extraction(url: str):
    url = url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رابط الفيديو مطلوب.")

    try:
        logger.info(f"Received extraction request for URL: {url}")
        return extract_youtube_info(url)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Extraction failed: {error_msg}")

        detail_msg = f"فشل استخراج الروابط: {error_msg} (يمكنك تحديث الكوكيز عبر /dashboard أو مراجعة /api/logs)"
        if "The page needs to be reloaded" in error_msg:
            detail_msg = "يوتيوب يطلب تحديث الكوكيز (انتهت الجلسة). يرجى لصق كوكيز جديدة عبر لوحة التحكم /dashboard."
        elif "Sign in to confirm" in error_msg or "Please sign in" in error_msg:
            detail_msg = "يوتيوب يطلب تسجيل الدخول لتأكيد عدم وجود روبوت. يرجى تجديد الكوكيز عبر لوحة التحكم /dashboard."

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg
        )


@app.post("/api/extract", tags=["Extractor"])
def extract_post(request_data: ExtractRequest):
    """استخراج الروابط المباشرة المؤقتة لجميع الجودات عبر طلب POST."""
    return handle_extraction(request_data.url)


@app.get("/api/extract", tags=["Extractor"])
def extract_get(url: str = Query(..., description="رابط فيديو اليوتيوب")):
    """استخراج الروابط المباشرة المؤقتة لجميع الجودات عبر طلب GET."""
    return handle_extraction(url)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
