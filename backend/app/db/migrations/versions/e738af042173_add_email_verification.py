"""add_email_verification

Revision ID: e738af042173
Revises: e738af042172
Create Date: 2026-05-25 01:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e738af042173'
down_revision: Union[str, None] = 'e738af042172'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('users', 'tier')
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'is_verified')
    op.add_column('users', sa.Column('tier', sa.String(length=50), server_default='free', nullable=False))
