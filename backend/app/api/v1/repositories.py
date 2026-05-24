import uuid
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.services.repo_service import repo_service

router = APIRouter(prefix="/repositories", tags=["repositories"])


class RepoAnalyzeRequest(BaseModel):
    repo_url: str
    branch: str = "main"


class RepoAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str


@router.post("/analyze", response_model=RepoAnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_repository(
    payload: RepoAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await repo_service.create_analysis(
        db, user_id=current_user.id, repo_url=payload.repo_url, branch=payload.branch
    )

    from app.workers.repo_tasks import analyze_repository_task
    analyze_repository_task.delay(result["id"])

    return result


@router.get("/{id}", status_code=status.HTTP_200_OK)
async def get_analysis(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.repositories.workflow_repo import workflow_repository

    wf = await workflow_repository.get(db, id=id)
    if not wf or wf.user_id != current_user.id:
        raise NotFoundError("Analysis not found.")

    return {
        "id": str(wf.id),
        "name": wf.name,
        "status": wf.status,
        "summary": wf.execution_log,
        "created_at": str(wf.created_at),
    }
