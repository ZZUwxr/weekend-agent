(function () {
  let poiLookup = new Map();
  let currentPoi = null;

  function bottomNav() {
    return `
      <div class="bottom-nav">
        <div class="bnav-item" onclick="switchTab('s-home',this)"><div class="bnav-icon">🏠</div><div class="bnav-label">主页</div></div>
        <div class="bnav-item active" onclick="switchTab('s-map',this)"><div class="bnav-icon">🗺️</div><div class="bnav-label">地图</div></div>
        <div class="bnav-item" onclick="switchTab('s-trips',this)"><div class="bnav-icon">📅</div><div class="bnav-label">行程</div></div>
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
        <div class="nav-title">附近地图</div>
        <div class="nav-action" onclick="showToast('在地图上添加自定义点位')">⊕</div>
      </div>

      <div class="scroll-body">
        <div style="margin:0 16px 14px;border-radius:var(--r);overflow:hidden;position:relative;height:240px;background:linear-gradient(160deg,#dcedc8 0%,#b3e5fc 45%,#ffe0b2 100%);border:1px solid var(--border);box-shadow:var(--shadow-card);">
          <svg style="position:absolute;inset:0;width:100%;height:100%;opacity:0.25" viewBox="0 0 360 240">
            <line x1="0" y1="120" x2="360" y2="120" stroke="#888" stroke-width="3"/>
            <line x1="180" y1="0" x2="180" y2="240" stroke="#888" stroke-width="3"/>
            <line x1="0" y1="60" x2="360" y2="160" stroke="#888" stroke-width="2"/>
            <line x1="80" y1="0" x2="280" y2="240" stroke="#888" stroke-width="1.5"/>
          </svg>
          <div id="map-pins"></div>
          <div style="position:absolute;top:148px;left:130px;">
            <div style="width:14px;height:14px;border-radius:50%;background:#3B82F6;border:2px solid white;box-shadow:0 0 0 4px rgba(59,130,246,0.25)"></div>
          </div>
          <svg style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none" viewBox="0 0 360 240">
            <polyline points="137,154 90,68 195,130 248,90" stroke="var(--brand)" stroke-width="2.5" fill="none" stroke-dasharray="6 4" opacity="0.7"/>
          </svg>
          <div style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,0.85);backdrop-filter:blur(8px);border-radius:20px;padding:5px 14px;font-size:11px;color:var(--ink-60);font-family:var(--font-display);font-weight:600;">🗺️ 接入高德/腾讯地图API后展示真实地图</div>
        </div>

        <div id="poi-detail-card" style="display:none;margin:0 16px 14px;background:var(--white);border-radius:var(--r);border:1.5px solid var(--brand);box-shadow:var(--shadow-float);overflow:hidden;">
          <div style="padding:14px 16px 10px;display:flex;align-items:center;gap:10px;">
            <div style="font-size:24px" id="poi-emoji">📍</div>
            <div style="flex:1">
              <div style="font-family:var(--font-display);font-size:15px;font-weight:700" id="poi-name">地点</div>
              <div style="font-size:11px;color:var(--ink-60)" id="poi-cat">分类 · 区域</div>
            </div>
            <div onclick="document.getElementById('poi-detail-card').style.display='none'" style="cursor:pointer;font-size:18px;color:var(--ink-30);">✕</div>
          </div>
          <div style="padding:0 16px 14px;display:flex;gap:16px;">
            <div style="text-align:center"><div style="font-family:var(--font-display);font-size:16px;font-weight:800;color:var(--green)" id="poi-relax">0</div><div style="font-size:10px;color:var(--ink-60)">放松</div></div>
            <div style="text-align:center"><div style="font-family:var(--font-display);font-size:16px;font-weight:800;color:#C0407A" id="poi-photo">0</div><div style="font-size:10px;color:var(--ink-60)">拍照</div></div>
            <div style="text-align:center"><div style="font-family:var(--font-display);font-size:16px;font-weight:800;color:var(--brand)" id="poi-novelty">0</div><div style="font-size:10px;color:var(--ink-60)">新鲜</div></div>
            <div style="flex:1;text-align:right"><div style="font-family:var(--font-display);font-size:13px;font-weight:700" id="poi-price">-</div><div style="font-size:10px;color:var(--ink-60)">人均消费</div></div>
          </div>
          <div style="padding:0 16px;display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px" id="poi-tags"></div>
          <div style="margin:0 16px 14px;background:var(--ink-10);border-radius:var(--r-sm);padding:10px 12px;font-size:12px;color:var(--ink-60);line-height:1.5" id="poi-desc"></div>
          <div style="display:flex;gap:8px;padding:0 16px 14px;">
            <button style="flex:1;padding:11px;background:var(--brand);color:white;border:none;border-radius:var(--r-sm);font-family:var(--font-display);font-size:13px;font-weight:700;cursor:pointer;" onclick="addToTrip()">加入行程</button>
            <button style="flex:1;padding:11px;background:var(--white);color:var(--ink);border:1.5px solid var(--border);border-radius:var(--r-sm);font-family:var(--font-display);font-size:13px;font-weight:600;cursor:pointer;" onclick="openNavigation()">导航前往</button>
          </div>
        </div>

        <div style="padding:0 24px 10px;font-size:12px;font-weight:700;color:var(--ink-60);text-transform:uppercase;letter-spacing:0.5px;font-family:var(--font-display);">当前行程地点</div>
        <div id="map-poi-list" style="padding:0 16px;display:flex;flex-direction:column;gap:8px;"></div>
        <div style="height:16px"></div>
        <div style="padding:0 24px 10px;font-size:12px;font-weight:700;color:var(--ink-60);text-transform:uppercase;letter-spacing:0.5px;font-family:var(--font-display);">附近备选</div>
        <div id="map-fallback-list" style="padding:0 16px;display:flex;flex-direction:column;gap:8px;"></div>
        <div style="height:100px"></div>
      </div>

      ${bottomNav()}
    `;
  }

  function selectedPlanId() {
    const state = window.AppState;
    const view = state?.currentPlan ? window.DataMapper.mapToPlansView(state.currentPlan) : { candidates: [] };
    return view.candidates[state?.selectedPlanIndex || 0]?.id || state?.currentPlan?.recommended_plan_id;
  }

  function renderPins(pois) {
    const positions = [[72, 52], [185, 118], [240, 78], [105, 168], [282, 142]];
    document.getElementById('map-pins').innerHTML = pois.map((poi, index) => {
      const [left, top] = positions[index % positions.length];
      return `
        <div style="position:absolute;top:${top}px;left:${left}px;display:flex;flex-direction:column;align-items:center;cursor:pointer;" onclick="showPoiDetail('${window.escapeHtml(poi.id)}')">
          <div style="background:${index === 0 ? 'var(--brand)' : 'var(--green)'};color:white;font-size:10px;font-weight:700;padding:4px 8px;border-radius:10px;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,0.18)">${poi.emoji} ${window.escapeHtml(poi.name.slice(0, 6))}</div>
          <div style="width:2px;height:8px;background:var(--brand)"></div>
          <div style="width:6px;height:6px;border-radius:50%;background:var(--brand)"></div>
        </div>
      `;
    }).join('');
  }

  function renderView() {
    const plan = window.AppState?.currentPlan;
    const view = plan ? window.DataMapper.mapToMapView(plan, selectedPlanId()) : { pois: [], fallbackPois: [] };
    poiLookup = new Map(view.pois.map(poi => [poi.id, poi]));
    view.pois.forEach(poi => poiLookup.set(poi.name, poi));
    renderPins(view.pois);

    document.getElementById('map-poi-list').innerHTML = view.pois.map(poi => `
      <div style="background:var(--white);border-radius:var(--r-sm);border:1.5px solid ${poi.stationIndex === 1 ? 'var(--brand)' : 'var(--border)'};padding:12px 14px;display:flex;align-items:center;gap:12px;cursor:pointer;box-shadow:var(--shadow-card);" onclick="showPoiDetail('${window.escapeHtml(poi.id)}')">
        <div style="width:36px;height:36px;border-radius:10px;background:var(--ink-10);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">${poi.emoji}</div>
        <div style="flex:1">
          <div style="font-size:13px;font-weight:600;">${window.escapeHtml(poi.name)}</div>
          <div style="font-size:11px;color:var(--ink-60);margin-top:2px;">${window.escapeHtml(poi.category || '地点')} · ${window.escapeHtml(poi.area || '附近')} · ${window.escapeHtml(poi.queueRisk || '排队未知')}</div>
        </div>
        <div style="text-align:right">
          <div style="font-family:var(--font-display);font-size:13px;font-weight:700;color:var(--brand)">站点 ${poi.stationIndex}</div>
          <div style="font-size:10px;color:var(--ink-60)">${window.escapeHtml(window.formatTime(poi.time) || '--:--')}</div>
        </div>
      </div>
    `).join('') || '<div style="background:var(--white);border-radius:var(--r-sm);border:1px solid var(--border);padding:14px;color:var(--ink-60);font-size:12px;">暂无当前行程地点，先去首页生成方案。</div>';

    document.getElementById('map-fallback-list').innerHTML = view.fallbackPois.slice(0, 4).map(poi => `
      <div style="background:var(--white);border-radius:var(--r-sm);border:1px solid var(--border);padding:12px 14px;display:flex;align-items:center;gap:12px;box-shadow:var(--shadow-card);">
        <div style="width:36px;height:36px;border-radius:10px;background:#F5F5F5;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">${poi.emoji}</div>
        <div style="flex:1">
          <div style="font-size:13px;font-weight:600;">${window.escapeHtml(poi.name)}</div>
          <div style="font-size:11px;color:var(--ink-60);margin-top:2px;">${window.escapeHtml(poi.category)} · ${window.escapeHtml(poi.area || '附近')} · ${window.escapeHtml(poi.queueRisk || '排队未知')}</div>
        </div>
        <button style="font-size:11px;padding:5px 10px;background:var(--ink-10);color:var(--ink);border:none;border-radius:6px;cursor:pointer;font-weight:600;" onclick="addNearby(this, '${window.escapeHtml(poi.name)}')">+ 加入</button>
      </div>
    `).join('') || '<div style="background:var(--white);border-radius:var(--r-sm);border:1px solid var(--border);padding:14px;color:var(--ink-60);font-size:12px;">暂无备选地点。</div>';
  }

  function showPoiDetail(nameOrId) {
    const poi = poiLookup.get(nameOrId);
    if (!poi) return window.showToast('没有找到该地点详情');
    currentPoi = poi;
    document.getElementById('poi-emoji').textContent = poi.emoji;
    document.getElementById('poi-name').textContent = poi.name;
    document.getElementById('poi-cat').textContent = `${poi.category || '地点'} · ${poi.area || '附近'}`;
    document.getElementById('poi-relax').textContent = Number(poi.scores.relax || 0).toFixed(1);
    document.getElementById('poi-photo').textContent = Number(poi.scores.photo || 0).toFixed(1);
    document.getElementById('poi-novelty').textContent = Number(poi.scores.novelty || 0).toFixed(1);
    document.getElementById('poi-price').textContent = poi.avgPrice ? `¥${poi.avgPrice}/人` : '价格未知';
    document.getElementById('poi-tags').innerHTML = poi.tags.map(tag => `<span style="font-size:10px;padding:3px 8px;border-radius:20px;background:var(--ink-10);color:var(--ink-60);font-weight:600;">${window.escapeHtml(tag)}</span>`).join('');
    document.getElementById('poi-desc').textContent = poi.description || '暂无说明。';
    document.getElementById('poi-detail-card').style.display = '';
  }

  function addToTrip() {
    window.showToast(currentPoi ? `已将「${currentPoi.name}」加入行程` : '请先选择地点');
  }

  function openNavigation() {
    window.showToast(currentPoi ? `正在打开「${currentPoi.name}」的导航` : '请先选择地点');
  }

  function addNearby(button, name) {
    if (button) button.textContent = '已加入';
    window.showToast(`已将「${name}」加入备选`);
  }

  function init() {
    renderView();
  }

  window.showPoiDetail = showPoiDetail;
  window.addToTrip = addToTrip;
  window.openNavigation = openNavigation;
  window.addNearby = addNearby;
  window.PageMap = { render, init, destroy() {} };
})();
