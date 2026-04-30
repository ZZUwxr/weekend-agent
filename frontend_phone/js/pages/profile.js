(function () {
  let selectedRating = 5;

  function bottomNav() {
    return `
      <div class="bottom-nav">
        <div class="bnav-item" onclick="switchTab('s-home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">主页</div></div>
        <div class="bnav-item" onclick="switchTab('s-map',this)"><div class="bnav-icon">🗺️</div><div class="bnav-label">地图</div></div>
        <div class="bnav-item" onclick="switchTab('s-trips',this)"><div class="bnav-icon">📅</div><div class="bnav-label">行程</div></div>
        <div class="bnav-item active" onclick="switchTab('s-profile',this)"><div class="bnav-icon">👤</div><div class="bnav-label">我的</div></div>
      </div>
    `;
  }

  function prefRow(label, width, weight) {
    return `
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:12px;flex:1;color:var(--ink);">${label}</span>
        <div style="width:100px;height:6px;background:var(--ink-10);border-radius:3px;overflow:hidden;"><div style="height:100%;width:${width}%;background:linear-gradient(90deg,var(--brand),var(--brand-2));border-radius:3px;"></div></div>
        <span style="font-family:var(--font-display);font-size:11px;font-weight:700;color:var(--brand);width:32px;text-align:right;">${weight}</span>
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
        <div class="nav-title">我的</div>
        <div class="nav-action" onclick="showToast('设置功能开发中')">⚙</div>
      </div>

      <div class="scroll-body">
        <div style="margin:0 16px 16px;background:var(--ink);border-radius:var(--r);padding:20px;box-shadow:var(--shadow-float);">
          <div style="display:flex;gap:14px;align-items:center;margin-bottom:16px;">
            <div style="width:52px;height:52px;border-radius:16px;background:linear-gradient(135deg,var(--brand),var(--brand-2));display:flex;align-items:center;justify-content:center;font-family:var(--font-display);font-size:22px;font-weight:800;color:white;flex-shrink:0;">明</div>
            <div>
              <div style="font-family:var(--font-display);font-size:17px;font-weight:700;color:white;">小明</div>
              <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:3px;">出行偏好：松弛型 · 中等预算</div>
            </div>
          </div>
          <div style="display:flex;gap:0;border-top:1px solid rgba(255,255,255,0.08);padding-top:14px;">
            <div style="flex:1;text-align:center;"><div style="font-family:var(--font-display);font-size:20px;font-weight:800;color:white;" id="profile-trip-count">0</div><div style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:2px;">当前行程</div></div>
            <div style="flex:1;text-align:center;border-left:1px solid rgba(255,255,255,0.08);"><div style="font-family:var(--font-display);font-size:20px;font-weight:800;color:#4ADE80;" id="profile-score">-</div><div style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:2px;">满意度</div></div>
            <div style="flex:1;text-align:center;border-left:1px solid rgba(255,255,255,0.08);"><div style="font-family:var(--font-display);font-size:20px;font-weight:800;color:#FBBF24;" id="profile-poi-count">0</div><div style="font-size:10px;color:rgba(255,255,255,0.5);margin-top:2px;">地点数</div></div>
          </div>
        </div>

        <div style="padding:0 24px 10px;font-size:12px;font-weight:700;color:var(--ink-60);text-transform:uppercase;letter-spacing:0.5px;font-family:var(--font-display);">Agent 学习到的你的偏好</div>
        <div style="margin:0 16px 14px;background:var(--white);border-radius:var(--r);border:1px solid var(--border);box-shadow:var(--shadow-card);overflow:hidden;">
          <div style="padding:14px 16px 10px;display:flex;align-items:center;gap:8px;">
            <div style="font-size:16px;">🧠</div>
            <div style="font-family:var(--font-display);font-size:13px;font-weight:700;">个人偏好权重</div>
            <div style="margin-left:auto;font-size:11px;color:var(--ink-60);">基于当前会话</div>
          </div>
          <div style="padding:0 16px 14px;display:flex;flex-direction:column;gap:8px;">
            ${prefRow('松弛节奏', 88, '×1.5')}
            ${prefRow('低排队风险', 82, '×1.4')}
            ${prefRow('生活化体验', 78, '×1.3')}
            ${prefRow('距离可控', 70, '×1.2')}
          </div>
        </div>

        <div style="margin:0 16px 14px;background:var(--white);border-radius:var(--r);border:1.5px solid rgba(255,69,0,0.2);box-shadow:var(--shadow-card);overflow:hidden;">
          <div style="padding:14px 16px 12px;background:linear-gradient(135deg,rgba(255,69,0,0.05),rgba(255,107,53,0.03));">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
              <div style="font-size:18px;">📝</div>
              <div style="font-family:var(--font-display);font-size:14px;font-weight:700;color:var(--brand);">行程反馈</div>
            </div>
            <div style="font-size:12px;color:var(--ink-60);line-height:1.5;" id="feedback-desc">当前会话有行程后，可以把反馈提交给后端。</div>
          </div>
          <div style="padding:12px 16px;display:flex;flex-direction:column;gap:8px;">
            <div style="display:flex;gap:6px;" id="rating-buttons">
              ${[1, 2, 3, 4, 5].map(n => `<button data-rating="${n}" style="flex:1;padding:8px;border:1px solid var(--border);border-radius:8px;background:${n === 5 ? 'var(--brand)' : 'var(--white)'};color:${n === 5 ? 'white' : 'var(--ink)'};font-weight:700;cursor:pointer;">${n}</button>`).join('')}
            </div>
            <textarea id="feedback-text" rows="3" style="width:100%;box-sizing:border-box;border:1px solid var(--border);border-radius:10px;padding:10px;font-size:12px;resize:none;font-family:inherit;" placeholder="比如：孩子玩得久不久、餐厅是否合适、节奏是否太赶…"></textarea>
            <button id="feedback-submit" style="width:100%;padding:11px;background:var(--brand);color:white;border:none;border-radius:10px;font-family:var(--font-display);font-size:13px;font-weight:700;cursor:pointer;">提交反馈</button>
          </div>
        </div>

        <div style="padding:0 24px 10px;font-size:12px;font-weight:700;color:var(--ink-60);text-transform:uppercase;letter-spacing:0.5px;font-family:var(--font-display);">设置</div>
        <div id="settings-list" style="margin:0 16px 16px;background:var(--white);border-radius:var(--r);border:1px solid var(--border);box-shadow:var(--shadow-card);overflow:hidden;"></div>
        <div style="height:100px"></div>
      </div>

      ${bottomNav()}
    `;
  }

  function renderStats() {
    const plan = window.AppState?.currentPlan;
    const candidate = plan ? window.DataMapper.selectedCandidate(plan, plan.recommended_plan_id) : null;
    document.getElementById('profile-trip-count').textContent = plan ? '1' : '0';
    document.getElementById('profile-score').textContent = candidate?.overall_score ? Number(candidate.overall_score).toFixed(1) : '-';
    document.getElementById('profile-poi-count').textContent = candidate?.stages?.length || 0;
    document.getElementById('feedback-desc').textContent = plan ? '你的反馈会写入后端反馈接口，并更新当前 plan 状态。' : '当前还没有行程，先生成一个方案后再反馈。';
    document.getElementById('feedback-submit').disabled = !plan;
    document.getElementById('feedback-submit').style.opacity = plan ? '1' : '0.55';
  }

  function renderSettings() {
    const items = [
      ['🏠', '我的位置', '深圳市科技园附近', '定位：深圳市科技园附近'],
      ['💰', '预算偏好', '中等（人均 50–120 元）', '预算偏好：中等'],
      ['🚗', '常用出行方式', '打车优先', '出行方式：打车优先'],
      ['🔔', '出发提醒', '提前 30 分钟', '出发提醒：提前 30 分钟'],
      ['🔒', '隐私设置', '评价数据仅个人可见', '评价数据仅个人可见'],
      ['❓', '关于本产品', '美团 AI 挑战赛参赛作品', '美团 AI 挑战赛参赛作品 v1.0']
    ];
    document.getElementById('settings-list').innerHTML = items.map((item, index) => `
      <div style="display:flex;align-items:center;gap:12px;padding:14px 16px;${index < items.length - 1 ? 'border-bottom:1px solid var(--border);' : ''}cursor:pointer;" onclick="showToast('${window.escapeHtml(item[3])}')">
        <div style="font-size:18px;">${item[0]}</div>
        <div style="flex:1"><div style="font-size:13px;font-weight:600;">${item[1]}</div><div style="font-size:11px;color:var(--ink-60);margin-top:2px;">${item[2]}</div></div>
        <div style="font-size:16px;color:var(--ink-30);">›</div>
      </div>
    `).join('');
  }

  function bindRating() {
    document.querySelectorAll('#rating-buttons button').forEach(button => {
      button.addEventListener('click', () => {
        selectedRating = Number(button.dataset.rating) || 5;
        document.querySelectorAll('#rating-buttons button').forEach(item => {
          const active = Number(item.dataset.rating) === selectedRating;
          item.style.background = active ? 'var(--brand)' : 'var(--white)';
          item.style.color = active ? 'white' : 'var(--ink)';
        });
      });
    });
  }

  async function submitFeedback() {
    const state = window.AppState;
    if (!state?.currentPlan || !state.sessionId) return window.showToast('还没有可反馈的行程');
    const btn = document.getElementById('feedback-submit');
    const old = btn.textContent;
    btn.disabled = true;
    btn.textContent = '提交中…';
    try {
      const payload = window.DataMapper.buildFeedbackPayload(state.currentPlan, {
        rating: selectedRating,
        raw_feedback: document.getElementById('feedback-text').value.trim(),
        tags: ['frontend_phone'],
        payload: { source: 'profile_page' }
      });
      await window.API.submitFeedback(state.sessionId, payload);
      window.showToast('反馈已提交');
      document.getElementById('feedback-text').value = '';
    } catch (error) {
      window.showToast(`反馈失败：${error.message}`);
    } finally {
      btn.disabled = false;
      btn.textContent = old;
    }
  }

  function init() {
    renderStats();
    renderSettings();
    bindRating();
    document.getElementById('feedback-submit')?.addEventListener('click', submitFeedback);
  }

  window.PageProfile = { render, init, destroy() {} };
})();
