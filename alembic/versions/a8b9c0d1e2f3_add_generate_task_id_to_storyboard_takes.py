"""add_generate_task_id_to_storyboard_takes

Revision ID: a8b9c0d1e2f3
Revises: c3297f920733
Create Date: 2026-08-15 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, Sequence[str], None] = "c3297f920733"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("storyboard_takes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("generate_task_id", sa.Integer(), nullable=True))
        batch_op.alter_column(
            "media_file_id",
            existing_type=sa.String(length=36),
            nullable=True,
            server_default="",
        )
        batch_op.create_foreign_key(
            "fk_take_generate_task",
            "generate_tasks",
            ["generate_task_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("idx_take_generate_task", ["generate_task_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("storyboard_takes", schema=None) as batch_op:
        batch_op.drop_index("idx_take_generate_task")
        batch_op.drop_constraint("fk_take_generate_task", type_="foreignkey")
        batch_op.alter_column(
            "media_file_id",
            existing_type=sa.String(length=36),
            nullable=False,
            server_default=None,
        )
        batch_op.drop_column("generate_task_id")
