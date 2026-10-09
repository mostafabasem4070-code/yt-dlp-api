/* ==========================================================================
   LIVE TERMINAL LOGS & DIAGNOSTICS CONSOLE
   YouTube API Hub - Cloud Control Center
   ========================================================================== */

let logsTimer = null;
let currentLogLevelFilter = 'ALL';
let logSearchKeyword = '';

async function loadServerLogs() {
    try {
        let url = `/api/logs?limit=150`;
        if (currentLogLevelFilter !== 'ALL') {
            url += `&level=${encodeURIComponent(currentLogLevelFilter)}`;
        }
        if (logSearchKeyword) {
            url += `&search=${encodeURIComponent(logSearchKeyword)}`;
        }

        const res = await apiFetch(url);
        if (!res.ok) return;
        const data = await res.json();
        const terminal = document.getElementById('terminalOutput');
        if (!terminal) return;

        const records = data.logs || [];
        if (records.length === 0) {
            terminal.innerHTML = '<div class="log-entry INFO" style="color:var(--text-muted);">[SYSTEM] لا توجد سجلات مسجلة حالياً تطابق الفلتر المحدد.</div>';
            return;
        }

        // إنشاء محتوى السجل بدقة بدون انهيار الكائنات
        terminal.innerHTML = '';
        records.forEach(item => {
            const div = document.createElement('div');
            
            let timestamp = '';
            let level = 'INFO';
            let logger = 'system';
            let message = '';

            if (typeof item === 'object' && item !== null) {
                timestamp = item.timestamp || '';
                level = (item.level || 'INFO').toUpperCase();
                logger = item.logger || 'system';
                message = item.message || '';
            } else {
                // إذا كان سطراً نصياً قديماً
                const str = String(item);
                message = str;
                if (str.includes('ERROR') || str.includes('Error')) level = 'ERROR';
                else if (str.includes('WARNING') || str.includes('Warning')) level = 'WARNING';
                else if (str.includes('DEBUG')) level = 'DEBUG';
            }

            div.className = `log-entry ${level}`;
            const timeTag = timestamp ? `[${timestamp}] ` : '';
            div.textContent = `${timeTag}[${level}] [${logger}] ${message}`;
            terminal.appendChild(div);
        });

        // التمرير التلقائي لأسفل السجل إن كان مفعلاً
        const autoScroll = document.getElementById('autoScrollLogs');
        if (autoScroll && autoScroll.checked) {
            terminal.scrollTop = terminal.scrollHeight;
        }

    } catch (err) {
        console.error('Failed to load server logs:', err);
    }
}

function setLogLevelFilter(level, btn) {
    currentLogLevelFilter = level;
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    if (btn) btn.classList.add('active');
    loadServerLogs();
}

function handleLogSearch(keyword) {
    logSearchKeyword = keyword.trim();
    loadServerLogs();
}

async function copyTerminalLogs() {
    const terminal = document.getElementById('terminalOutput');
    const text = terminal ? (terminal.innerText || terminal.textContent || '') : '';
    const btn = document.getElementById('btnCopyLogs');

    if (!text.trim() || text.includes('لا توجد سجلات')) {
        showToast('السجل فارغ حالياً.', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(text);
        if (btn) {
            const oldHtml = btn.innerHTML;
            btn.innerHTML = '<span style="color:#10b981;">✓ تم النسخ بنجاح!</span>';
            setTimeout(() => { btn.innerHTML = oldHtml; }, 2200);
        }
        showToast('تم نسخ سجل العمليات بالكامل إلى الحافظة!');
    } catch (err) {
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast('تم نسخ السجل للحافظة!');
    }
}

async function clearTerminalLogs() {
    if (!confirm('هل تريد مسح سجل العمليات الحالية بالكامل؟')) return;

    try {
        await apiFetch('/api/logs', { method: 'DELETE' });
        const terminal = document.getElementById('terminalOutput');
        if (terminal) {
            terminal.innerHTML = '<div class="log-entry INFO">[SYSTEM] تم مسح سجل العمليات بنجاح.</div>';
        }
        showToast('تم مسح السجل بنجاح.');
    } catch (e) {
        showToast('فشل مسح السجل.', 'error');
    }
}

function startLogsPolling() {
    loadServerLogs();
    if (logsTimer) clearInterval(logsTimer);
    logsTimer = setInterval(loadServerLogs, 3500);
}

function stopLogsPolling() {
    if (logsTimer) {
        clearInterval(logsTimer);
        logsTimer = null;
    }
}

window.loadServerLogs = loadServerLogs;
window.setLogLevelFilter = setLogLevelFilter;
window.handleLogSearch = handleLogSearch;
window.copyTerminalLogs = copyTerminalLogs;
window.clearTerminalLogs = clearTerminalLogs;
window.startLogsPolling = startLogsPolling;
window.stopLogsPolling = stopLogsPolling;
