(function () {
  function render() {
    return `
      <div class="status-bar">
        <span>9:43</span>
        <div class="status-icons"><span>▲▲▲</span><span>🔋</span></div>
      </div>

      <div class="nav-header">
        <div class="nav-back" onclick="goTo('s-analyzing')">←</div>
        <div class="nav-title">协商结果</div>
        <div class="nav-action" id="compare-action" style="font-size:12px;font-weight:700;">对比</div>
      </div>

      <div class="scroll-body">
        <div class="plans-header">
          <div class="plans-title">为你协商出<br><span id="plan-count">0</span> 个方案</div>
          <div class="plans-sub">已识别冲突并计算各角色满意度</div>
        </div>

        <div class="plan-tabs" id="plan-tabs"></div>

        <div class="satisfaction-card" id="sat-card">
          <div class="sat-title" id="sat-title">📊 各角色满意度</div>
          <div class="sat-rows" id="sat-rows"></div>
          <div class="sat-group-total">
            <div class="sgt-label">群体综合得分</div>
            <div class="sgt-score" id="sgt-score">-</div>
          </div>
        </div>

        <div class="itinerary-card">
          <div class="itin-header">
            <div class="itin-theme" id="itin-theme">等待生成方案</div>
            <div class="itin-duration" id="itin-duration">-</div>
          </div>
          <div class="itin-stops" id="itin-stops"></div>
        </div>

        <div class="comp-badge" id="comp-badge">
          <div class="comp-badge-icon">🎁</div>
          <div class="comp-badge-text" id="comp-text">生成完成后会展示补偿说明。</div>
        </div>

        <div class="plan-actions">
          <button class="action-primary" id="confirm-plan-btn" type="button">确认方案，一键安排 →</button>
          <button class="action-secondary" id="switch-plan-btn" type="button">查看另一个方案</button>
        </div>
        <div class="spacer-16"></div>
      </div>
    `;
  }

  function planView() {
    const planOutput = window.AppState?.currentPlan;
    return planOutput ? window.DataMapper.mapToPlansView(planOutput) : { candidates: [], recommendedIndex: 0 };
  }

  function selectedIndex(view) {
    if (!view.candidates.length) return 0;
    const raw = window.AppState?.selectedPlanIndex;
    if (Number.isInteger(raw) && raw >= 0 && raw < view.candidates.length) return raw;
    return view.recommendedIndex || 0;
  }

  function renderTabs(view, index) {
    const container = document.getElementById('plan-tabs');
    if (!container) return;
    container.innerHTML = view.candidates.map((candidate, idx) => `
      <div class="plan-tab ${idx === 0 ? 'plan-a-tab' : 'plan-b-tab'} ${idx === index ? 'selected' : ''}" data-index="${idx}">
        ${candidate.isRecommended ? '<div class="recommended-tag">推荐</div>' : ''}
        <div class="pt-label">Plan ${String.fromCharCode(65 + idx)}</div>
        <div class="pt-sub">${window.escapeHtml(candidate.title)} · 综合 ${candidate.groupScore}</div>
      </div>
    `).join('') || '<div class="plan-tab selected"><div class="pt-label">暂无方案</div><div class="pt-sub">请先在首页生成</div></div>';
    container.querySelectorAll('.plan-tab').forEach(tab => {
      tab.addEventListener('click', () => selectCandidate(Number(tab.dataset.index)));
    });
  }

  function renderCandidate(candidate, index, total) {
    document.getElementById('sat-title').textContent = `📊 各角色满意度 · Plan ${String.fromCharCode(65 + index)}`;
    document.getElementById('sgt-score').textContent = candidate.groupScore;
    document.getElementById('itin-theme').textContent = candidate.theme || candidate.title;
    document.getElementById('itin-duration').textContent = `${candidate.stops.length}站 · ¥${candidate.estimatedCost || 0}`;
    document.getElementById('comp-text').innerHTML = candidate.compensation
      ? `<strong>已做补偿：</strong>${window.escapeHtml(candidate.compensation)}`
      : '<strong>补偿说明：</strong>当前方案没有显式牺牲项。';
    document.getElementById('confirm-plan-btn').textContent = `确认 Plan ${String.fromCharCode(65 + index)}，一键安排 →`;
    document.getElementById('switch-plan-btn').textContent = total > 1 ? `查看 Plan ${String.fromCharCode(65 + ((index + 1) % total))}` : '暂无另一个方案';

    document.getElementById('sat-rows').innerHTML = candidate.roles.map(role => `
      <div class="sat-row">
        <div class="sat-role">${role.emoji} ${window.escapeHtml(role.name)}</div>
        <div class="sat-bar-bg"><div class="sat-bar ${role.level}" style="width:${role.percent}%"></div></div>
        <div class="sat-score">${role.score}</div>
      </div>
      ${role.compensation ? `<div class="sat-comp">${window.escapeHtml(role.compensation)}</div>` : ''}
    `).join('') || '<div class="sat-row"><div class="sat-role">暂无评分</div><div class="sat-bar-bg"><div class="sat-bar mid" style="width:0%"></div></div><div class="sat-score">-</div></div>';

    document.getElementById('itin-stops').innerHTML = candidate.stops.map((stop, idx) => `
      <div class="itin-stop">
        <div class="stop-time">${window.escapeHtml(stop.time || '--:--')}</div>
        <div class="stop-dot-col">
          <div class="stop-dot ${stop.type === 'buf' ? 'move' : stop.type}"></div>
          ${idx < candidate.stops.length - 1 ? '<div class="stop-line"></div>' : ''}
        </div>
        <div class="stop-info">
          <div class="stop-name">${window.escapeHtml(stop.name)}</div>
          <div class="stop-detail">${window.escapeHtml(stop.detail)}</div>
          <div class="stop-tags">${stop.tags.map(tag => `<span class="stop-tag">${window.escapeHtml(tag)}</span>`).join('')}</div>
        </div>
      </div>
    `).join('') || '<div class="itin-stop"><div class="stop-info"><div class="stop-name">暂无时间线</div><div class="stop-detail">后端没有返回 timeline</div></div></div>';
  }

  function renderEmpty() {
    document.getElementById('plan-count').textContent = '0';
    renderTabs({ candidates: [] }, 0);
    document.getElementById('confirm-plan-btn').dataset.empty = '1';
    document.getElementById('confirm-plan-btn').textContent = '回首页生成方案';
    document.getElementById('switch-plan-btn').disabled = true;
  }

  function refresh() {
    const view = planView();
    if (!view.candidates.length) {
      renderEmpty();
      return;
    }
    const index = selectedIndex(view);
    window.AppState.selectedPlanIndex = index;
    document.getElementById('plan-count').textContent = view.candidates.length;
    renderTabs(view, index);
    renderCandidate(view.candidates[index], index, view.candidates.length);
  }

  function selectCandidate(indexOrKey) {
    const view = planView();
    if (!view.candidates.length) return;
    let index = indexOrKey;
    if (indexOrKey === 'a') index = 0;
    if (indexOrKey === 'b') index = 1;
    index = Math.max(0, Math.min(view.candidates.length - 1, Number(index) || 0));
    window.AppState.selectedPlanIndex = index;
    refresh();
  }

  async function confirmSelected() {
    const state = window.AppState;
    if (!state?.sessionId) {
      window.showToast('缺少 session_id，无法确认方案');
      return;
    }
    const btn = document.getElementById('confirm-plan-btn');
    const old = btn.textContent;
    btn.disabled = true;
    btn.textContent = '确认中…';
    try {
      const plan = await window.API.confirmPlan(state.sessionId);
      state.currentPlan = plan;
      state.sessionId = plan.session_id || state.sessionId;
      window.navigateTo?.('s-exec');
    } catch (error) {
      window.showToast(`确认失败：${error.message}`);
      btn.disabled = false;
      btn.textContent = old;
    }
  }

  function compare() {
    const view = planView();
    if (view.candidates.length < 2) {
      window.showToast('至少需要两个方案才能对比');
      return;
    }
    window.showCompareModal(view.candidates[0], view.candidates[1], () => selectCandidate(0), () => selectCandidate(1));
  }

  function init() {
    refresh();
    document.getElementById('confirm-plan-btn')?.addEventListener('click', event => {
      if (event.currentTarget.dataset.empty === '1') window.navigateTo?.('s-home');
      else confirmSelected();
    });
    document.getElementById('switch-plan-btn')?.addEventListener('click', () => {
      const view = planView();
      if (view.candidates.length > 1) selectCandidate((selectedIndex(view) + 1) % view.candidates.length);
    });
    document.getElementById('compare-action')?.addEventListener('click', compare);
  }

  window.selectPlan = selectCandidate;
  window.PagePlans = { render, init, destroy() {}, selectCandidate };
})();
