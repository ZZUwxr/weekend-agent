import time
from uuid import uuid4

from local_explorer_agent.app.tools.base import BaseTool, ToolResult


class ShareTool(BaseTool):
    name = "share_tool"

    def share_plan(self, *, session_id: str, message: str) -> ToolResult:
        started_at = time.perf_counter()
        return self._result(
            data={
                "share_id": f"share_{uuid4().hex[:10]}",
                "session_id": session_id,
                "message": message,
                "mock_url": f"https://mock.weekend-agent.local/share/{session_id}",
            },
            started_at=started_at,
        )
