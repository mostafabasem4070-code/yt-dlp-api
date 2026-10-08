import os
import shutil
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from log_manager import get_recent_logs, clear_logs
from youtube_service import extract_youtube_info, get_cookie_file_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Direct Links Extractor API",
    description="API لاستخراج الروابط المباشرة المؤقتة لجميع جودات فيديو اليوتيوب عبر yt-dlp مع سجل أخطاء وتشخيص حي.",
    version="1.1.0"
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

@app.get("/", tags=["Health"])
def health_check():
    """فحص حالة السيرفر ودليل استخدام الـ API"""
    return {
        "status": "online",
        "service": "YouTube Direct Links Extractor API",
        "documentation": "/docs",
        "endpoints": {
            "POST /api/extract": "إرسال رابط الفيديو عبر JSON body: {'url': '...'}",
            "GET /api/extract": "إرسال رابط الفيديو عبر Query param: /api/extract?url=...",
            "GET /api/logs": "عرض سجل العمليات والأخطاء الحية من الذاكرة",
            "GET /api/debug": "فحص حالة الكوكيز وأدوات النظام (Node, FFMPEG) على السيرفر"
        }
    }

@app.get("/api/debug", tags=["Diagnostics"])
def debug_info():
    """فحص تشخيصي شامل للنظام وبيئة التشغيل دون أي انهيار"""
    try:
        cookie_path = get_cookie_file_path()
        return {
            "status": "ok",
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
        
        # رسائل مساعدة واضحة مع إشارة إلى رابط اللوج للتشخيص
        detail_msg = f"فشل استخراج الروابط: {error_msg} (راجع /api/logs لمعرفة تفاصيل الخطأ)"
        if "The page needs to be reloaded" in error_msg:
            detail_msg = "يوتيوب يطلب إعادة تحميل الصفحة أو تحديث الكوكيز. راجع /api/logs لتفاصيل العملية."
        elif "Sign in to confirm" in error_msg or "Please sign in" in error_msg:
            detail_msg = "يوتيوب يطلب تسجيل الدخول لتأكيد عدم وجود روبوت. تأكد من صحة cookies.txt أو متغير YOUTUBE_COOKIES."

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
