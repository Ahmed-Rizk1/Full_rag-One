from typing import Any, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workflow import Workflow, WorkflowStep
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    async def get_with_steps(self, db: AsyncSession, *, id: Any) -> Workflow | None:
        result = await db.execute(
            select(Workflow)
            .options(selectinload(Workflow.steps))
            .where(Workflow.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self, db: AsyncSession, *, user_id: Any, skip: int = 0, limit: int = 100
    ) -> Sequence[Workflow]:
        result = await db.execute(
            select(Workflow)
            .where(Workflow.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class WorkflowStepRepository(BaseRepository[WorkflowStep]):
    async def get_by_workflow(
        self, db: AsyncSession, *, workflow_id: Any
    ) -> Sequence[WorkflowStep]:
        result = await db.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == workflow_id)
            .order_by(WorkflowStep.step_order)
        )
        return result.scalars().all()


workflow_repository = WorkflowRepository(Workflow)
workflow_step_repository = WorkflowStepRepository(WorkflowStep)
