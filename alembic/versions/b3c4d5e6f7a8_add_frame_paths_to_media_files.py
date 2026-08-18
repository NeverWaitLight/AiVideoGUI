"""add frame paths to media_files

Revision ID: b3c4d5e6f7a8
Revises: a8b9c0d1e2f3
Create Date: 2026-08-18 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "a8b9c0d1e2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "media_files",
        sa.Column("first_frame_path", sa.String(500), nullable=False, server_default=""),
    )
    op.add_column(
        "media_files",
        sa.Column("last_frame_path", sa.String(500), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("media_files", "last_frame_path")
    op.drop_column("media_files", "first_frame_path")
