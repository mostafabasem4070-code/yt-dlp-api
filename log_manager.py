import logging
from collections import deque
from datetime import datetime
from typing import List, Dict, Any

# تخزين آخر 200 رسالة لوج في الذاكرة للوصول إليها عبر المتصفح
_LOG_BUFFER = deque(maxlen=200)

class InMemoryLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            _LOG_BUFFER.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "message": msg
            })
        except Exception:
            self.handleError(record)

# إعداد الـ Handler العام
memory_handler = InMemoryLogHandler()
memory_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(memory_handler)
logging.getLogger().setLevel(logging.INFO)

class YtDlpLogger:
    """مستمع خاص لسجلات yt-dlp لتسجيل كل ما يحدث في الفحص الداخلي"""
    def debug(self, msg):
        if not msg.startswith('[debug]'):
            _LOG_BUFFER.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "DEBUG",
                "logger": "yt-dlp",
                "message": msg
            })
            logging.debug(f"[yt-dlp] {msg}")

    def info(self, msg):
        _LOG_BUFFER.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "logger": "yt-dlp",
            "message": msg
        })
        logging.info(f"[yt-dlp] {msg}")

    def warning(self, msg):
        _LOG_BUFFER.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "WARNING",
            "logger": "yt-dlp",
            "message": msg
        })
        logging.warning(f"[yt-dlp] {msg}")

    def error(self, msg):
        _LOG_BUFFER.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "ERROR",
            "logger": "yt-dlp",
            "message": msg
        })
        logging.error(f"[yt-dlp] {msg}")

def get_recent_logs() -> List[Dict[str, Any]]:
    return list(_LOG_BUFFER)

def clear_logs():
    _LOG_BUFFER.clear()
