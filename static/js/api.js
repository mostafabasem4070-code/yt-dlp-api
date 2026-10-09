/* ==========================================================================
   API CLIENT, AUTHENTICATION & TOAST NOTIFICATIONS
   YouTube API Hub - Cloud Control Center
   ========================================================================== */

let currentAdminToken = localStorage.getItem('ytdlp_admin_token') || '';

async function apiFetch(endpoint, options = {}) {
    options.headers = options.headers || {};
    
    // تمرير التوكن بكافة الترويسات المدعومة لضمان التوافق التام
    if (currentAdminToken) {
        options.headers['Authorization'] = `Bearer ${currentAdminToken}`;
        options.headers['X-Admin-Token'] = currentAdminToken;
        options.headers['X-Session-Token'] = currentAdminToken;
    }

    // إرسال الكوكيز المحلية مع كل طلب
    options.credentials = 'same-origin';

    try {
        const res = await fetch(endpoint, options);
        if (res.status === 401) {
            lockDashboardUI();
        }
        return res;
    } catch (err) {
        console.error(`API Error on ${endpoint}:`, err);
        throw err;
    }
}

/* ==================== TOAST NOTIFICATIONS ==================== */
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconSvg = type === 'success' 
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color:var(--success); flex-shrink:0;"><polyline points="20 6 9 17 4 12"></polyline></svg>`
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color:var(--danger); flex-shrink:0;"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;

    toast.innerHTML = `
        ${iconSvg}
        <span>${message}</span>
    `;
    
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(15px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 320);
    }, 3800);
}

/* ==================== AUTHENTICATION MANAGEMENT ==================== */
function lockDashboardUI() {
    const overlay = document.getElementById('authLockOverlay');
    if (overlay) {
        overlay.classList.remove('unlocked');
    }
    currentAdminToken = '';
    localStorage.removeItem('ytdlp_admin_token');

    // إيقاف مؤقتات المراقبة عند القفل
    if (window.stopLiveTimers) {
        window.stopLiveTimers();
    }
}

function unlockDashboardUI(token) {
    currentAdminToken = token;
    localStorage.setItem('ytdlp_admin_token', token);
    const overlay = document.getElementById('authLockOverlay');
    if (overlay) {
        overlay.classList.add('unlocked');
    }
    
    // تشغيل وتحميل كافة بيانات اللوحة
    if (window.initDashboardData) {
        window.initDashboardData();
    }
}

async function checkAuthOnStartup() {
    try {
        const res = await apiFetch('/api/auth/status');
        const data = await res.json();
        if (data.authenticated) {
            unlockDashboardUI(currentAdminToken || 'cookie_session');
        } else {
            lockDashboardUI();
        }
    } catch (e) {
        lockDashboardUI();
    }
}

async function handleLoginSubmit(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('adminPasswordInput');
    const btn = document.getElementById('btnLoginSubmit');
    const password = input.value.trim();

    if (!password) {
        showToast('يرجى كتابة كلمة المرور.', 'error');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span>جاري التحقق...</span>';

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: password })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            showToast('تم تسجيل الدخول بنجاح! أهلاً بك.');
            input.value = '';
            unlockDashboardUI(data.token);
        } else {
            showToast(data.detail || 'كلمة المرور غير صحيحة.', 'error');
        }
    } catch (err) {
        showToast('تعذر الاتصال بالخادم.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>دخول لوحة التحكم</span>';
    }
}

async function handleLogout() {
    try {
        await apiFetch('/api/auth/logout', { method: 'POST' });
    } catch (e) { }
    showToast('تم تسجيل الخروج بنجاح.');
    lockDashboardUI();
}

window.apiFetch = apiFetch;
window.showToast = showToast;
window.lockDashboardUI = lockDashboardUI;
window.unlockDashboardUI = unlockDashboardUI;
window.checkAuthOnStartup = checkAuthOnStartup;
window.handleLoginSubmit = handleLoginSubmit;
window.handleLogout = handleLogout;
