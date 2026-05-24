import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.workflow_repo import workflow_repository
from app.repositories.memory_repo import memory_repository


# ── Repository unit tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_workflow(db_session: AsyncSession):
    """WorkflowRepository.create() persists a workflow record."""
    wf = await workflow_repository.create(db_session, obj_in={
        "user_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Test Workflow",
        "status": "pending",
        "definition": {"steps": []},
        "execution_log": {},
    })
    await db_session.commit()
    assert wf.id is not None
    assert wf.name == "Test Workflow"
    assert wf.status == "pending"


@pytest.mark.asyncio
async def test_create_memory(db_session: AsyncSession):
    """MemoryRepository.create() persists a memory record."""
    mem = await memory_repository.create(db_session, obj_in={
        "user_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "memory_type": "fact",
        "content": "The sky is blue.",
        "importance_score": 0.8,
    })
    await db_session.commit()
    assert mem.id is not None
    assert mem.content == "The sky is blue."
    assert mem.importance_score == 0.8


@pytest.mark.asyncio
async def test_get_workflow_returns_none_for_missing(db_session: AsyncSession):
    """WorkflowRepository.get() returns None for a non-existent ID."""
    import uuid
    result = await workflow_repository.get(db_session, id=uuid.uuid4())
    assert result is None


# ── API endpoint tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_workflow_endpoint(client: AsyncClient, db_session: AsyncSession):
    """POST /api/v1/workflows creates a workflow and returns 201."""
    email = "workflow_test@example.com"
    password = "securepassword123"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": password, "full_name": "WF User"})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.post(
        "/api/v1/workflows/",
        json={"name": "My Workflow", "steps": [{"agent_type": "general", "input_data": {}}]},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Workflow"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_execute_workflow_endpoint_triggers_celery(client: AsyncClient, db_session: AsyncSession):
    """POST /api/v1/workflows/{id}/execute dispatches the Celery task and returns 202."""
    email = "workflow_exec@example.com"
    password = "securepassword123"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": password, "full_name": "WF Exec"})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Create workflow first
    create_res = await client.post(
        "/api/v1/workflows/",
        json={"name": "Exec Workflow", "steps": []},
        headers=headers,
    )
    wf_id = create_res.json()["id"]

    # Mock the Celery task dispatch
    mock_task = MagicMock()
    mock_task.id = "mock-task-id-123"

    with patch("app.workers.workflow_tasks.execute_workflow_task.delay", return_value=mock_task):
        response = await client.post(f"/api/v1/workflows/{wf_id}/execute", headers=headers)

    assert response.status_code == 202
    assert response.json()["task_id"] == "mock-task-id-123"
    assert response.json()["status"] == "queued"
