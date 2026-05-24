from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.workflow_repo import workflow_repository, workflow_step_repository
from app.models.workflow import Workflow


class WorkflowService:
    async def create_workflow(
        self,
        db: AsyncSession,
        user_id: Any,
        name: str,
        steps: list[dict],
    ) -> Workflow:
        wf = await workflow_repository.create(db, obj_in={
            "user_id": user_id,
            "name": name,
            "status": "pending",
            "definition": {"steps": steps},
            "execution_log": {},
        })
        await db.flush()

        for i, step_def in enumerate(steps):
            await workflow_step_repository.create(db, obj_in={
                "workflow_id": wf.id,
                "step_order": i,
                "agent_type": step_def.get("agent_type", "general"),
                "status": "pending",
                "input_data": step_def.get("input_data", {}),
                "output_data": {},
            })

        await db.commit()
        return wf

    async def execute(self, workflow_id: Any) -> str:
        from app.workers.workflow_tasks import execute_workflow_task
        task = execute_workflow_task.delay(str(workflow_id))
        return task.id

    async def get_workflow(self, db: AsyncSession, workflow_id: Any) -> Workflow | None:
        return await workflow_repository.get_with_steps(db, id=workflow_id)


workflow_service = WorkflowService()
