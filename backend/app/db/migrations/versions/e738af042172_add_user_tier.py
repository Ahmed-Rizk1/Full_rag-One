"""add_user_tier

Revision ID: e738af042172
Revises: f2e4ef042172
Create Date: 2026-05-24 23:25:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e738af042172'
down_revision: Union[str, None] = 'f2e4ef042172'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('tier', sa.String(length=50), server_default='free', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'tier')
