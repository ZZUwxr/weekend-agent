(function () {
  const ROLE_EMOJI = {
    child: '🧒',
    spouse: '👩',
    user: '👨',
    friend: '🧑',
    elder: '👴',
    unknown: '👤'
  };

  const CONFLICT_TYPE_CN = {
    energy_mismatch: '体力需求冲突',
    diet_conflict: '饮食需求冲突',
    budget_conflict: '预算观冲突',
    pace_conflict: '节奏偏好冲突',
    photo_vs_practical: '拍照vs实用冲突',
    indoor_outdoor: '室内外偏好冲突',
    unknown: '需求冲突'
  };

  const TIMELINE_TYPE_MAP = {
    activity: 'act',
    transport: 'move',
    dining: 'eat',
    buffer: 'buf'
  };

  const ACTION_EMOJI = {
    book_restaurant: '🍽️',
    book_activity: '🎡',
    call_taxi: '🚕',
    share_plan: '📤',
    order_gift: '🎁'
  };

  const CATEGORY_EMOJI = {
    亲子空间: '🎡',
    游乐园: '🎠',
    动物园: '🐒',
    餐厅: '🍽️',
    轻食: '🥗',
    烧烤: '🍢',
    火锅: '🍲',
    烤肉: '🥩',
    桑拿鸡: '🐔',
    咖啡: '☕',
    甜品: '🍧',
    茶馆: '🍵',
    书店: '📚',
    展览: '🖼️',
    公园: '🌳',
    Citywalk: '🚶',
    桌游: '🎲',
    电竞馆: '🎮',
    网吧: '🖥️',
    密室逃脱: '🗝️',
    真人CS: '🔫',
    KTV: '🎤',
    小剧场: '🎭',
    买手店: '🛍️',
    夜间活动: '🌙'
  };

  function arr(value) { return Array.isArray(value) ? value : []; }
  function num(value, fallback = 0) { return Number.isFinite(Number(value)) ? Number(value) : fallback; }
  function text(value, fallback = '') { return value === null || value === undefined || value === '' ? fallback : String(value); }
  function scoreLevel(score) { return window.scoreLevel ? window.scoreLevel(score) : (num(score) >= 4 ? 'high' : num(score) >= 3 ? 'mid' : 'low'); }
  function scoreToPercent(score) { return window.scoreToPercent ? window.scoreToPercent(score) : Math.round((num(score) / 5) * 100); }
  function formatTime(value) { return window.formatTime ? window.formatTime(value) : text(value).slice(0, 5); }
  function formatDuration(value) { return window.formatDuration ? window.formatDuration(value) : `${num(value)}min`; }

  function roleById(roleId, inferredContext) {
    return arr(inferredContext?.roles).find(role => role.role_id === roleId) || null;
  }

  function resolveRoleName(roleId, inferredContext) {
    return roleById(roleId, inferredContext)?.display_name || roleId || '未知角色';
  }

  function resolveRoleEmoji(roleId, inferredContext) {
    const role = roleById(roleId, inferredContext);
    return ROLE_EMOJI[role?.role_type] || ROLE_EMOJI.unknown;
  }

  function selectedCandidate(planOutput, selectedPlanId) {
    const candidates = arr(planOutput?.plan_candidates);
    if (!candidates.length) return null;
    return candidates.find(p => p.plan_id === selectedPlanId)
      || candidates.find(p => p.plan_id === planOutput?.recommended_plan_id)
      || candidates[0];
  }

  function stageByPoi(candidate) {
    const map = new Map();
    arr(candidate?.stages).forEach(stage => {
      if (stage.selected_poi?.id) map.set(stage.selected_poi.id, stage);
    });
    return map;
  }

  function mapToAnalyzingView(planOutput) {
    const inferred = planOutput?.inferred_context || {};
    return {
      query: text(planOutput?.input_query, '等待输入出行需求…'),
      roles: arr(inferred.roles).map(role => ({
        id: role.role_id,
        emoji: ROLE_EMOJI[role.role_type] || ROLE_EMOJI.unknown,
        name: text(role.display_name, '未知角色'),
        desc: arr(role.risk_points)[0] || arr(role.hard_constraints)[0] || arr(role.soft_preferences)[0] || '已识别出行诉求',
        constraints: [
          ...arr(role.hard_constraints).map(item => ({ type: 'hard', text: item })),
          ...arr(role.soft_preferences).map(item => ({ type: 'soft', text: item })),
          ...arr(role.hidden_needs).map(item => ({ type: 'inferred', text: item }))
        ]
      })),
      conflicts: arr(planOutput?.conflicts).map(conflict => ({
        icon: '⚡',
        title: text(conflict.description, '检测到需求冲突'),
        typeLabel: CONFLICT_TYPE_CN[conflict.conflict_type] || CONFLICT_TYPE_CN.unknown,
        pairs: arr(conflict.evidence).length ? arr(conflict.evidence).map(item => ({ sideA: item, sideB: text(conflict.resolution_hint, '需要折中处理') })) : [{
          sideA: arr(conflict.involved_roles).map(id => `${resolveRoleEmoji(id, inferred)} ${resolveRoleName(id, inferred)}`).join(' / '),
          sideB: text(conflict.resolution_hint, '需要折中处理')
        }]
      })),
      confidence: {
        items: Object.entries(inferred.confidence_summary || {}).map(([key, value]) => ({
          label: ({ distance: '出行距离', diet: '饮食约束', transport: '出行方式', budget: '预算水平' }[key] || key),
          value: num(value)
        }))
      }
    };
  }

  function mapToPlansView(planOutput) {
    const inferred = planOutput?.inferred_context || {};
    const candidates = arr(planOutput?.plan_candidates).map(candidate => {
      const poiById = new Map(arr(candidate.stages).map(stage => [stage.selected_poi?.id, stage.selected_poi]));
      const stops = arr(candidate.timeline).map(item => {
        const poi = poiById.get(item.poi_id) || {};
        const tags = arr(poi.activity_tags).concat(arr(poi.mood_tags)).slice(0, 4);
        return {
          time: formatTime(item.time),
          type: TIMELINE_TYPE_MAP[item.type] || 'act',
          name: text(item.poi_name || poi.name, item.type === 'transport' ? '路程移动' : '待定地点'),
          detail: [item.notes, item.duration_minutes ? formatDuration(item.duration_minutes) : '', item.estimated_cost ? `¥${item.estimated_cost}` : ''].filter(Boolean).join(' · '),
          tags
        };
      });
      const roles = arr(candidate.satisfaction_scores).map(score => ({
        emoji: resolveRoleEmoji(score.role_id, inferred),
        name: resolveRoleName(score.role_id, inferred),
        score: num(score.score).toFixed(1),
        level: scoreLevel(score.score),
        percent: scoreToPercent(score.score),
        compensation: score.compensation || null
      }));
      const compensation = roles.map(role => role.compensation).filter(Boolean).join('；');
      const estimatedCost = arr(candidate.timeline).reduce((sum, item) => sum + num(item.estimated_cost), 0);
      return {
        id: candidate.plan_id,
        planType: candidate.plan_type,
        title: text(candidate.title, '未命名方案'),
        theme: text(candidate.theme, ''),
        isRecommended: candidate.plan_id === planOutput?.recommended_plan_id,
        groupScore: num(candidate.overall_score).toFixed(1),
        roles,
        stops,
        compensation,
        estimatedCost,
        raw: candidate
      };
    });
    const recommendedIndex = Math.max(0, candidates.findIndex(candidate => candidate.isRecommended));
    return { candidates, recommendedIndex };
  }

  function mapToExecView(planOutput) {
    const plan = selectedCandidate(planOutput, planOutput?.recommended_plan_id) || {};
    const poiById = new Map(arr(plan.stages).map(stage => [stage.selected_poi?.id, stage.selected_poi?.name]));
    const tasks = arr(planOutput?.execution_graph).map(task => {
      const status = task.status === 'confirmed' ? 'done' : task.status === 'failed' || task.status === 'cancelled' ? 'replan' : 'pending';
      return {
        id: task.task_id,
        icon: ACTION_EMOJI[task.action] || '✅',
        name: `${task.action || 'task'}${task.poi_id ? ` — ${poiById.get(task.poi_id) || task.poi_id}` : ''}`,
        detail: Object.entries(task.params || {}).map(([k, v]) => `${k}: ${v}`).join(' · ') || task.mock_scenario || '',
        status,
        statusLabel: status === 'done' ? '完成' : status === 'replan' ? '需处理' : '待执行',
        isReplan: status === 'replan',
        isNew: task.status === 'pending'
      };
    });
    const completed = tasks.filter(task => task.status === 'done').length;
    const needsAttention = tasks.filter(task => task.status === 'replan').length;
    const inProgress = Math.max(0, tasks.length - completed - needsAttention);
    return {
      planTitle: plan.title || '当前方案',
      planTheme: plan.theme || '',
      startTime: arr(plan.timeline)[0]?.time || '',
      tasks,
      progress: {
        completed,
        inProgress,
        needsAttention,
        percent: tasks.length ? Math.round((completed / tasks.length) * 100) : 0
      },
      estimatedCost: arr(plan.timeline).reduce((sum, item) => sum + num(item.estimated_cost), 0),
      groupScore: num(plan.overall_score).toFixed(1),
      shareMessage: planOutput?.share_message || '',
      replanReason: planOutput?.replan_reason || ''
    };
  }

  function mapToMapView(planOutput, selectedPlanId) {
    const plan = selectedCandidate(planOutput, selectedPlanId);
    const stageMap = stageByPoi(plan);
    const timelineByPoi = new Map(arr(plan?.timeline).filter(item => item.poi_id).map(item => [item.poi_id, item]));
    const pois = arr(plan?.stages).filter(stage => stage.selected_poi).map((stage, index) => {
      const poi = stage.selected_poi;
      const scores = poi.experience_scores || {};
      return {
        id: poi.id,
        name: poi.name,
        emoji: CATEGORY_EMOJI[poi.category] || '📍',
        category: poi.category,
        area: poi.area || '',
        lon: poi.lon,
        lat: poi.lat,
        avgPrice: poi.avg_price,
        queueRisk: poi.queue_risk,
        scores: { relax: scores.relax_score || 0, photo: scores.photo_score || 0, novelty: scores.novelty_score || 0 },
        tags: arr(poi.activity_tags).concat(arr(poi.mood_tags)).slice(0, 6),
        description: stage.experience_goal || stage.reasoning || '',
        isCurrentTrip: true,
        stationIndex: index + 1,
        time: timelineByPoi.get(poi.id)?.time || ''
      };
    });
    return {
      pois,
      routeSegments: arr(plan?.route_segments),
      fallbackPois: arr(plan?.stages).flatMap(stage => arr(stage.fallback_pois).map(poi => ({
        name: poi.name,
        emoji: CATEGORY_EMOJI[poi.category] || '📍',
        category: poi.category,
        area: poi.area || '',
        queueRisk: poi.queue_risk
      })))
    };
  }

  function mapToTripsView(planOutput) {
    const plan = selectedCandidate(planOutput, planOutput?.recommended_plan_id);
    if (!plan) return { active: null, history: [] };
    return {
      active: {
        title: plan.title,
        theme: plan.theme,
        score: num(plan.overall_score).toFixed(1),
        estimatedCost: arr(plan.timeline).reduce((sum, item) => sum + num(item.estimated_cost), 0),
        stopCount: arr(plan.stages).length
      },
      history: []
    };
  }

  function buildFeedbackPayload(planOutput, formData) {
    return {
      rating: formData?.rating ? Number(formData.rating) : null,
      raw_feedback: formData?.raw_feedback || formData?.rawFeedback || '',
      tags: arr(formData?.tags),
      payload: { session_id: planOutput?.session_id, ...(formData?.payload || {}) }
    };
  }

  window.DataMapper = {
    ROLE_EMOJI,
    CONFLICT_TYPE_CN,
    TIMELINE_TYPE_MAP,
    ACTION_EMOJI,
    CATEGORY_EMOJI,
    resolveRoleName,
    resolveRoleEmoji,
    selectedCandidate,
    mapToAnalyzingView,
    mapToPlansView,
    mapToExecView,
    mapToMapView,
    mapToTripsView,
    buildFeedbackPayload
  };
})();
