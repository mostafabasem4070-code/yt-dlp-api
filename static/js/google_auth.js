/* ==========================================================================
   GOOGLE AUTH PANEL - Browser-based Cookie Extraction
   YouTube API Hub - Cloud Control Center
   ========================================================================== */

async function loadGoogleAuthStatus() {
    try {
        const res = await apiFetch('/api/auth/google/status');
        if (!res.ok) return;
        const data = await res.json();
        renderGoogleAuthPanel(data);
    } catch (err) {
        console.error('Failed to load Google Auth status:', err);
    }
}

function renderGoogleAuthPanel(data) {
    const panel = document.getElementById('googleAuthStatusPanel');
    if (!panel) return;

    const session = data.session || {};
    const playwrightOk = data.playwright_installed;
    const status = session.status || 'idle';

    const statusMap = {
        idle:          { label: 'جاهز للبدء',            color: 'var(--text-muted)',    icon: '⏳' },
        running:       { label: 'يُشغّل المتصفح...',     color: 'var(--warning)',       icon: '🔄' },
        waiting_login: { label: 'في انتظار تسجيل الدخول', color: 'var(--accent-cyan)', icon: '🔐' },
        extracting:    { label: 'يستخرج الكوكيز...',     color: 'var(--accent-purple)', icon: '📦' },
        done:          { label: 'تم بنجاح!',              color: 'var(--success)',       icon: '✅' },
        error:         { label: 'خطأ',                    color: 'var(--danger)',        icon: '❌' },
        timeout:       { label: 'انتهت المهلة',           color: 'var(--warning)',       icon: '⌛' },
    };

    const s = statusMap[status] || statusMap['idle'];
    const isActive = ['running', 'waiting_login', 'extracting'].includes(status);
    const isDone = status === 'done';
    const isError = ['error', 'timeout'].includes(status);

    panel.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <span style="font-size:1.4rem;">${s.icon}</span>
            <div>
                <div style="font-size:0.85rem; font-weight:700; color:${s.color};">${s.label}</div>
                <div style="font-size:0.8rem; color:var(--text-muted); margin-top:2px;">${session.message || ''}</div>
            </div>
            ${isActive ? `<div class="spinner" style="margin-right:auto;"></div>` : ''}
        </div>

        ${isDone ? `
        <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:8px; padding:12px; margin-bottom:12px; font-size:0.85rem; color:var(--success);">
            <strong>تم استخراج الكوكيز بنجاح!</strong><br>
            عدد الكوكيز المحفوظة: <strong>${session.cookies_count}</strong>
        </div>
        ` : ''}

        ${isError ? `
        <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); border-radius:8px; padding:10px; margin-bottom:12px; font-size:0.82rem; color:var(--danger);">
            ${session.error || 'حدث خطأ غير متوقع'}
        </div>
        ` : ''}

        ${!playwrightOk ? `
        <div style="background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.3); border-radius:8px; padding:10px; margin-bottom:12px; font-size:0.82rem; color:var(--warning);">
            ⚠️ مكتبة Playwright غير مثبتة. شغّل على السيرفر:<br>
            <code style="font-family:var(--font-mono); font-size:0.78rem; display:block; margin-top:6px; background:rgba(0,0,0,0.3); padding:6px; border-radius:4px;">pip install playwright && playwright install chromium</code>
        </div>
        ` : ''}

        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            ${!isActive ? `
            <button id="btnGoogleLogin" class="btn-action success" onclick="startGoogleLogin()" ${!playwrightOk ? 'disabled' : ''}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v4l3 3"></path></svg>
                <span>بدء تسجيل الدخول بمتصفح جوجل</span>
            </button>
            ` : `
            <button class="btn-action danger" onclick="cancelGoogleLogin()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                <span>إلغاء الجلسة</span>
            </button>
            `}
            ${isDone ? `
            <button class="btn-action cyan" onclick="loadCookieStatus(); loadGoogleAuthStatus();">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                <span>تحديث حالة الكوكيز</span>
            </button>
            ` : ''}
        </div>
    `;
}

async function startGoogleLogin() {
    const btn = document.getElementById('btnGoogleLogin');
    if (btn) { btn.disabled = true; }

    try {
        const res = await apiFetch('/api/auth/google/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timeout_minutes: 10, headless: false })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            showToast('تم فتح المتصفح على السيرفر. أكمل تسجيل الدخول.', 'success');
            // بدء الـ polling كل 3 ثوانٍ
            startGoogleAuthPolling();
        } else {
            showToast(data.message || 'فشل بدء الجلسة', 'error');
            loadGoogleAuthStatus();
        }
    } catch (e) {
        showToast('تعذر الاتصال بالخادم', 'error');
        if (btn) { btn.disabled = false; }
    }
}

async function cancelGoogleLogin() {
    try {
        const res = await apiFetch('/api/auth/google/cancel', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'تم الإلغاء', 'warning');
        stopGoogleAuthPolling();
        loadGoogleAuthStatus();
    } catch (e) {
        showToast('تعذر الاتصال', 'error');
    }
}

// ===== Polling System =====
let _googleAuthPollTimer = null;

function startGoogleAuthPolling() {
    stopGoogleAuthPolling();
    _googleAuthPollTimer = setInterval(pollGoogleAuthSession, 3000);
}

function stopGoogleAuthPolling() {
    if (_googleAuthPollTimer) {
        clearInterval(_googleAuthPollTimer);
        _googleAuthPollTimer = null;
    }
}

async function pollGoogleAuthSession() {
    try {
        const res = await apiFetch('/api/auth/google/poll');
        if (!res.ok) return;
        const data = await res.json();
        const session = data.session || {};
        const status = session.status;

        // تحديث الواجهة
        renderGoogleAuthPanel({ ...data, playwright_installed: true });

        // إيقاف الـ polling عند الانتهاء
        if (['done', 'error', 'timeout', 'idle'].includes(status)) {
            stopGoogleAuthPolling();

            if (status === 'done') {
                showToast(`تم استخراج ${session.cookies_count} كوكي بنجاح من نفس الـ IP!`, 'success');
                // تحديث عداد الكوكيز في الشريط الجانبي فوراً
                setTimeout(() => { loadCookieStatus(); }, 500);
            } else if (status === 'error' || status === 'timeout') {
                showToast(session.message || 'انتهت جلسة تسجيل الدخول', 'warning');
            }
        }
    } catch (e) {
        console.error('Google auth poll error:', e);
    }
}

// تصدير الدوال للنطاق العام
window.loadGoogleAuthStatus = loadGoogleAuthStatus;
window.startGoogleLogin = startGoogleLogin;
window.cancelGoogleLogin = cancelGoogleLogin;
window.startGoogleAuthPolling = startGoogleAuthPolling;
window.stopGoogleAuthPolling = stopGoogleAuthPolling;
