/* ==========================================================================
   OVERVIEW, SYSTEM HEALTH & DIAGNOSTIC PROBES
   YouTube API Hub - Cloud Control Center
   ========================================================================== */

async function loadOverview() {
    try {
        const res = await apiFetch('/api/monitor/health');
        if (!res.ok) return;
        const data = await res.json();

        // 1. JS Runtime Engine Card
        const hasDeno = data.components?.deno?.installed;
        const hasNode = data.components?.node?.installed;
        const jsEl = document.getElementById('statJsRuntime');
        if (jsEl) {
            if (hasDeno && hasNode) {
                jsEl.textContent = 'Deno & Node ✓';
                jsEl.style.color = 'var(--success)';
            } else if (hasDeno) {
                jsEl.textContent = 'Deno Engine ✓';
                jsEl.style.color = 'var(--accent-cyan)';
            } else if (hasNode) {
                jsEl.textContent = 'Node.js Engine ✓';
                jsEl.style.color = 'var(--accent-cyan)';
            } else {
                jsEl.textContent = 'غير متوفر ✗';
                jsEl.style.color = 'var(--danger)';
            }
        }

        // 2. yt-dlp Version Card
        const ytVer = data.components?.ytdlp?.current_version || '2024.12+';
        const ytEl = document.getElementById('statYtVersion');
        const ytSideEl = document.getElementById('sideYtVersion');
        if (ytEl) ytEl.textContent = ytVer;
        if (ytSideEl) ytSideEl.textContent = `v${ytVer}`;

        // 3. Cookies Status Card (مع إبراز مدة الصلاحية بوضوح تام!)
        const cookieData = data.components?.cookies || {};
        const stateEl = document.getElementById('statCookieState');
        const cookieSubtext = document.getElementById('statCookieSubtext');
        const sideCookieBadge = document.getElementById('sideCookieBadge');

        if (sideCookieBadge) {
            sideCookieBadge.textContent = `${cookieData.total_cookies || 0} كوكي`;
        }

        if (stateEl) {
            if (cookieData.status === 'healthy' || cookieData.has_auth) {
                const days = cookieData.days_until_expiry || 0;
                const expiryText = cookieData.expiry_countdown && cookieData.expiry_countdown !== '--' 
                    ? cookieData.expiry_countdown 
                    : `${days} يوم`;
                stateEl.textContent = `نشطة ومسجلة (${cookieData.total_cookies || 0})`;
                stateEl.style.color = 'var(--success)';
                if (cookieSubtext) {
                    cookieSubtext.innerHTML = `صلاحية الجلسة: <strong style="color:var(--text-main); font-family:var(--font-mono);">${expiryText}</strong>`;
                }
            } else if (cookieData.status === 'warning') {
                stateEl.textContent = `وضع الزائر (${cookieData.total_cookies || 0})`;
                stateEl.style.color = 'var(--accent-cyan)';
                if (cookieSubtext) {
                    cookieSubtext.textContent = 'تعمل بدون تسجيل دخول حساب';
                }
            } else if (cookieData.status === 'critical') {
                stateEl.textContent = 'منتهية الصلاحية';
                stateEl.style.color = 'var(--danger)';
                if (cookieSubtext) {
                    cookieSubtext.textContent = 'يلزم تجديد الكوكيز فوراً';
                }
            } else {
                stateEl.textContent = 'وضع الزائر (Guest)';
                stateEl.style.color = 'var(--text-muted)';
                if (cookieSubtext) {
                    cookieSubtext.textContent = 'لا توجد كوكيز مسجلة';
                }
            }
        }

        // 4. Domains Firewall Status Card
        const secData = data.components?.security_engine || {};
        const domainsEl = document.getElementById('statDomainsCount');
        const domainsSub = document.getElementById('statDomainsSubtext');
        if (domainsEl) {
            const isStrict = secData.strict_mode;
            const count = secData.allowed_domains_count || 0;
            if (secData.badge && secData.badge.includes('*')) {
                domainsEl.textContent = '* (مفتوح للجميع)';
                domainsEl.style.color = 'var(--warning)';
                if (domainsSub) domainsSub.textContent = isStrict ? 'الوضع الصارم مفعل' : 'الوضع المفتوح';
            } else {
                domainsEl.textContent = `${count} دومين مصرح`;
                domainsEl.style.color = 'var(--accent-cyan)';
                if (domainsSub) domainsSub.textContent = isStrict ? 'الوضع الصارم مفعل (محمي)' : 'الوضع المرن';
            }
        }

        // 5. Update Quick Component Counters
        if (data.summary) {
            const sm = data.summary;
            const quickRun = document.getElementById('quickCompRunning');
            const quickUp = document.getElementById('quickCompUpdate');
            const quickStop = document.getElementById('quickCompStopped');
            const quickPct = document.getElementById('quickCompPercent');

            if (quickRun) quickRun.textContent = `${sm.running} تعمل`;
            if (quickUp) quickUp.textContent = `${sm.needs_update} يتوفر تحديث`;
            if (quickStop) quickStop.textContent = `${sm.stopped} متوقفة`;
            if (quickPct) quickPct.textContent = `${sm.health_percentage}%`;

            const sideCompBadge = document.getElementById('sideCompBadge');
            if (sideCompBadge) sideCompBadge.textContent = `${sm.running}/${sm.total} تعمل`;

            const serverBadge = document.getElementById('serverHealthBadge');
            if (serverBadge && data.overall_badge) {
                serverBadge.textContent = data.overall_message || data.overall_badge;
            }
        }

        // 6. Update Resources in Overview
        if (data.resources) {
            updateResourcesUI(data.resources);
        }

        // 7. Render Components Health Matrix
        renderComponentsGrid(data.components_list || []);

    } catch (err) {
        console.error('Failed to load overview:', err);
    }
}

