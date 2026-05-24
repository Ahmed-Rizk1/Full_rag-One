import uuid
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.services.workflow_service import workflow_service

router = APIRouter(prefix="/workflows", tags=["workflows"])


from app.repositories.workflow_repo import workflow_repository, workflow_step_repository


class WorkflowCreate(BaseModel):
    name: str
    steps: list[dict] = []


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str


@router.get("", response_model=list[WorkflowResponse], status_code=status.HTTP_200_OK)
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await workflow_repository.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await workflow_service.create_workflow(
        db, user_id=current_user.id, name=payload.name, steps=payload.steps
    )


@router.post("/{id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wf = await workflow_service.get_workflow(db, workflow_id=id)
    if not wf or wf.user_id != current_user.id:
        raise NotFoundError("Workflow not found.")
    task_id = await workflow_service.execute(id)
    return {"task_id": task_id, "workflow_id": str(id), "status": "queued"}


@router.get("/{id}", response_model=WorkflowResponse, status_code=status.HTTP_200_OK)
async def get_workflow(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wf = await workflow_service.get_workflow(db, workflow_id=id)
    if not wf or wf.user_id != current_user.id:
        raise NotFoundError("Workflow not found.")
    return wf
