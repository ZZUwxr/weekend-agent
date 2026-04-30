(function () {
  const DEFAULT_API_BASE = '/api/v1';
  const API_BASE = (() => {
    const params = new URLSearchParams(window.location.search);
    const apiHost = params.get('api');
    if (!apiHost) {
      const isLocalStatic = ['127.0.0.1', 'localhost'].includes(window.location.hostname)
        && window.location.port
        && window.location.port !== '8000';
      if (window.location.protocol === 'file:' || isLocalStatic) {
        return 'http://127.0.0.1:8000/api/v1';
      }
      return DEFAULT_API_BASE;
    }
    const trimmed = apiHost.replace(/\/+$/, '');
    return trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`;
  })();

  async function parseError(response) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      message = body.detail || body.message || JSON.stringify(body);
    } catch (_) {
      try { message = await response.text(); } catch (__) {}
    }
    const error = new Error(message || `${response.status} ${response.statusText}`);
    error.status = response.status;
    return error;
  }

  async function requestJson(path, options = {}) {
    const init = {
      method: options.method || 'GET',
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      signal: options.signal
    };
    if (options.body !== undefined) init.body = JSON.stringify(options.body);
    const response = await fetch(`${API_BASE}${path}`, init);
    if (!response.ok) throw await parseError(response);
    if (response.status === 204) return null;
    return response.json();
  }

  function previewPlan(request) {
    return requestJson('/plans/preview', { method: 'POST', body: request });
  }

  function getPlan(sessionId) {
    return requestJson(`/plans/${encodeURIComponent(sessionId)}`);
  }

  function confirmPlan(sessionId) {
    return requestJson(`/plans/${encodeURIComponent(sessionId)}/confirm`, { method: 'POST' });
  }

  function executePlan(sessionId) {
    return requestJson(`/plans/${encodeURIComponent(sessionId)}/execute`, { method: 'POST' });
  }

  function submitPlanEvent(sessionId, event) {
    return requestJson(`/plans/${encodeURIComponent(sessionId)}/events`, {
      method: 'POST',
      body: { ...(event || {}), session_id: sessionId }
    });
  }

  function submitFeedback(sessionId, request) {
    return requestJson(`/plans/${encodeURIComponent(sessionId)}/feedback`, {
      method: 'POST',
      body: request || {}
    });
  }

  function getRuntimeMeta() {
    return requestJson('/meta/runtime');
  }

  function dispatchSse(eventName, data, callbacks) {
    const table = {
      step_start: callbacks.onStepStart,
      step_complete: callbacks.onStepComplete,
      tool_call: callbacks.onToolCall,
      candidate_start: callbacks.onCandidateStart,
      candidate_complete: callbacks.onCandidateComplete,
      plan_complete: callbacks.onPlanComplete,
      error: callbacks.onError
    };
    const callback = table[eventName];
    if (typeof callback === 'function') callback(data);
  }

  function streamPlanPreview(request, callbacks = {}) {
    const controller = new AbortController();
    let aborted = false;

    (async () => {
      try {
        const response = await fetch(`${API_BASE}/plans/preview/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
          body: JSON.stringify(request),
          signal: controller.signal
        });
        if (!response.ok) throw await parseError(response);
        if (!response.body || !window.TextDecoder) {
          const plan = await previewPlan(request);
          callbacks.onPlanComplete?.({ session_id: plan.session_id, plan });
          callbacks.onDone?.();
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let currentEvent = 'message';
        let currentData = [];

        function flush() {
          if (!currentData.length) return;
          const raw = currentData.join('\n');
          let data = raw;
          try { data = JSON.parse(raw); } catch (_) {}
          dispatchSse(currentEvent, data, callbacks);
          currentEvent = 'message';
          currentData = [];
        }

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split(/\r?\n/);
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (!line.trim()) {
              flush();
            } else if (line.startsWith('event:')) {
              currentEvent = line.slice(6).trim();
            } else if (line.startsWith('data:')) {
              currentData.push(line.slice(5).trim());
            }
          }
        }
        if (buffer.trim()) currentData.push(buffer.trim().replace(/^data:\s*/, ''));
        flush();
        callbacks.onDone?.();
      } catch (error) {
        if (!aborted) callbacks.onError?.({ message: error.message || String(error) });
        if (!aborted) callbacks.onDone?.();
      }
    })();

    return {
      abort() {
        aborted = true;
        controller.abort();
      }
    };
  }

  window.API = {
    DEFAULT_API_BASE,
    API_BASE,
    requestJson,
    previewPlan,
    getPlan,
    confirmPlan,
    executePlan,
    submitPlanEvent,
    submitFeedback,
    getRuntimeMeta,
    streamPlanPreview
  };
})();
