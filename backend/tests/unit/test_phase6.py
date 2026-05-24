from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.core.schemas.enums import GroqModel
from app.repositories.conversation_repo import conversation_repository


@pytest.mark.asyncio
async def test_intent_classifier_routing_research():
    """Verify that intent classifier correctly classifies research category."""
    mock_llm = AsyncMock()
    mock_llm.complete.return_value = {"content": "research", "usage": {}}

    mock_retriever = MagicMock()
    orchestrator = AgentOrchestrator(mock_llm, mock_retriever)

    state = {
        "messages": [{"role": "user", "content": "What is the policy document?"}],
        "user_id": "test_user",
        "conversation_id": "test_conv",
        "agent_type": "general",
        "context": [],
        "citations": [],
        "tool_results": [],
    }

    result = await orchestrator.node_classify_intent(state)  # type: ignore
    assert result["agent_type"] == "research"
    mock_llm.complete.assert_called_once()


@pytest.mark.asyncio
async def test_intent_classifier_routing_code():
    """Verify that intent classifier correctly classifies code category."""
    mock_llm = AsyncMock()
    mock_llm.complete.return_value = {"content": "code", "usage": {}}

    mock_retriever = MagicMock()
    orchestrator = AgentOrchestrator(mock_llm, mock_retriever)

    state = {
        "messages": [{"role": "user", "content": "Refactor this python method"}],
        "user_id": "test_user",
        "conversation_id": "test_conv",
        "agent_type": "general",
        "context": [],
        "citations": [],
        "tool_results": [],
    }

    result = await orchestrator.node_classify_intent(state)  # type: ignore
    assert result["agent_type"] == "code"


@pytest.mark.asyncio
async def test_sse_streaming_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Verify that send message endpoint returns correctly formatted Server-Sent Events (SSE) chunks."""
    # 1. Sign up and authenticate user
    email = "chat_sse@example.com"
    password = "securepassword123"
    signup_payload = {"email": email, "password": password, "full_name": "SSE User"}

    await client.post("/api/v1/auth/signup", json=signup_payload)
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create conversation
    conv_payload = {"title": "SSE test conversation", "agent_type": "general"}
    conv_response = await client.post(
        "/api/v1/chat/conversations",
        json=conv_payload,
        headers=headers,
    )
    assert conv_response.status_code == 201
    conv_id = conv_response.json()["id"]

    # 3. Mock Groq LLM completion and stream generator
    async def mock_stream(*args, **kwargs):
        yield "Streaming "
        yield "tokens "
        yield "live!"

    # Patch the singletons imported in chat router
    with patch("app.api.v1.chat.llm_client.stream", side_effect=mock_stream), \
         patch("app.api.v1.chat.llm_client.complete") as mock_complete:

        # Mock the intent classification completion to return 'general'
        mock_complete.return_value = {"content": "general", "usage": {}}

        # Send message to trigger orchestrator
        msg_payload = {"content": "Hello bot, start stream"}
        response = await client.post(
            f"/api/v1/chat/conversations/{conv_id}/messages",
            json=msg_payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Read the raw stream chunks
        stream_chunks = []
        async for line in response.aiter_bytes():
            stream_chunks.append(line.decode("utf-8"))

        full_stream_output = "".join(stream_chunks)

        # Assert correct SSE payload lines
        assert "event: token" in full_stream_output
        assert "event: citations" in full_stream_output
        assert "event: done" in full_stream_output
        assert "Streaming" in full_stream_output
        assert "live!" in full_stream_output
