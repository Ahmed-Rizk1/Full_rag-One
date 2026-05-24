import uuid
from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from app.models.base import Base, TimestampMixin, UUIDMixin


class Workflow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflows"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    definition: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    execution_log: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    steps: Mapped[list["WorkflowStep"]] = relationship(
        "WorkflowStep", back_populates="workflow", cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order"
    )


class WorkflowStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_steps"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="steps")
