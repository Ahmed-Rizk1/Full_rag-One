from typing import Any

from app.agents.base_agent import load_prompt
from app.core.schemas.enums import GroqModel
from app.services.llm_client import LLMClient


class PlanningAgent:
    """Specialist agent that decomposes complex user prompts into structured plans."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self.system_prompt = load_prompt("planning.txt")

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        messages = state.get("messages", [])

        formatted_messages = [{"role": "system", "content": self.system_prompt}]
        for msg in messages:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})

        # Run completion (streaming if queue is provided, else non-streaming)
        queue = state.get("queue")
        if queue:
            content_pieces = []
            async for token in self.llm_client.stream(
                messages=formatted_messages,
                model=GroqModel.LLAMA_70B,
            ):
                content_pieces.append(token)
                await queue.put({"type": "token", "content": token})

            full_content = "".join(content_pieces)
        else:
            response = await self.llm_client.complete(
                messages=formatted_messages,
                model=GroqModel.LLAMA_70B,
            )
            full_content = response["content"]

        assistant_msg = {"role": "assistant", "content": full_content}

        return {
            "messages": messages + [assistant_msg],
        }
