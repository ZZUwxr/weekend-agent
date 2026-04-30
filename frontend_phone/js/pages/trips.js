(function () {
  function bottomNav() {
    return `
      <div class="bottom-nav">
        <div class="bnav-item" onclick="switchTab('s-home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">主页</div></div>
        <div class="bnav-item" onclick="switchTab('s-map',this)"><div class="bnav-icon">🗺️</div><div class="bnav-label">地图</div></div>
        <div class="bnav-item active" onclick="switchTab('s-trips',this)"><div class="bnav-icon">📅</div><div class="bnav-label">行程</div></div>
        <div class="bnav-item" onclick="switchTab('s-profile',this)"><div class="bnav-icon">👤</div><div class="bnav-label">我的</div></div>
      </div>
    `;
  }

  function render() {
    return `
      <div class="status-bar">
        <span>9:41</span>
        <div class="status-icons"><span>▲▲▲</span><span>🔋</span></div>
      </div>
      <div class="nav-header">
        <div style="width:36px"></div>
        <div class="nav-title">我的行程</div>
        <div class="nav-action" onclick="navigateTo('s-home')" style="font-size:12px;font-weight:700;color:var(--brand)">+ 新建</div>
      </div>

      <div class="scroll-body">
        <div id="active-trip"></div>
        <div style="padding:0 24px 10px;font-size:12px;font-weight:700;color:var(--ink-60);text-transform:uppercase;letter-spacing:0.5px;font-family:var(--font-display);">历史行程</div>
        <div id="history-trips" style="padding:0 16px;display:flex;flex-direction:column;gap:10px;"></div>
        <div style="height:100px"></div>
      </div>

      ${bottomNav()}
    `;
  }

  function selectedCandidate() {
    const state = window.AppState;
    if (!state?.currentPlan) return null;
    const view = window.DataMapper.mapToPlansView(state.currentPlan);
    return view.candidates[state.selectedPlanIndex || 0] || view.candidates[view.recommendedIndex] || view.candidates[0] || null;
  }

  function renderMiniTimeline(candidate) {
    const stops = candidate?.raw?.stages || [];
    if (!stops.length) return '';
    return stops.slice(0, 4).map((stage, index) => {
      const poi = stage.selected_poi || {};
      const emoji = window.DataMapper.CATEGORY_EMOJI[poi.category] || '📍';
      return `
        ${index > 0 ? '<div style="flex:1;height:2px;background:rgba(255,255,255,0.15);margin:0 4px;position:relative;top:-8px;"></div>' : ''}
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
          <div style="width:32px;height:32px;border-radius:50%;background:${index === 0 ? 'var(--brand)' : 'rgba(255,255,255,0.15)'};display:flex;align-items:center;justify-content:center;font-size:14px;">${emoji}</div>
          <div style="font-size:9px;color:rgba(255,255,255,0.5);text-align:center;max-width:44px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${window.escapeHtml(poi.category || '地点')}</div>
        </div>
      `;
    }).join('');
  }

  function renderActive() {
    const plan = window.AppState?.currentPlan;
    const trip = plan ? window.DataMapper.mapToTripsView(plan).active : null;
    const candidate = selectedCandidate();
    const completed = (plan?.execution_graph || []).filter(task => task.status === 'confirmed').length;
    const taskTotal = (plan?.execution_graph || []).length;
    const title = trip?.title || '还没有当前行程';
    const subtitle = trip ? `今天 · ${candidate?.planType || '推荐方案'} · ${trip.stopCount}站` : '从首页生成方案后会出现在这里';

    document.getElementById('active-trip').innerHTML = `
      <div style="margin:0 16px 16px;background:var(--ink);border-radius:var(--r);overflow:hidden;box-shadow:var(--shadow-float);">
        <div style="padding:16px 18px 12px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
            <div style="width:8px;height:8px;border-radius:50%;background:#4ADE80;animation:pulseGreen 2s infinite"></div>
            <span style="font-size:11px;color:rgba(255,255,255,0.6);font-family:var(--font-display);font-weight:600;letter-spacing:0.5px;">${trip ? '进行中' : '空态'}</span>
          </div>
          <div style="font-family:var(--font-display);font-size:18px;font-weight:800;color:white;letter-spacing:-0.4px;margin-bottom:4px;">${window.escapeHtml(title)}</div>
          <div style="font-size:12px;color:rgba(255,255,255,0.5);">${window.escapeHtml(subtitle)}</div>
        </div>
        <div style="padding:0 18px 16px;display:flex;gap:0;align-items:center;">${renderMiniTimeline(candidate) || '<div style="font-size:12px;color:rgba(255,255,255,0.5);padding:8px 0;">暂无站点</div>'}</div>
        <div style="display:flex;border-top:1px solid rgba(255,255,255,0.08);">
          <div style="flex:1;padding:12px 18px;border-right:1px solid rgba(255,255,255,0.08);">
            <div style="font-family:var(--font-display);font-size:16px;font-weight:800;color:white;">¥${trip?.estimatedCost || 0}</div>
            <div style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:2px;">预估总花费</div>
          </div>
          <div style="flex:1;padding:12px 18px;border-right:1px solid rgba(255,255,255,0.08);">
            <div style="font-family:var(--font-display);font-size:16px;font-weight:800;color:#4ADE80;">${completed}/${taskTotal || 0}</div>
            <div style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:2px;">任务完成</div>
          </div>
          <div style="flex:1;padding:12px 18px;">
            <div style="font-family:var(--font-display);font-size:16px;font-weight:800;color:#FBBF24;">${trip?.score || '-'}</div>
            <div style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:2px;">群体满意度</div>
          </div>
        </div>
        <div style="padding:12px 16px;">
          <button id="trip-open-exec" style="width:100%;padding:12px;background:var(--brand);color:white;border:none;border-radius:10px;font-family:var(--font-display);font-size:14px;font-weight:700;cursor:pointer;">${trip ? '查看执行进度 →' : '去首页生成 →'}</button>
        </div>
      </div>
    `;
    document.getElementById('trip-open-exec')?.addEventListener('click', () => {
      window.navigateTo?.(trip ? 's-exec' : 's-home');
    });
  }

  function renderHistory() {
    const history = window.AppState?.currentPlan ? [] : [];
    document.getElementById('history-trips').innerHTML = history.length ? '' : `
      <div style="background:var(--white);border-radius:var(--r-sm);border:1px solid var(--border);box-shadow:var(--shadow-card);padding:14px 16px;">
        <div style="font-size:14px;font-weight:600;">暂无历史行程</div>
        <div style="font-size:12px;color:var(--ink-60);line-height:1.5;margin-top:4px;">后端暂未提供历史行程接口，本页只展示当前会话生成的行程。</div>
        <button style="margin-top:10px;font-size:12px;padding:7px 12px;background:var(--white);border:1px solid var(--border);border-radius:8px;cursor:pointer;font-weight:600;color:var(--ink);" onclick="repeatTrip('朋友聚会')">用朋友聚会再来一次</button>
      </div>
    `;
  }

  function repeatTrip(type) {
    window.navigateTo?.('s-home');
    setTimeout(() => {
      const input = document.getElementById('homeInput');
      if (input) input.value = `帮我安排一个${type}，更生活一点，别太赶。`;
      input?.focus();
    }, 0);
  }

  function init() {
    renderActive();
    renderHistory();
  }

  window.repeatTrip = repeatTrip;
  window.PageTrips = { render, init, destroy() {} };
})();
