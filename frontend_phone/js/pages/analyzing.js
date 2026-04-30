(function () {
  const STREAM_LABELS = {
    step_start: '正在分析需求',
    step_complete: '完成一步分析',
    tool_call: '正在调用工具',
    candidate_start: '开始生成候选方案',
    candidate_complete: '候选方案已生成',
    plan_complete: '方案生成完成',
    error: '生成遇到问题'
  };

  function badge(type) {
    if (type === 'hard') return ['c-hard', '硬约束'];
    if (type === 'soft') return ['c-soft', '软偏好'];
    return ['c-inferred', '推断'];
  }

  function render() {
    return `
      <div class="status-bar">
        <span>9:41</span>
        <div class="status-icons"><span>▲▲▲</span><span>🔋</span></div>
      </div>

      <div class="nav-header">
        <div class="nav-back" onclick="goTo('s-home')">←</div>
        <div class="nav-title">分析群体需求</div>
        <div style="width:36px"></div>
      </div>

      <div class="scroll-body">
        <div class="analysis-hero">
          <div class="user-query-bubble" id="analysis-query">等待输入出行需求…</div>
          <div class="analysis-header" id="analysis-title">正在理解你的需求</div>
          <div class="analysis-sub" id="analysis-sub">准备调用后端 Agent…</div>
        </div>

        <div class="roles-grid" id="roles-grid">
          <div class="loading-skeleton" style="height:120px;border-radius:16px;"></div>
        </div>

        <div class="spacer-12"></div>
        <div class="conflict-section" id="conflict-section"></div>
        <div class="confidence-grid" id="confidence-grid"></div>

        <div class="proceed-wrap">
          <div id="analysis-hint" style="font-size:12px;color:var(--ink-60);margin-bottom:10px;text-align:center;">生成完成后可以开始协商</div>
          <button class="proceed-btn" id="analysis-proceed" type="button">
            <span>开始协商，生成方案</span>
            <span class="arrow">→</span>
          </button>
        </div>
      </div>
    `;
  }

  function renderRoles(roles) {
    const container = document.getElementById('roles-grid');
    if (!container) return;
    if (!roles.length) {
      container.innerHTML = '<div class="role-card"><div class="role-card-header"><div class="role-avatar dad">👤</div><div><div class="role-name">等待角色识别</div><div class="role-desc">Agent 正在从输入中解析同行人</div></div></div></div>';
      return;
    }
    container.innerHTML = roles.map(role => `
      <div class="role-card">
        <div class="role-card-header">
          <div class="role-avatar ${role.id?.includes('child') ? 'child' : role.id?.includes('spouse') ? 'wife' : 'dad'}">${role.emoji}</div>
          <div>
            <div class="role-name">${window.escapeHtml(role.name)}</div>
            <div class="role-desc">${window.escapeHtml(role.desc)}</div>
          </div>
        </div>
        <div class="role-constraints">
          ${(role.constraints.length ? role.constraints : [{ type: 'inferred', text: '暂无明确约束，按普通同行人处理' }]).map(item => {
            const [cls, label] = badge(item.type);
            return `<div class="constraint-row"><span class="c-badge ${cls}">${label}</span><span>${window.escapeHtml(item.text)}</span></div>`;
          }).join('')}
        </div>
      </div>
    `).join('');
  }

  function renderConflicts(conflicts) {
    const container = document.getElementById('conflict-section');
    if (!container) return;
    if (!conflicts.length) {
      container.innerHTML = `
        <div class="conflict-card">
          <div class="conflict-header">
            <div class="conflict-icon">✓</div>
            <div class="conflict-title-wrap">
              <div class="conflict-title">暂未检测到强冲突</div>
              <div class="conflict-type">会在方案阶段继续做平衡</div>
            </div>
            <div class="conflict-count">0</div>
          </div>
        </div>
      `;
      return;
    }
    container.innerHTML = `
      <div class="conflict-card">
        <div class="conflict-header">
          <div class="conflict-icon">⚡</div>
          <div class="conflict-title-wrap">
            <div class="conflict-title">检测到 ${conflicts.length} 个需求冲突</div>
            <div class="conflict-type">冲突原型：${window.escapeHtml(conflicts[0].typeLabel)}</div>
          </div>
          <div class="conflict-count">${conflicts.length}</div>
        </div>
        <div class="conflict-items">
          ${conflicts.flatMap(conflict => conflict.pairs.map(pair => `
            <div class="conflict-item">
              <div class="vs-pair">
                <div class="vs-a">${window.escapeHtml(pair.sideA)}</div>
                <div class="vs-b">${window.escapeHtml(pair.sideB)}</div>
              </div>
              <div class="vs-connector">VS</div>
            </div>
          `)).join('')}
        </div>
      </div>
    `;
  }

  function renderConfidence(confidence) {
    const items = confidence.items.length ? confidence.items : [{ label: '整体推断', value: 0.65 }];
    const container = document.getElementById('confidence-grid');
    if (!container) return;
    container.innerHTML = `
      <div class="conf-card">
        <div class="conf-title">推断置信度</div>
        ${items.map(item => {
          const pct = Math.round((Number(item.value) <= 1 ? Number(item.value) * 100 : Number(item.value)) || 0);
          const high = pct >= 80;
          return `
            <div class="conf-row">
              <span class="conf-label">${window.escapeHtml(item.label)}</span>
              <div class="conf-bar-bg"><div class="conf-bar-fill ${high ? 'fill-high' : 'fill-mid'}" style="width:${pct}%"></div></div>
              <span class="conf-pct ${high ? 'high' : ''}" style="${high ? '' : 'color:var(--amber)'}">${pct}%</span>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function renderPlan(planOutput) {
    const view = window.DataMapper.mapToAnalyzingView(planOutput);
    document.getElementById('analysis-query').textContent = view.query;
    document.getElementById('analysis-title').textContent = `识别到 ${view.roles.length || 1} 个角色`;
    document.getElementById('analysis-sub').textContent = '已拆解约束、偏好和潜在冲突';
    document.getElementById('analysis-hint').textContent = '分析完成 · 可以进入方案协商';
    renderRoles(view.roles);
    renderConflicts(view.conflicts);
    renderConfidence(view.confidence);
  }

  function renderStreaming() {
    const state = window.AppState || {};
    document.getElementById('analysis-query').textContent = state.pendingQuery || '等待输入出行需求…';
    document.getElementById('analysis-title').textContent = state.isStreaming ? 'Agent 正在工作' : '等待生成结果';
    document.getElementById('analysis-sub').textContent = state.streamStatus || '准备调用后端 Agent…';
  }

  function handleStreamEvent(event, data) {
    const state = window.AppState || {};
    state.streamEvents = state.streamEvents || [];
    state.streamEvents.push({ event, data, at: Date.now() });
    const stepName = data?.step_name || data?.name || data?.label;
    state.streamStatus = stepName
      ? `${STREAM_LABELS[event] || event}：${stepName}`
      : (data?.message || STREAM_LABELS[event] || '正在更新…');

    if (event === 'plan_complete') {
      const plan = data?.plan || data;
      if (plan) {
        state.currentPlan = plan;
        state.sessionId = data?.session_id || plan.session_id || state.sessionId;
        state.isStreaming = false;
        renderPlan(plan);
        return;
      }
    }
    if (event === 'error') {
      state.streamStatus = data?.message || '生成遇到问题，准备降级重试';
    }
    renderStreaming();
  }

  function init() {
    if (window.AppState?.currentPlan) renderPlan(window.AppState.currentPlan);
    else renderStreaming();
    document.getElementById('analysis-proceed')?.addEventListener('click', () => {
      if (!window.AppState?.currentPlan) {
        window.showToast(window.AppState?.isStreaming ? '还在生成方案，稍等一下' : '还没有可协商的方案');
        return;
      }
      window.navigateTo?.('s-plans');
    });
  }

  window.PageAnalyzing = { render, init, destroy() {}, handleStreamEvent };
})();
