import logging
from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional

# تخزين آخر 500 رسالة لوج في الذاكرة للوصول إليها عبر لوحة التحكم
_LOG_BUFFER = deque(maxlen=500)

class InMemoryLogHandler(logging.Handler):
    def emit(self, record):
        try:
            # استخراج الرسالة بدون تكرار الترويسات
            try:
                raw_msg = record.getMessage()
            except Exception:
                raw_msg = str(record.msg)
            
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "message": raw_msg
            }
            _LOG_BUFFER.append(entry)
        except Exception:
            self.handleError(record)

# إعداد الـ Handler العام
memory_handler = InMemoryLogHandler()
memory_handler.setLevel(logging.INFO)

def setup_logging_capture():
    """ربط مستمع السجلات بجميع المحركات والخوادم لضمان ظهور كافة العمليات في اللوحة"""
    root_logger = logging.getLogger()
    if memory_handler not in root_logger.handlers:
        root_logger.addHandler(memory_handler)
    root_logger.setLevel(logging.INFO)

    # التقاط سجلات Uvicorn و FastAPI ومحركات النظام الفرعية
    loggers_to_attach = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "main",
        "youtube_service",
        "stream_service",
        "security_manager",
        "cookie_manager",
        "health_monitor",
        "updater_service"
    ]
    for name in loggers_to_attach:
        l = logging.getLogger(name)
        if memory_handler not in l.handlers:
            l.addHandler(memory_handler)
        l.setLevel(logging.INFO)

# تفعيل الربط فوراً عند الاستيراد
setup_logging_capture()

class YtDlpLogger:
    """مستمع خاص لسجلات yt-dlp لتسجيل كل ما يحدث في الفحص الداخلي"""
    def debug(self, msg: str):
        if not msg.startswith('[debug]'):
            _LOG_BUFFER.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "DEBUG",
                "logger": "yt-dlp",
                "message": msg
            })
            logging.debug(f"[yt-dlp] {msg}")

    def info(self, msg: str):
        _LOG_BUFFER.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "logger": "yt-dlp",
            "message": msg
        })
        logging.info(f"[yt-dlp] {msg}")

    def warning(self, msg: str):
        _LOG_BUFFER.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "WARNING",
            "logger": "yt-dlp",
            "message": msg
        })
        logging.warning(f"[yt-dlp] {msg}")

    def error(self, msg: str):
        _LOG_BUFFER.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "ERROR",
            "logger": "yt-dlp",
            "message": msg
        })
        logging.error(f"[yt-dlp] {msg}")

def get_recent_logs(limit: int = 150, level: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """الحصول على السجلات الأخيرة مع خيارات الفلترة المتقدمة"""
    logs = list(_LOG_BUFFER)
    if level and level.upper() != "ALL":
        target = level.upper()
        logs = [l for l in logs if l.get("level") == target]
    if search:
        s = search.lower()
        logs = [l for l in logs if s in l.get("message", "").lower() or s in l.get("logger", "").lower()]
    
    if limit > 0:
        logs = logs[-limit:]
    return logs

def clear_logs():
    """مسح الذاكرة المؤقتة للسجلات"""
    _LOG_BUFFER.clear()
    _LOG_BUFFER.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "logger": "system",
        "message": "تم تفريغ سجل العمليات بنجاح."
    })
