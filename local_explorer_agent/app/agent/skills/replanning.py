from local_explorer_agent.app.domain.enums import EventType, PlanState
from local_explorer_agent.app.domain.models import PlanEvent, PlanOutput


class ReplanningSkill:
    name = "replanning"

    def run(self, *, plan: PlanOutput, event: PlanEvent) -> PlanOutput:
        updated = plan.model_copy(deep=True)
        updated.plan_version += 1
        updated.state = PlanState.REPLANNING

        if event.event_type == EventType.QUEUE_OVERFLOW:
            changed = self._replace_affected_poi(updated, event)
            updated.replan_reason = (
                "排队风险升高，已优先使用受影响阶段的备选 POI。"
                if changed
                else "排队事件已记录，但没有找到可替换备选点。"
            )
        elif event.event_type == EventType.WEATHER_CHANGE:
            changed = self._replace_outdoor_poi(updated, event)
            updated.replan_reason = (
                "天气变化，已把受影响户外节点替换为室内备选。"
                if changed
                else "天气事件已记录，当前推荐方案没有必须替换的户外节点。"
            )
        elif event.event_type == EventType.BOOKING_FAILED:
            for task in updated.execution_graph:
                if task.poi_id == event.affected_poi_id:
                    task.status = "failed"
                    task.result = {"reason": "mock booking failed", "event_id": event.event_id}
            self._replace_affected_poi(updated, event)
            updated.replan_reason = "预订失败，已标记失败任务并尝试切换到阶段备选点。"
        elif event.event_type == EventType.TIME_OVERRUN:
            for candidate in updated.plan_candidates:
                for stage in candidate.stages[1:]:
                    stage.duration_minutes = max(25, stage.duration_minutes - 10)
            updated.replan_reason = "时间超出预期，已压缩后续阶段时长，保留核心节点。"
        elif event.event_type == EventType.USER_FEEDBACK:
            updated.state = PlanState.FEEDBACK
            updated.replan_reason = "已记录用户反馈，等待下一轮局部偏好调整。"

        return updated

    def _replace_affected_poi(self, plan: PlanOutput, event: PlanEvent) -> bool:
        changed = False
        for candidate in plan.plan_candidates:
            for stage in candidate.stages:
                selected_poi_id = stage.selected_poi.id if stage.selected_poi else None
                if self._is_affected(stage.stage_id, selected_poi_id, event):
                    if stage.fallback_pois:
                        old = stage.selected_poi
                        stage.selected_poi = stage.fallback_pois.pop(0)
                        if old:
                            stage.fallback_pois.append(old)
                        stage.reasoning = f"{stage.reasoning} 已因事件 {event.event_id} 局部替换。"
                        changed = True
        return changed

    def _replace_outdoor_poi(self, plan: PlanOutput, event: PlanEvent) -> bool:
        changed = False
        for candidate in plan.plan_candidates:
            for stage in candidate.stages:
                if event.affected_stage_id and stage.stage_id != event.affected_stage_id:
                    continue
                if stage.selected_poi and not stage.selected_poi.indoor:
                    indoor_fallback = next((poi for poi in stage.fallback_pois if poi.indoor), None)
                    if indoor_fallback:
                        stage.fallback_pois = [
                            poi for poi in stage.fallback_pois if poi.id != indoor_fallback.id
                        ]
                        stage.fallback_pois.append(stage.selected_poi)
                        stage.selected_poi = indoor_fallback
                        changed = True
        return changed

    def _is_affected(
        self,
        stage_id: str,
        poi_id: str | None,
        event: PlanEvent,
    ) -> bool:
        return bool(
            (event.affected_stage_id and event.affected_stage_id == stage_id)
            or (event.affected_poi_id and event.affected_poi_id == poi_id)
        )
