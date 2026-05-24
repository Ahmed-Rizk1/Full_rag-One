from typing import Any


class MemoryAgent:
    """Stub: determines what to commit to long-term memory from agent outputs."""

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        # TODO Phase 7B: implement importance scoring + LTM writes
        return {**state, "memory_stored": False}
