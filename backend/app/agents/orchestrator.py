from typing import Any, TypedDict
from langgraph.graph import END, StateGraph

from app.agents.code_agent import CodeAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.research_agent import ResearchAgent
from app.core.schemas.enums import GroqModel
from app.rag.retriever import HybridRetriever
from app.services.llm_client import LLMClient


class AgentState(TypedDict):
    """LangGraph state representation for the Multi-Agent Orchestrator."""

    messages: list[dict[str, Any]]
    user_id: str
    conversation_id: str
    agent_type: str
    context: list[str]
    citations: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    db: Any  # Database session (AsyncSession) passed dynamically
    queue: Any  # Optional asyncio.Queue for token streaming


class AgentOrchestrator:
    """Main Orchestration Engine combining intent classification, RAG, and LangGraph routing."""

    def __init__(self, llm_client: LLMClient, retriever: HybridRetriever) -> None:
        self.llm_client = llm_client
        self.research_agent = ResearchAgent(retriever, llm_client)
        self.code_agent = CodeAgent(llm_client)
        self.planning_agent = PlanningAgent(llm_client)

        # Initialize LangGraph builder
        workflow = StateGraph(AgentState)

        # Register graph execution nodes
        workflow.add_node("classify_intent", self.node_classify_intent)
        workflow.add_node("research", self.node_research)
        workflow.add_node("code", self.node_code)
        workflow.add_node("planning", self.node_planning)
        workflow.add_node("general", self.node_general)

        # Define edge routing rules
        workflow.set_entry_point("classify_intent")

        workflow.add_conditional_edges(
            "classify_intent",
            self.route_intent,
            {
                "research": "research",
                "code": "code",
                "planning": "planning",
                "general": "general",
            },
        )

        workflow.add_edge("research", END)
        workflow.add_edge("code", END)
        workflow.add_edge("planning", END)
        workflow.add_edge("general", END)

        self.graph = workflow.compile()

    async def node_classify_intent(self, state: AgentState) -> dict[str, Any]:
        """Classify the user's intent to route to the correct specialist."""
        messages = state.get("messages", [])

        query_str = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                query_str = msg.get("content", "")
                break

        if not query_str:
            return {"agent_type": "general"}

        prompt = f"""You are an AI intent classifier. Classify the user query into one of these exact categories:
- "research" (if they are asking to search, summarize, or query uploaded documents/knowledge)
- "code" (if they are asking about programming, code analysis, or repository reviews)
- "planning" (if they want to break down a task or generate an execution plan)
- "general" (for general questions, greeting, or chit-chat)

Output ONLY the category name in lowercase: "research", "code", "planning", or "general". Do not include explanations or formatting.

Query: "{query_str}"
"""
        response = await self.llm_client.complete(
            messages=[{"role": "user", "content": prompt}],
            model=GroqModel.LLAMA_70B,
        )

        intent = response["content"].strip().lower()
        # Fallback validation
        if intent not in ("research", "code", "planning", "general"):
            intent = "general"

        return {"agent_type": intent}

    def route_intent(self, state: AgentState) -> str:
        """Edge evaluation function deciding routing destinations based on intent classification."""
        return state.get("agent_type", "general")

    async def node_research(self, state: AgentState) -> dict[str, Any]:
        """Execute the Research specialist node."""
        return await self.research_agent.run(state)

    async def node_code(self, state: AgentState) -> dict[str, Any]:
        """Execute the Code specialist node."""
        return await self.code_agent.run(state)

    async def node_planning(self, state: AgentState) -> dict[str, Any]:
        """Execute the Planning specialist node."""
        return await self.planning_agent.run(state)

    async def node_general(self, state: AgentState) -> dict[str, Any]:
        """Execute the General Chat agent node."""
        messages = state.get("messages", [])

        formatted = [{"role": "system", "content": "You are a helpful assistant."}]
        for msg in messages:
            formatted.append({"role": msg["role"], "content": msg["content"]})

        # Run completion (streaming if queue is provided, else non-streaming)
        queue = state.get("queue")
        if queue:
            content_pieces = []
            async for token in self.llm_client.stream(
                messages=formatted,
                model=GroqModel.LLAMA_70B,
            ):
                content_pieces.append(token)
                await queue.put({"type": "token", "content": token})

            full_content = "".join(content_pieces)
        else:
            response = await self.llm_client.complete(
                messages=formatted,
                model=GroqModel.LLAMA_70B,
            )
            full_content = response["content"]

        assistant_msg = {"role": "assistant", "content": full_content}
        return {"messages": messages + [assistant_msg]}
