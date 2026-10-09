/* ==========================================================================
   SECURITY, DOMAIN FIREWALL & API KEY MANAGEMENT
   YouTube API Hub - Cloud Control Center
   ========================================================================== */

async function loadSecuritySettings() {
    try {
        const res = await apiFetch('/api/security/settings');
        if (!res.ok) return;
        const data = await res.json();
        const domains = data.allowed_domains || ['*'];

        // 1. تحديث وضع الفحص الصارم
        const strictToggle = document.getElementById('strictModeToggle');
        if (strictToggle) strictToggle.checked = !!data.strict_mode;

        // 2. تحديث الشارات وعدد الدومينات
        const badge = document.getElementById('domainCountBadge');
        if (badge) badge.textContent = `${domains.length}`;

        // 3. عرض مفتاح الـ API
        const apiKeyEl = document.getElementById('currentApiKeyDisplay');
        if (apiKeyEl) {
            apiKeyEl.textContent = data.api_key || 'غير متوفر';
        }

        renderDomainChips(domains);

    } catch (err) {
        console.error('Failed to load security settings:', err);
    }
}

function renderDomainChips(domains) {
    const container = document.getElementById('domainChipsContainer');
    if (!container) return;
    container.innerHTML = '';

    if (!domains || domains.length === 0) {
        container.innerHTML = '<span style="color:var(--text-muted); font-size:0.85rem;">لا توجد دومينات مضافة.</span>';
        return;
    }

    domains.forEach(d => {
        const chip = document.createElement('div');
        chip.className = `domain-chip ${d === '*' ? 'wildcard' : ''}`;
        chip.innerHTML = `
            <span>${d === '*' ? '★ * (الجميع مسموح)' : d}</span>
            <button class="btn-remove-chip" onclick="handleRemoveDomain('${d}')" title="حذف">&times;</button>
        `;
        container.appendChild(chip);
    });
}

async function handleAddDomain() {
    const input = document.getElementById('newDomainInput');
    const domain = input.value.trim();
    if (!domain) {
        showToast('يرجى كتابة اسم الدومين أولاً.', 'error');
        return;
    }

    try {
        const res = await apiFetch('/api/security/domains/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain: domain })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message);
            input.value = '';
            renderDomainChips(data.allowed_domains);
            loadSecuritySettings();
            if (window.loadOverview) loadOverview();
        } else {
            showToast(data.detail || 'فشل إضافة الدومين.', 'error');
        }
    } catch (e) {
        showToast('تعذر الاتصال بالخادم.', 'error');
    }
}

async function handleRemoveDomain(domain) {
    if (!confirm(`هل تريد بالتأكيد إزالة الدومين (${domain}) من قائمة المصرح لهم؟`)) return;

    try {
        const res = await apiFetch('/api/security/domains/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain: domain })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message);
            renderDomainChips(data.allowed_domains);
            loadSecuritySettings();
            if (window.loadOverview) loadOverview();
        } else {
            showToast(data.detail || 'فشل حذف الدومين.', 'error');
        }
    } catch (e) {
        showToast('تعذر الاتصال بالخادم.', 'error');
    }
}

async function handleToggleStrict(checked) {
    try {
        const res = await apiFetch('/api/security/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ strict_mode: checked })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(checked ? 'تم تفعيل وضع التحقق الصارم من الدومينات!' : 'تم تعطيل وضع التحقق الصارم.');
            loadSecuritySettings();
            if (window.loadOverview) loadOverview();
        } else {
            showToast(data.detail || 'فشل حفظ الإعدادات.', 'error');
        }
    } catch (e) {
        showToast('فشل تعديل الوضع الصارم.', 'error');
    }
}

