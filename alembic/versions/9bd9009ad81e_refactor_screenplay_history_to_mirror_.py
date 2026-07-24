"""refactor_screenplay_history_to_mirror_screenplay_fields

Revision ID: 9bd9009ad81e
Revises: 6ed316b0ca94
Create Date: 2026-07-24 16:15:03.424210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9bd9009ad81e'
down_revision: Union[str, Sequence[str], None] = '6ed316b0ca94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "screenplay_history" in inspector.get_table_names():
        op.drop_table("screenplay_history")

    op.create_table(
        "screenplay_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("screenplay_id", sa.Integer(), sa.ForeignKey("screenplay.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("scene_number", sa.Integer(), nullable=False),
        sa.Column("location_type", sa.String(50), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("time_type", sa.String(50), nullable=False),
        sa.Column("time_detail", sa.String(100), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_screenplay_history_screenplay", "screenplay_history", ["screenplay_id", "created_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_screenplay_history_screenplay", table_name="screenplay_history")
    op.drop_table("screenplay_history")

    op.create_table(
        "screenplay_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenes_snapshot", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_screenplay_history_project", "screenplay_history", ["project_id", "created_at"])
