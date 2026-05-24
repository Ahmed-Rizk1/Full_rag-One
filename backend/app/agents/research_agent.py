from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import load_prompt
from app.core.schemas.enums import GroqModel
from app.rag.retriever import HybridRetriever
from app.services.llm_client import LLMClient


class ResearchAgent:
    """Specialist agent that retrieves document context and performs cited Q&A completions."""

    def __init__(self, retriever: HybridRetriever, llm_client: LLMClient) -> None:
        self.retriever = retriever
        self.llm_client = llm_client
        self.system_prompt = load_prompt("research.txt")

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        messages = state.get("messages", [])
        user_id = state.get("user_id")
        db: AsyncSession | None = state.get("db")

        # Find the latest user query
        query_str = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                query_str = msg.get("content", "")
                break

        context_texts: list[str] = []
        citations: list[dict[str, Any]] = []

        # Execute hybrid retrieval if active database session is available
        if db and query_str and user_id:
            retrieved = await self.retriever.retrieve(
                db=db,
                query_str=query_str,
                user_id=user_id,
            )
            context_texts = [r.content for r in retrieved]
            citations = [r.to_dict() for r in retrieved]

        # Structure prompts with context injections
        context_block = "\n---\n".join(context_texts)
        system_instructions = f"{self.system_prompt}\n\nDocument Context:\n{context_block}"

        formatted_messages = [{"role": "system", "content": system_instructions}]
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
            # Post citations to the stream
            await queue.put({"type": "citations", "citations": citations})
        else:
            response = await self.llm_client.complete(
                messages=formatted_messages,
                model=GroqModel.LLAMA_70B,
            )
            full_content = response["content"]

        assistant_msg = {"role": "assistant", "content": full_content}

        return {
            "messages": messages + [assistant_msg],
            "context": context_texts,
            "citations": citations,
        }
