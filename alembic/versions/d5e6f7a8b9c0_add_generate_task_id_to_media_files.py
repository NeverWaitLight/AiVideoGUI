"""add generate_task_id to media_files

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-08-21 15:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("media_files", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("generate_task_id", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.create_index("idx_media_generate_task", ["generate_task_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("media_files", schema=None) as batch_op:
        batch_op.drop_index("idx_media_generate_task")
        batch_op.drop_column("generate_task_id")
