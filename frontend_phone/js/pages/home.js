(function () {
  const SCENARIOS = [
    {
      cls: 'family',
      emoji: '👨‍👩‍👧',
      name: '家庭亲子',
      conflict: '代际冲突型',
      query: '今天下午带孩子和家人出去玩，孩子需要能玩久一点，大人也能休息，别太远。'
    },
    {
      cls: 'friends',
      emoji: '🧑‍🤝‍🧑',
      name: '朋友聚会',
      conflict: '偏好分化型',
      query: '周末四个朋友出去玩，想要更生活一点，可以上网、密室、烧烤或火锅，预算中等。'
    },
    {
      cls: 'couple',
      emoji: '💑',
      name: '情侣约会',
      conflict: '消费观型',
      query: '想安排一个轻松的情侣约会，有一点新鲜感，不要太累，晚饭要好吃。'
    }
  ];

  function renderBottomNav(activeId) {
    return `
      <div class="bottom-nav">
        <div class="bnav-item ${activeId === 's-home' ? 'active' : ''}" onclick="switchTab('s-home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">主页</div></div>
        <div class="bnav-item ${activeId === 's-map' ? 'active' : ''}" onclick="switchTab('s-map',this)"><div class="bnav-icon">🗺️</div><div class="bnav-label">地图</div></div>
        <div class="bnav-item ${activeId === 's-trips' ? 'active' : ''}" onclick="switchTab('s-trips',this)"><div class="bnav-icon">📅</div><div class="bnav-label">行程</div></div>
        <div class="bnav-item ${activeId === 's-profile' ? 'active' : ''}" onclick="switchTab('s-profile',this)"><div class="bnav-icon">👤</div><div class="bnav-label">我的</div></div>
      </div>
    `;
  }

  function render() {
    const hasPlan = !!window.AppState?.currentPlan;
    const planTitle = hasPlan
      ? window.escapeHtml(window.DataMapper.selectedCandidate(window.AppState.currentPlan, window.AppState.currentPlan.recommended_plan_id)?.title || '最近生成的行程')
      : '还没有生成行程';
    const planSub = hasPlan
      ? '刚刚生成 · 点击查看方案'
      : '暂无真实历史 · 先生成一条新行程';

    return `
      <div class="status-bar">
        <span>9:41</span>
        <div class="status-icons"><span>▲▲▲</span><span>WiFi</span><span>🔋</span></div>
      </div>

      <div class="nav-header">
        <div style="width:36px"></div>
        <div class="nav-title">今天去哪</div>
        <div class="nav-action" onclick="showToast('暂无新通知')">🔔</div>
      </div>

      <div class="scroll-body">
        <div class="home-hero">
          <div class="home-greeting">你好，小明 👋<br>今天<span>想去哪</span>？</div>
          <div class="home-sub">告诉我一句话，我来帮你协调好所有人</div>
        </div>

        <div class="input-card">
          <div class="input-card-top">
            <div class="input-avatar">MT</div>
            <textarea class="input-field" placeholder="今天下午带老婆孩子出去玩，别太远，帮我安排一下…" rows="3" id="homeInput"></textarea>
          </div>
          <div class="input-card-bottom">
            <div class="input-hints">
              <div class="hint-tag" data-fill="孩子5岁">👶 孩子5岁</div>
              <div class="hint-tag" data-fill="老婆在减肥">🥗 老婆减肥</div>
              <div class="hint-tag" data-fill="4人朋友局">👥 4人朋友</div>
              <div class="hint-tag" data-fill="别太远">📍 别太远</div>
            </div>
            <button class="send-btn" type="button">→</button>
          </div>
        </div>

        <div class="spacer-16"></div>
        <div class="section-label">场景快选</div>
        <div class="scenario-scroll">
          ${SCENARIOS.map(item => `
            <div class="scenario-card ${item.cls}" data-query="${window.escapeHtml(item.query)}">
              <div class="scenario-emoji">${item.emoji}</div>
              <div class="scenario-name">${item.name}</div>
              <div class="scenario-conflict">${item.conflict}</div>
            </div>
          `).join('')}
        </div>

        <div class="spacer-16"></div>
        <div class="section-label">上次安排</div>
        <div class="plan-mini-list">
          <div class="plan-mini" data-open-current="${hasPlan ? '1' : '0'}">
            <div class="plan-mini-icon">🎡</div>
            <div class="plan-mini-info">
              <div class="plan-mini-name">${planTitle}</div>
              <div class="plan-mini-sub">${window.escapeHtml(planSub)}</div>
            </div>
            <div class="plan-mini-arrow">›</div>
          </div>
        </div>
        <div class="spacer-16"></div>
      </div>

      ${renderBottomNav('s-home')}
    `;
  }

  function fillHome(text) {
    const input = document.getElementById('homeInput');
    if (!input) return;
    const value = input.value.trim();
    input.value = value ? `${value}，${text}` : text;
    input.focus();
  }

  function submitHome() {
    const input = document.getElementById('homeInput');
    const query = input?.value.trim() || input?.placeholder || '';
    if (!query) {
      window.showToast('先描述一下你想怎么出门');
      return;
    }
    window.startPlanRequest?.(query);
  }

  function init() {
    const input = document.getElementById('homeInput');
    const send = document.querySelector('#s-home .send-btn');
    send?.addEventListener('click', submitHome);
    input?.addEventListener('keydown', event => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') submitHome();
    });
    document.querySelectorAll('#s-home .hint-tag').forEach(tag => {
      tag.addEventListener('click', () => fillHome(tag.dataset.fill || tag.textContent.trim()));
    });
    document.querySelectorAll('#s-home .scenario-card').forEach(card => {
      card.addEventListener('click', () => {
        if (input) input.value = card.dataset.query || '';
        submitHome();
      });
    });
    document.querySelector('#s-home .plan-mini')?.addEventListener('click', event => {
      if (event.currentTarget.dataset.openCurrent === '1') {
        window.navigateTo?.('s-plans');
      } else {
        window.showToast('还没有真实历史行程，先生成一个吧');
      }
    });
  }

  window.fillHome = fillHome;
  window.PageHome = { render, init, destroy() {} };
})();
