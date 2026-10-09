import os
import json
import time
import hmac
import hashlib
import secrets
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("security_manager")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "security_config.json")

# In-memory session store: token -> { "created_at": float, "expires_at": float }
_ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """تشفير كلمة المرور باستخدام SHA-256 مع Salt عشوائي آمن"""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hashed, salt


def _load_config() -> Dict[str, Any]:
    """تحميل إعدادات الأمان والدومينات من الملف أو إنشاء الإعدادات الافتراضية"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load security config: {e}")

    # القيم الافتراضية مع قراءة متغيرات البيئة إن وجدت
    env_password = os.getenv("ADMIN_PASSWORD") or os.getenv("DASHBOARD_PASSWORD") or "admin2026!"
    hashed_pwd, salt = _hash_password(env_password)

    env_domains_raw = os.getenv("ALLOWED_DOMAINS", "*")
    allowed_domains = [d.strip() for d in env_domains_raw.split(",") if d.strip()]
    if not allowed_domains:
        allowed_domains = ["*"]

    env_strict = os.getenv("STRICT_DOMAIN_CHECK", "false").lower() in ("true", "1", "yes")
    default_api_key = os.getenv("API_KEY") or f"sec_{secrets.token_hex(16)}"

    cfg = {
        "admin_password_hash": hashed_pwd,
        "salt": salt,
        "allowed_domains": allowed_domains,
        "strict_mode": env_strict,
        "api_key": default_api_key,
        "updated_at": int(time.time())
    }
    _save_config(cfg)
    return cfg


def _save_config(config: Dict[str, Any]) -> bool:
    """حفظ إعدادات الأمان في ملف JSON دائم"""
    try:
        config["updated_at"] = int(time.time())
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save security config: {e}")
        return False


# ===================== AUTHENTICATION =====================

def verify_admin_password(password: str) -> bool:
    """التحقق من صحة كلمة مرور الإدارة"""
    cfg = _load_config()
    stored_hash = cfg.get("admin_password_hash", "")
    salt = cfg.get("salt", "")

    # فحص أيضاً كلمة المرور من متغير البيئة مباشرة إن تغيرت في Railway
    env_pwd = os.getenv("ADMIN_PASSWORD") or os.getenv("DASHBOARD_PASSWORD")
    if env_pwd and password == env_pwd:
        return True

    test_hash, _ = _hash_password(password, salt)
    return hmac.compare_digest(stored_hash, test_hash)


def change_admin_password(old_password: str, new_password: str) -> Tuple[bool, str]:
    """تغيير كلمة مرور الإدارة بعد التحقق من القديمة"""
    if not verify_admin_password(old_password):
        return False, "كلمة المرور الحالية غير صحيحة."
    
    if len(new_password) < 6:
        return False, "كلمة المرور الجديدة يجب أن تتكون من 6 أحرف على الأقل."

    cfg = _load_config()
    hashed_pwd, salt = _hash_password(new_password)
    cfg["admin_password_hash"] = hashed_pwd
    cfg["salt"] = salt
    _save_config(cfg)
    
    # تفريغ الجلسات الحالية لإجبار إعادة تسجيل الدخول
    _ACTIVE_SESSIONS.clear()
    return True, "تم تغيير كلمة المرور بنجاح."


def create_session_token() -> str:
    """إنشاء جلسة دخول مشفرة صالحة لمدة 7 أيام"""
    token = secrets.token_urlsafe(36)
    now = time.time()
    _ACTIVE_SESSIONS[token] = {
        "created_at": now,
        "expires_at": now + SESSION_TTL_SECONDS
    }
    return token


def validate_session_token(token: Optional[str]) -> bool:
    """التحقق من صحة وصلاحية جلسة الدخول"""
    if not token:
        return False

    session = _ACTIVE_SESSIONS.get(token)
    if not session:
        return False

    if time.time() > session.get("expires_at", 0):
        _ACTIVE_SESSIONS.pop(token, None)
        return False

    return True


def revoke_session_token(token: str) -> None:
    """تسجيل الخروج وإلغاء الجلسة"""
    _ACTIVE_SESSIONS.pop(token, None)


# ===================== DOMAIN WHITELIST & ORIGIN VALIDATION =====================

def normalize_domain(domain_str: str) -> str:
    """استخراج النطاق الصافي بدون بروتوكول أو منافذ أو مسارات"""
    raw = domain_str.strip().lower()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        return (parsed.hostname or "").lower()
    # إزالة أي مسار أو منفذ
    raw = raw.split("/")[0].split(":")[0]
    return raw


def get_security_settings() -> Dict[str, Any]:
    """الحصول على كافة إعدادات الأمان والدومينات المصرح لها (دون كشف التجزئة)"""
    cfg = _load_config()
    return {
        "allowed_domains": cfg.get("allowed_domains", ["*"]),
        "strict_mode": cfg.get("strict_mode", False),
        "api_key": cfg.get("api_key", ""),
        "updated_at": cfg.get("updated_at", 0),
        "active_sessions_count": len(_ACTIVE_SESSIONS)
    }


def add_allowed_domain(domain: str) -> Tuple[bool, str, List[str]]:
    """إضافة دومين جديد إلى قائمة الدومينات المصرح لها"""
    clean = normalize_domain(domain)
    if not clean:
        return False, "اسم الدومين غير صالح.", []

    cfg = _load_config()
    domains = cfg.get("allowed_domains", [])

    if clean in domains:
        return True, "الدومين موجود بالفعل في القائمة.", domains

    domains.append(clean)
    cfg["allowed_domains"] = domains
    _save_config(cfg)
    return True, f"تمت إضافة الدومين {clean} بنجاح.", domains


def remove_allowed_domain(domain: str) -> Tuple[bool, str, List[str]]:
    """حذف دومين من قائمة الدومينات المصرح لها"""
    clean = normalize_domain(domain)
    cfg = _load_config()
    domains = cfg.get("allowed_domains", [])

    if clean not in domains and domain not in domains:
        return False, "الدومين غير موجود في القائمة.", domains

    domains = [d for d in domains if d != clean and d != domain]
    cfg["allowed_domains"] = domains
    _save_config(cfg)
    return True, f"تم حذف الدومين {clean} بنجاح.", domains


def update_security_preferences(strict_mode: bool, allowed_domains: Optional[List[str]] = None, generate_new_api_key: bool = False) -> Dict[str, Any]:
    """تحديث خيارات الأمان ووضع الفحص الصارم ومفتاح الـ API"""
    cfg = _load_config()
    cfg["strict_mode"] = bool(strict_mode)

    if allowed_domains is not None:
        cleaned = [normalize_domain(d) for d in allowed_domains if normalize_domain(d)]
        cfg["allowed_domains"] = cleaned

    if generate_new_api_key:
        cfg["api_key"] = f"sec_{secrets.token_hex(16)}"

    _save_config(cfg)
    return get_security_settings()


def is_request_authorized(
    origin: Optional[str] = None,
    referer: Optional[str] = None,
    host: Optional[str] = None,
    api_key_header: Optional[str] = None,
    auth_token: Optional[str] = None
) -> Tuple[bool, str]:
    """
    التحقق مما إذا كان الطلب مصرحاً له:
    1. إذا كانت الجلسة مسجلة كمسؤول (Dashboard Auth Token) -> مصرح دائماً.
    2. إذا تم تمرير API Key صحيح (من Laravel عبر X-API-Key) -> مصرح دائماً.
    3. إذا لم يكن الوضع الصارم مفعلاً وكانت قائمة الدومينات تحتوي على '*' -> مصرح.
    4. إذا كان الوضع الصارم مفعلاً، يتم فحص Origin أو Referer ومطابقته بالقائمة.
    """
    # 1. فحص توكن جلسة المشرف
    if auth_token and validate_session_token(auth_token):
        return True, "Authorized via Admin Session"

    cfg = _load_config()
    expected_api_key = cfg.get("api_key")

    # 2. فحص مفتاح الـ API المرسل من السيرفر (Laravel أو غيره)
    if expected_api_key and api_key_header and hmac.compare_digest(expected_api_key, api_key_header):
        return True, "Authorized via API Key"

    allowed_domains = cfg.get("allowed_domains", ["*"])
    strict_mode = cfg.get("strict_mode", False)

    # إذا كان مسموح للجميع ولم يتم تفعيل الوضع الصارم
    if "*" in allowed_domains and not strict_mode:
        return True, "Open access (Wildcard allowed)"

    # استخراج الدومين من ترويسة Origin أو Referer
    caller_domain = ""
    if origin:
        caller_domain = normalize_domain(origin)
    elif referer:
        caller_domain = normalize_domain(referer)

    # فحص الدومين في القائمة المسموحة
    if caller_domain:
        for allowed in allowed_domains:
            allowed_clean = normalize_domain(allowed)
            if allowed_clean == "*":
                return True, "Wildcard match"
            if caller_domain == allowed_clean or caller_domain.endswith("." + allowed_clean):
                return True, f"Domain allowed: {caller_domain}"

    # إذا كان الطلب من السيرفر نفسه (Localhost / Railway Host)
    if host:
        host_clean = normalize_domain(host)
        if host_clean in ("localhost", "127.0.0.1") or (caller_domain in ("localhost", "127.0.0.1")):
            return True, "Localhost allowed"

    # في حال فشل التطابق
    if not caller_domain:
        return False, "طلب غير مصرح به: لم يتم إرسال ترويسة Origin أو مفتاح API صالح."

    return False, f"طلب مرفوض: الدومين '{caller_domain}' غير مدرج في قائمة الدومينات المصرح لها."
