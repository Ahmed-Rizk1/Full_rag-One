from app.memory.short_term import ShortTermMemory


class MemoryManager:
    """Unified interface for short-term (Redis) and long-term (DB+vector) memory."""

    def __init__(self) -> None:
        self.stm = ShortTermMemory()

    async def recall(self, query: str, user_id: str) -> list:
        """Stubbed: returns empty context. Phase 7B will add semantic LTM search."""
        return []

    async def get_session(self, user_id: str, conv_id: str) -> list:
        return await self.stm.get(user_id, conv_id)

    async def append_to_session(self, user_id: str, conv_id: str, message: dict) -> None:
        await self.stm.append(user_id, conv_id, message)

    async def clear_session(self, user_id: str, conv_id: str) -> None:
        await self.stm.clear(user_id, conv_id)
