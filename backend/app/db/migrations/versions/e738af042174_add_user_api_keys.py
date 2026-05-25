"""add_user_api_keys

Revision ID: e738af042174
Revises: e738af042173
Create Date: 2026-05-25 19:51:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e738af042174'
down_revision: Union[str, None] = 'e738af042173'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('openai_api_key', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('groq_api_key', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('preferred_provider', sa.String(length=50), server_default='groq', nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'preferred_provider')
    op.drop_column('users', 'groq_api_key')
    op.drop_column('users', 'openai_api_key')
