(function () {
  const SCREENS = {
    's-home': 'PageHome',
    's-analyzing': 'PageAnalyzing',
    's-plans': 'PagePlans',
    's-exec': 'PageExec',
    's-map': 'PageMap',
    's-trips': 'PageTrips',
    's-profile': 'PageProfile'
  };

  window.AppState = {
    sessionId: null,
    userId: `user_${Math.random().toString(36).slice(2, 8)}`,
    currentPlan: null,
    selectedPlanIndex: 0,
    isStreaming: false,
    streamAbort: null,
    streamEvents: [],
    streamStatus: '',
    pendingQuery: '',
    planCompleteSeen: false,
    completedPlanFetching: false,
    city: '深圳',
    startTime: null,
    durationMinutes: 240
  };

  function moduleFor(screenId) {
    return window[SCREENS[screenId]];
  }

  function renderScreen(screenId) {
    const el = document.getElementById(screenId);
    const page = moduleFor(screenId);
    if (!el || !page) return;
    if (typeof page.destroy === 'function') page.destroy();
    el.innerHTML = page.render();
    if (typeof page.init === 'function') page.init();
  }

  function navigateTo(screenId, data = {}) {
    Object.assign(window.AppState, data || {});
    window.goTo(screenId);
  }

  function selectedPlanId() {
    const plan = window.AppState.currentPlan;
    if (!plan) return null;
    const view = window.DataMapper.mapToPlansView(plan);
    return view.candidates[window.AppState.selectedPlanIndex || 0]?.id || plan.recommended_plan_id;
  }

  function setCompletedPlan(data) {
    const plan = data?.plan || data;
    if (!plan || !Array.isArray(plan.plan_candidates)) return;
    window.AppState.currentPlan = plan;
    window.AppState.sessionId = data?.session_id || plan.session_id || window.AppState.sessionId;
    const view = window.DataMapper.mapToPlansView(plan);
    window.AppState.selectedPlanIndex = view.recommendedIndex || 0;
    window.AppState.isStreaming = false;
    window.PageAnalyzing?.handleStreamEvent?.('plan_complete', { session_id: window.AppState.sessionId, plan });
  }

  async function handlePlanComplete(data) {
    window.AppState.planCompleteSeen = true;
    if (data?.plan && Array.isArray(data.plan.plan_candidates)) {
      setCompletedPlan(data);
      return;
    }

    const sessionId = data?.session_id;
    if (!sessionId) {
      window.PageAnalyzing?.handleStreamEvent?.('error', { message: 'plan_complete 缺少 session_id' });
      return;
    }

    window.AppState.completedPlanFetching = true;
    window.AppState.sessionId = sessionId;
    window.PageAnalyzing?.handleStreamEvent?.('step_start', { name: 'fetch_completed_plan', label: '拉取完整方案' });
    try {
      const plan = await window.API.getPlan(sessionId);
      setCompletedPlan({ session_id: sessionId, plan });
    } catch (error) {
      window.AppState.isStreaming = false;
      window.PageAnalyzing?.handleStreamEvent?.('error', { message: `拉取完整方案失败：${error.message}` });
      window.showToast(`拉取完整方案失败：${error.message}`);
    } finally {
      window.AppState.completedPlanFetching = false;
    }
  }

  async function fallbackPreview(request, reason) {
    if (window.AppState.currentPlan || window.AppState.fallbackStarted) return;
    window.AppState.fallbackStarted = true;
    window.AppState.streamStatus = reason ? `流式失败，改用同步后端 API：${reason}` : '改用同步后端 API';
    window.PageAnalyzing?.handleStreamEvent?.('step_start', { step_name: 'preview_fallback' });
    try {
      const plan = await window.API.previewPlan(request);
      setCompletedPlan({ session_id: plan.session_id, plan });
    } catch (error) {
      window.AppState.isStreaming = false;
      window.PageAnalyzing?.handleStreamEvent?.('error', { message: error.message || String(error) });
      window.showToast(`生成失败：${error.message}`);
    }
  }

  function startPlanRequest(query) {
    if (typeof window.AppState.streamAbort === 'function') window.AppState.streamAbort();
    const request = {
      user_id: window.AppState.userId,
      query,
      city: window.AppState.city,
      start_time: window.AppState.startTime || new Date().toISOString(),
      duration_minutes: window.AppState.durationMinutes
    };

    Object.assign(window.AppState, {
      currentPlan: null,
      sessionId: null,
      selectedPlanIndex: 0,
      isStreaming: true,
      fallbackStarted: false,
      planCompleteSeen: false,
      completedPlanFetching: false,
      pendingQuery: query,
      streamEvents: [],
      streamStatus: '正在连接后端 Agent…'
    });
    navigateTo('s-analyzing');

    try {
      const stream = window.API.streamPlanPreview(request, {
        onStepStart: data => window.PageAnalyzing?.handleStreamEvent?.('step_start', data),
        onStepComplete: data => window.PageAnalyzing?.handleStreamEvent?.('step_complete', data),
        onToolCall: data => window.PageAnalyzing?.handleStreamEvent?.('tool_call', data),
        onCandidateStart: data => window.PageAnalyzing?.handleStreamEvent?.('candidate_start', data),
        onCandidateComplete: data => window.PageAnalyzing?.handleStreamEvent?.('candidate_complete', data),
        onPlanComplete: data => handlePlanComplete(data),
        onError: data => {
          window.PageAnalyzing?.handleStreamEvent?.('error', data);
          fallbackPreview(request, data?.message);
        },
        onDone: () => {
          if (!window.AppState.currentPlan && !window.AppState.fallbackStarted && !window.AppState.planCompleteSeen) {
            fallbackPreview(request, '流式响应未返回完整方案');
          }
        }
      });
      window.AppState.streamAbort = stream.abort;
    } catch (error) {
      fallbackPreview(request, error.message);
    }
  }

  function initApp() {
    Object.keys(SCREENS).forEach(screenId => {
      window.onEnter(screenId, () => renderScreen(screenId));
    });
    Object.keys(SCREENS).forEach(renderScreen);
    window.API.getRuntimeMeta?.()
      .then(meta => {
        window.AppState.runtimeMeta = meta;
        console.info('[Weekend Agent] runtime', meta);
      })
      .catch(error => console.warn('[Weekend Agent] runtime meta failed', error));
  }

  Object.assign(window, {
    renderScreen,
    navigateTo,
    startPlanRequest,
    selectedPlanId
  });

  document.addEventListener('DOMContentLoaded', initApp);
})();