function renderComponentsGrid(components) {
    const container = document.getElementById('componentsHealthGrid');
    if (!container) return;
    container.innerHTML = '';

    if (!components || components.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted); padding:20px;">لا توجد مكونات مفحوصة.</div>';
        return;
    }

    components.forEach(c => {
        const div = document.createElement('div');
        div.className = 'card';
        div.style.padding = '18px 20px';

        let badgeClass = 'healthy';
        if (c.status === 'warning') badgeClass = 'warning';
        else if (c.status === 'critical') badgeClass = 'critical';

        let extraMeta = '';
        if (c.key === 'cookies' && c.expiry_countdown) {
            extraMeta = `<div style="font-size:0.8rem; color:var(--text-muted); margin-top:6px;">الصلاحية: <strong style="color:var(--text-main); font-family:var(--font-mono);">${c.expiry_countdown}</strong></div>`;
        }

        div.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                <div>
                    <h4 style="font-size:0.96rem; font-weight:700; color:var(--text-main); margin-bottom:4px;">${c.name}</h4>
                    <span style="font-size:0.78rem; color:var(--text-muted);">${c.state_text || ''}</span>
                </div>
                <span class="comp-badge ${badgeClass}">${c.badge || 'نشط'}</span>
            </div>
            <p style="font-size:0.82rem; color:var(--text-muted); line-height:1.5;">${c.message || ''}</p>
            ${extraMeta}
        `;
        container.appendChild(div);
    });
}

async function runDiagnosticProbe() {
    showToast('جاري تشغيل الفحص الحي التشخيصي لكافة المكونات والاتصال بيوتيوب...');
    try {
        const res = await apiFetch('/api/monitor/probe', { method: 'POST' });
        const data = await res.json();
        if (data.probe?.success) {
            showToast(`نجح الفحص التشخيصي! زمن الاستجابة: ${data.probe.elapsed_seconds} ثانية`);
        } else {
            showToast('اكتمل الفحص مع وجود تنبيهات.', 'warning');
        }
        loadOverview();
    } catch (e) {
        showToast('فشل تشغيل الفحص التشخيصي.', 'error');
    }
}

async function handleTriggerUpdate() {
    const btn = document.getElementById('btnCheckUpdate');
    const statusEl = document.getElementById('updateStatusText');

    if (btn) btn.disabled = true;
    if (statusEl) statusEl.textContent = 'الاتصال بمستودع PyPi والتحقق من التحديثات...';

    try {
        const res = await apiFetch('/api/system/update', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message || 'تم تحديث yt-dlp بنجاح!');
            if (statusEl) statusEl.textContent = data.message;
            loadOverview();
        } else {
            showToast(data.detail || 'فشل التحديث.', 'error');
        }
    } catch (e) {
        showToast('تعذر الاتصال بالخادم.', 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

window.loadOverview = loadOverview;
window.renderComponentsGrid = renderComponentsGrid;
window.runDiagnosticProbe = runDiagnosticProbe;
window.handleTriggerUpdate = handleTriggerUpdate;
