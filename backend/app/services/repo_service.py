import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class RepoService:
    """Service for repository intelligence: clone, parse diffs, and audit code."""

    async def create_analysis(
        self, db: AsyncSession, *, user_id: uuid.UUID, repo_url: str, branch: str = "main"
    ) -> dict[str, Any]:
        """Create a repo analysis record and return its ID."""
        from app.repositories.workflow_repo import workflow_repository

        wf = await workflow_repository.create(db, obj_in={
            "user_id": user_id,
            "name": f"repo_analysis:{repo_url}",
            "status": "pending",
            "definition": {"repo_url": repo_url, "branch": branch, "type": "repo_analysis"},
            "execution_log": {},
        })
        await db.commit()
        logger.info("Repo analysis created", analysis_id=str(wf.id), repo_url=repo_url)
        return {"id": str(wf.id), "status": "pending"}

    def parse_diff(self, diff_text: str) -> list[dict[str, Any]]:
        """Parse a unified diff string into structured file-level change summaries."""
        files: list[dict[str, Any]] = []
        current_file: dict[str, Any] | None = None

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                if current_file:
                    files.append(current_file)
                parts = line.split(" b/")
                filename = parts[-1] if len(parts) > 1 else "unknown"
                current_file = {"filename": filename, "additions": 0, "deletions": 0}
            elif current_file:
                if line.startswith("+") and not line.startswith("+++"):
                    current_file["additions"] += 1
                elif line.startswith("-") and not line.startswith("---"):
                    current_file["deletions"] += 1

        if current_file:
            files.append(current_file)

        return files

    def build_file_tree(self, file_paths: list[str]) -> dict:
        """Build a nested dict file tree from a flat list of paths."""
        tree: dict = {}
        for path in file_paths:
            parts = path.strip("/").split("/")
            node = tree
            for part in parts:
                node = node.setdefault(part, {})
        return tree


repo_service = RepoService()
