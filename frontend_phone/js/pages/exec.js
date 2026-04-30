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
        <span>9:45</span>
        <div class="status-icons"><span>▲▲▲</span><span>🔋</span></div>
      </div>
      <div class="nav-header">
        <div class="nav-back" onclick="goTo('s-plans')">←</div>
        <div class="nav-title">执行进度</div>
        <div class="nav-action" onclick="shareTrip()">↗</div>
      </div>

      <div class="scroll-body">
        <div class="exec-header">
          <div class="exec-title" id="exec-title">等待确认方案</div>
          <div class="exec-sub" id="exec-sub">确认后会生成执行任务链</div>
        </div>

        <div class="progress-card">
          <div class="progress-top">
            <div class="progress-label">整体完成度</div>
            <div class="progress-pct" id="progress-pct">0%</div>
          </div>
          <div class="progress-track"><div class="progress-fill" id="prog-fill" style="width:0%"></div></div>
          <div class="progress-stats">
            <div class="pstat"><div class="pstat-val ok" id="pstat-done">0</div><div class="pstat-label">已完成</div></div>
            <div class="pstat"><div class="pstat-val pending" id="pstat-pending">0</div><div class="pstat-label">进行中</div></div>
            <div class="pstat"><div class="pstat-val alert" id="pstat-alert">0</div><div class="pstat-label">需关注</div></div>
          </div>
        </div>

        <div class="replan-alert" id="replan-alert" style="display:none">
          <div class="ra-top">
            <div class="ra-icon">⚠️</div>
            <div class="ra-title">自动重规划触发</div>
            <div class="ra-time">now</div>
          </div>
          <div class="ra-desc" id="replan-desc"></div>
          <div class="ra-btns">
            <button class="ra-btn-accept" id="accept-replan-btn" type="button">接受新方案</button>
            <button class="ra-btn-view" id="exec-compare-btn" type="button">查看对比</button>
          </div>
        </div>

        <div class="tasks-label">执行任务链</div>
        <div class="tasks-list" id="tasks-list"></div>

        <div class="spacer-12"></div>
        <div class="share-pill">
          <div class="share-text" id="share-text">确认方案后会生成可复制的分享文案。</div>
          <button class="share-copy" id="share-copy" type="button">复制</button>
        </div>

        <div class="onetap-wrap">
          <button class="onetap-btn" id="execute-all-btn" type="button">
            <div class="onetap-left">
              <span>一键全部下单</span>
              <span class="onetap-sub">餐厅 + 活动 + 叫车</span>
            </div>
            <div class="onetap-price" id="onetap-price">¥0</div>
          </button>
        </div>
        <div class="spacer-16"></div>
      </div>

      ${bottomNav()}
    `;
  }

  function statusClass(task) {
    if (task.status === 'done') return 's-done';
    if (task.status === 'replan') return 's-replan';
    if (task.status === 'surprise') return 's-surprise';
    return 's-pending';
  }

  function iconBg(task) {
    if (task.status === 'done') return '#DCFCE7';
    if (task.status === 'replan') return '#FEE2E2';
    if (task.status === 'surprise') return '#F3E8FF';
    return '#FEF3C7';
  }

  function renderEmpty() {
    document.getElementById('tasks-list').innerHTML = `
      <div class="task-item">
        <div class="task-icon" style="background:#F3F4F6">⏳</div>
        <div class="task-info">
          <div class="task-name">暂无执行任务</div>
          <div class="task-detail">请先在方案页确认一个计划</div>
        </div>
        <span class="status-badge s-pending">待生成</span>
      </div>
    `;
    document.getElementById('execute-all-btn').disabled = true;
  }

  function renderView() {
    const plan = window.AppState?.currentPlan;
    if (!plan) {
      renderEmpty();
      return;
    }
    const view = window.DataMapper.mapToExecView(plan);
    document.getElementById('exec-title').textContent = `${view.planTitle} · 执行中`;
    document.getElementById('exec-sub').textContent = `${view.planTheme || '当前方案'} · ${window.formatTime(view.startTime) || '待定'} 出发`;
    document.getElementById('progress-pct').textContent = `${view.progress.percent}%`;
    document.getElementById('prog-fill').style.width = `${view.progress.percent}%`;
    document.getElementById('pstat-done').textContent = view.progress.completed;
    document.getElementById('pstat-pending').textContent = view.progress.inProgress;
    document.getElementById('pstat-alert').textContent = view.progress.needsAttention;
    document.getElementById('onetap-price').textContent = `¥${view.estimatedCost || 0}`;
    document.getElementById('share-text').innerHTML = window.escapeHtml(view.shareMessage || '行程已经准备好，可以发给同行人确认。');

    const alert = document.getElementById('replan-alert');
    if (view.replanReason) {
      alert.style.display = '';
      document.getElementById('replan-desc').textContent = view.replanReason;
    } else {
      alert.style.display = 'none';
    }

    document.getElementById('tasks-list').innerHTML = view.tasks.map(task => `
      <div class="task-item ${task.isReplan ? 'is-replan' : ''} ${task.isNew ? 'is-new' : ''}">
        <div class="task-icon" style="background:${iconBg(task)}">${task.icon}</div>
        <div class="task-info">
          <div class="task-name">${window.escapeHtml(task.name)}</div>
          <div class="task-detail">${window.escapeHtml(task.detail || '等待执行')}</div>
        </div>
        <span class="status-badge ${statusClass(task)}">${window.escapeHtml(task.statusLabel)}</span>
      </div>
    `).join('') || `
      <div class="task-item">
        <div class="task-icon" style="background:#FEF3C7">⏳</div>
        <div class="task-info">
          <div class="task-name">后端未返回 execution_graph</div>
          <div class="task-detail">可以先查看方案，稍后补齐执行任务</div>
        </div>
        <span class="status-badge s-pending">待执行</span>
      </div>
    `;
  }

  async function executeAll(button) {
    const state = window.AppState;
    if (!state?.sessionId) {
      window.showToast('缺少 session_id，无法执行');
      return;
    }
    const btn = button || document.getElementById('execute-all-btn');
    const old = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<div class="onetap-left"><span>执行中…</span><span class="onetap-sub">正在调用后端任务链</span></div><div class="onetap-price">...</div>';
    try {
      const response = await window.API.executePlan(state.sessionId);
      state.currentPlan = response.plan || state.currentPlan;
      if (response.tasks && state.currentPlan) state.currentPlan.execution_graph = response.tasks;
      window.showToast(response.success ? '执行完成' : '部分任务需要关注');
      renderView();
    } catch (error) {
      window.showToast(`执行失败：${error.message}`);
      btn.innerHTML = old;
    } finally {
      btn.disabled = false;
    }
  }

  async function acceptReplan(button) {
    const state = window.AppState;
    if (!state?.sessionId) return window.showToast('缺少 session_id');
    const btn = button || document.getElementById('accept-replan-btn');
    const old = btn.textContent;
    btn.disabled = true;
    btn.textContent = '提交中…';
    try {
      const plan = await window.API.submitPlanEvent(state.sessionId, {
        event_type: 'user_feedback',
        severity: 2,
        payload: { action: 'accept_replan' }
      });
      state.currentPlan = plan;
      window.showToast('已接受新方案');
      renderView();
    } catch (error) {
      window.showToast(`提交失败：${error.message}`);
      btn.textContent = old;
    } finally {
      btn.disabled = false;
    }
  }

  function shareTrip() {
    const msg = window.AppState?.currentPlan?.share_message || document.getElementById('share-text')?.textContent || '';
    if (!msg) return window.showToast('暂无可分享文案');
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(msg).then(() => window.showToast('行程文案已复制')).catch(() => window.showToast(msg.slice(0, 40)));
    } else {
      window.showToast(msg.slice(0, 40));
    }
  }

  function init() {
    renderView();
    document.getElementById('execute-all-btn')?.addEventListener('click', event => executeAll(event.currentTarget));
    document.getElementById('accept-replan-btn')?.addEventListener('click', event => acceptReplan(event.currentTarget));
    document.getElementById('exec-compare-btn')?.addEventListener('click', () => window.navigateTo?.('s-plans'));
    document.getElementById('share-copy')?.addEventListener('click', shareTrip);
  }

  window.executeAll = executeAll;
  window.acceptReplan = acceptReplan;
  window.shareTrip = shareTrip;
  window.PageExec = { render, init, destroy() {} };
})();
