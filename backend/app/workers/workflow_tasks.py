import asyncio
import uuid

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="execute_workflow_task", bind=True, max_retries=3)
def execute_workflow_task(self, workflow_id: str) -> dict:
    """Execute a workflow by iterating through its steps sequentially (stub)."""
    return asyncio.run(_run_workflow(workflow_id))


async def _run_workflow(workflow_id: str) -> dict:
    from app.db.session import SessionLocal
    from app.repositories.workflow_repo import workflow_repository, workflow_step_repository

    async with SessionLocal() as db:
        wf = await workflow_repository.get_with_steps(db, id=uuid.UUID(workflow_id))
        if not wf:
            logger.error("Workflow not found", workflow_id=workflow_id)
            return {"status": "error", "detail": "Workflow not found"}

        await workflow_repository.update(db, db_obj=wf, obj_in={"status": "running"})
        await db.commit()

        for step in wf.steps:
            try:
                # Stub: mark each step completed immediately
                await workflow_step_repository.update(
                    db, db_obj=step,
                    obj_in={"status": "completed", "output_data": {"result": "stub_output"}}
                )
                await db.commit()
                logger.info("Step completed", step_id=str(step.id), order=step.step_order)
            except Exception as exc:
                await workflow_step_repository.update(
                    db, db_obj=step, obj_in={"status": "failed"}
                )
                await workflow_repository.update(
                    db, db_obj=wf, obj_in={"status": "failed", "execution_log": {"error": str(exc)}}
                )
                await db.commit()
                logger.error("Step failed", step_id=str(step.id), error=str(exc))
                return {"status": "failed"}

        await workflow_repository.update(db, db_obj=wf, obj_in={"status": "completed"})
        await db.commit()
        return {"status": "completed", "workflow_id": workflow_id}
