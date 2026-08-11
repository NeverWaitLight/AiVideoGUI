"""add task_type to generate_tasks

Revision ID: 77958a0c0f8d
Revises: 24332896a659
Create Date: 2026-08-11 14:32:26.449913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77958a0c0f8d'
down_revision: Union[str, Sequence[str], None] = '24332896a659'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加新字段
    with op.batch_alter_table('generate_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('task_type', sa.String(length=20), nullable=False, server_default='video'))
        batch_op.add_column(sa.Column('character_uuid', sa.String(length=36), nullable=False, server_default=''))
        batch_op.create_index('idx_generate_task_type', ['task_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('generate_tasks', schema=None) as batch_op:
        batch_op.drop_column('character_uuid')
        batch_op.drop_column('task_type')
