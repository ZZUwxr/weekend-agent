(function () {
  const previousContent = new Map();

  function showToast(msg, duration = 2200) {
    let toast = document.getElementById('global-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'global-toast';
      toast.style.cssText = `
        position:fixed; bottom:110px; left:50%; transform:translateX(-50%) translateY(20px);
        background:rgba(17,16,16,0.88); color:white;
        padding:11px 20px; border-radius:100px;
        font-family:'Sora',sans-serif; font-size:13px; font-weight:500;
        z-index:9999; opacity:0; transition:all 0.25s cubic-bezier(.4,0,.2,1);
        backdrop-filter:blur(8px); max-width:320px;
        white-space:normal; text-align:center; line-height:1.4;
      `;
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-50%) translateY(20px)';
    requestAnimationFrame(() => requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(-50%) translateY(0)';
    }));
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(-50%) translateY(10px)';
    }, duration);
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function showCompareModal(planA, planB, onSelectA, onSelectB) {
    const safeA = planA || {};
    const safeB = planB || {};
    let modal = document.getElementById('compare-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'compare-modal';
      document.body.appendChild(modal);
    }
    modal.style.cssText = `
      position:fixed; inset:0; z-index:1000;
      background:rgba(17,16,16,0.6); backdrop-filter:blur(6px);
      display:flex; align-items:flex-end; justify-content:center;
    `;
    const rows = [
      ['核心思路', safeA.theme || safeA.title || 'Plan A', safeB.theme || safeB.title || 'Plan B'],
      ['群体综合分', safeA.groupScore ?? '-', safeB.groupScore ?? '-'],
      ['预估花费', safeA.estimatedCost ? `¥${safeA.estimatedCost}` : '-', safeB.estimatedCost ? `¥${safeB.estimatedCost}` : '-'],
      ['第一站', safeA.stops?.[0]?.name || '-', safeB.stops?.[0]?.name || '-'],
      ['补偿措施', safeA.compensation || '暂无', safeB.compensation || '暂无']
    ];
    modal.innerHTML = `
      <div style="width:393px; background:#F8F6F2; border-radius:24px 24px 0 0;
                  padding:20px 20px 40px; max-height:82vh; overflow-y:auto;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <div style="font-family:'Sora',sans-serif;font-size:16px;font-weight:800;">Plan A vs Plan B 对比</div>
          <div id="compare-close"
               style="width:30px;height:30px;border-radius:50%;background:rgba(17,16,16,0.08);
                      display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:16px;">✕</div>
        </div>
        ${rows.map(([label, a, b]) => `
          <div style="display:grid;grid-template-columns:80px 1fr 1fr;gap:8px;
                      padding:10px 0;border-bottom:1px solid rgba(17,16,16,0.07);align-items:start;">
            <div style="font-size:10px;color:rgba(17,16,16,0.5);font-weight:600;padding-top:2px;">${escapeHtml(label)}</div>
            <div style="font-size:12px;background:#1A1A2E;color:white;padding:7px 10px;
                        border-radius:8px;line-height:1.4;">${escapeHtml(a)}</div>
            <div style="font-size:12px;background:#0F3460;color:white;padding:7px 10px;
                        border-radius:8px;line-height:1.4;">${escapeHtml(b)}</div>
          </div>
        `).join('')}
        <div style="display:grid;grid-template-columns:80px 1fr 1fr;gap:8px;margin-top:12px;">
          <div></div>
          <button id="compare-select-a"
                  style="padding:12px;background:#FF4500;color:white;border:none;border-radius:10px;
                         font-family:'Sora',sans-serif;font-size:13px;font-weight:700;cursor:pointer;">
            选 Plan A</button>
          <button id="compare-select-b"
                  style="padding:12px;background:#0F3460;color:white;border:none;border-radius:10px;
                         font-family:'Sora',sans-serif;font-size:13px;font-weight:700;cursor:pointer;">
            选 Plan B</button>
        </div>
      </div>
    `;
    modal.addEventListener('click', e => { if (e.target === modal) modal.style.display = 'none'; }, { once: true });
    document.getElementById('compare-close').onclick = () => { modal.style.display = 'none'; };
    document.getElementById('compare-select-a').onclick = () => {
      modal.style.display = 'none';
      if (typeof onSelectA === 'function') onSelectA();
    };
    document.getElementById('compare-select-b').onclick = () => {
      modal.style.display = 'none';
      if (typeof onSelectB === 'function') onSelectB();
    };
  }

  function showLoading(elementId, message = '加载中…') {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (!previousContent.has(elementId)) previousContent.set(elementId, el.innerHTML);
    el.innerHTML = `<div class="loading-skeleton" style="height:56px;display:flex;align-items:center;justify-content:center;color:var(--ink-60);font-size:12px;">${escapeHtml(message)}</div>`;
  }

  function hideLoading(elementId) {
    const el = document.getElementById(elementId);
    if (!el || !previousContent.has(elementId)) return;
    el.innerHTML = previousContent.get(elementId);
    previousContent.delete(elementId);
  }

  function formatTime(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 5);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false });
  }

  function formatDuration(minutes) {
    const total = Math.max(0, Number(minutes) || 0);
    const h = Math.floor(total / 60);
    const m = total % 60;
    if (!h) return `${m}min`;
    if (!m) return `${h}h`;
    return `${h}h${m}min`;
  }

  function scoreLevel(score) {
    const s = Number(score) || 0;
    if (s >= 4) return 'high';
    if (s >= 3) return 'mid';
    return 'low';
  }

  function scoreToPercent(score) {
    return Math.max(0, Math.min(100, Math.round(((Number(score) || 0) / 5) * 100)));
  }

  Object.assign(window, {
    showToast,
    showCompareModal,
    showLoading,
    hideLoading,
    formatTime,
    formatDuration,
    scoreLevel,
    scoreToPercent,
    escapeHtml
  });
})();
