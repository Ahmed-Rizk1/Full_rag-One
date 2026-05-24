import os
from typing import Any, Protocol, runtime_checkable

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")


@runtime_checkable
class BaseAgent(Protocol):
    """Structural typing Protocol for specialist execution agents in our architecture."""

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent logic over the current state dictionary and return mutations."""
        ...


def load_prompt(filename: str) -> str:
    """Load a system prompt template dynamically from the prompts folder."""
    path = os.path.join(PROMPTS_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()
