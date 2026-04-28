from typing import TypeVar

from pydantic import BaseModel

from local_explorer_agent.app.core.exceptions import LLMError
from local_explorer_agent.app.domain.enums import GroupType, RoleType
from local_explorer_agent.app.domain.models import GroupContext, RoleProfile

T = TypeVar("T", bound=BaseModel)


class MockLLMClient:
    def complete_json(self, prompt: str, schema: type[T]) -> T:
        if "Prompt" in prompt or "输出 JSON Schema" in prompt:
            raise LLMError("MockLLMClient defers skill prompts to rule-based fallback")
        if schema is GroupContext:
            if "2男2女" in prompt or "拍照" in prompt:
                return schema.model_validate(
                    GroupContext(
                        group_type=GroupType.FRIENDS,
                        roles=[
                            RoleProfile(
                                role_id="photo_oriented_role",
                                role_type=RoleType.FRIEND,
                                display_name="拍照氛围导向朋友",
                                soft_preferences=["拍照", "有氛围"],
                            )
                        ],
                        group_size=4,
                        scene_label="mock_friends_outing",
                        inferred_constraints=["mock structured output"],
                        confidence_summary={"overall": 0.8},
                    ).model_dump()
                )
            return schema.model_validate(
                GroupContext(
                    group_type=GroupType.FAMILY,
                    roles=[
                        RoleProfile(
                            role_id="adult_user",
                            role_type=RoleType.USER,
                            display_name="成人用户",
                            soft_preferences=["轻松参与", "别太远"],
                        )
                    ],
                    group_size=1,
                    scene_label="mock_family_outing",
                    inferred_constraints=["mock structured output"],
                    confidence_summary={"overall": 0.8},
                ).model_dump()
            )
        raise LLMError("MockLLMClient only returns direct GroupContext; use rule-based fallback")
