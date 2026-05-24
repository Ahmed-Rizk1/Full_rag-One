import json
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

_TTL = 7200  # 2 hours


class ShortTermMemory:
    """Redis-backed short-term session buffer keyed by session:{user_id}:{conv_id}."""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._client

    def _key(self, user_id: str, conv_id: str) -> str:
        return f"session:{user_id}:{conv_id}"

    async def get(self, user_id: str, conv_id: str) -> list[dict[str, Any]]:
        try:
            raw = await self._get_client().get(self._key(user_id, conv_id))
            return json.loads(raw) if raw else []
        except Exception:
            return []

    async def set(self, user_id: str, conv_id: str, messages: list[dict[str, Any]]) -> None:
        try:
            await self._get_client().setex(
                self._key(user_id, conv_id), _TTL, json.dumps(messages)
            )
        except Exception:
            pass

    async def append(self, user_id: str, conv_id: str, message: dict[str, Any]) -> None:
        messages = await self.get(user_id, conv_id)
        messages.append(message)
        await self.set(user_id, conv_id, messages)

    async def clear(self, user_id: str, conv_id: str) -> None:
        try:
            await self._get_client().delete(self._key(user_id, conv_id))
        except Exception:
            pass