async function copyApiKey() {
    const el = document.getElementById('currentApiKeyDisplay');
    const text = el ? (el.innerText || el.textContent || '').trim() : '';
    if (!text || text === 'غير متوفر') {
        showToast('مفتاح الـ API غير متوفر للنسخ.', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(text);
        showToast('تم نسخ مفتاح API بنجاح إلى الحافظة!');
    } catch (e) {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('تم نسخ مفتاح API للحافظة!');
    }
}

async function handleRegenerateApiKey() {
    if (!confirm('تنبيه هام: توليد مفتاح جديد سيعطل المفتاح القديم، ويتطلب منك تحديث متغير YTDLP_API_KEY في ملف .env لمنصة Laravel فوراً. هل تريد المتابعة؟')) {
        return;
    }

    try {
        const res = await apiFetch('/api/security/api-key/regenerate', { method: 'POST' });
        const data = await res.json();
        if (res.ok && data.success) {
            showToast(data.message);
            loadSecuritySettings();
        } else {
            showToast(data.detail || 'فشل توليد المفتاح.', 'error');
        }
    } catch (e) {
        showToast('تعذر الاتصال بالخادم.', 'error');
    }
}

async function handleTestDomain() {
    const input = document.getElementById('testDomainInput');
    const domain = input.value.trim();
    const resultBox = document.getElementById('testDomainResult');

    if (!domain) {
        showToast('يرجى وضع الدومين أو الرابط للاختبار.', 'error');
        return;
    }

    try {
        const res = await apiFetch('/api/security/domains/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain: domain })
        });
        const data = await res.json();

        resultBox.style.display = 'block';
        if (data.authorized) {
            resultBox.className = 'card';
            resultBox.style.borderColor = 'var(--success)';
            resultBox.style.backgroundColor = 'rgba(16, 185, 129, 0.08)';
            resultBox.innerHTML = `
                <div style="display:flex; align-items:center; gap:10px; color:var(--success); font-weight:700;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    <span>دومين مصرح له ومقبول!</span>
                </div>
                <div style="font-size:0.85rem; color:var(--text-main); margin-top:6px;">${data.reason}</div>
            `;
        } else {
            resultBox.className = 'card';
            resultBox.style.borderColor = 'var(--danger)';
            resultBox.style.backgroundColor = 'rgba(239, 68, 68, 0.08)';
            resultBox.innerHTML = `
                <div style="display:flex; align-items:center; gap:10px; color:var(--danger); font-weight:700;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                    <span>طلب مرفوض ومحظور!</span>
                </div>
                <div style="font-size:0.85rem; color:var(--text-main); margin-top:6px;">${data.reason}</div>
            `;
        }
    } catch (e) {
        showToast('فشل إجراء فحص الدومين.', 'error');
    }
}

async function handleChangePassword(e) {
    if (e) e.preventDefault();
    const curPwd = document.getElementById('curPasswordInput').value;
    const newPwd = document.getElementById('newPasswordInput').value;
    const confirmPwd = document.getElementById('confirmPasswordInput').value;

    if (newPwd !== confirmPwd) {
        showToast('كلمة المرور الجديدة غير متطابقة.', 'error');
        return;
    }

    try {
        const res = await apiFetch('/api/security/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: curPwd, new_password: newPwd })
        });
        const data = await res.json();
        if (res.ok) {
            showToast('تم تغيير كلمة المرور بنجاح! يرجى الدخول بكلمة المرور الجديدة.');
            document.getElementById('changePasswordForm').reset();
            lockDashboardUI();
        } else {
            showToast(data.detail || 'فشل تغيير كلمة المرور.', 'error');
        }
    } catch (e) {
        showToast('تعذر الاتصال بالخادم.', 'error');
    }
}

window.loadSecuritySettings = loadSecuritySettings;
window.handleAddDomain = handleAddDomain;
window.handleRemoveDomain = handleRemoveDomain;
window.handleToggleStrict = handleToggleStrict;
window.copyApiKey = copyApiKey;
window.handleRegenerateApiKey = handleRegenerateApiKey;
window.handleTestDomain = handleTestDomain;
window.handleChangePassword = handleChangePassword;
