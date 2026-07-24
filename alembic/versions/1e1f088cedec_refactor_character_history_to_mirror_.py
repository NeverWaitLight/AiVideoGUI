"""refactor character_history to mirror characters table fields

Revision ID: 1e1f088cedec
Revises: 9bd9009ad81e
Create Date: 2026-07-24 17:30:30.919837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e1f088cedec'
down_revision: Union[str, Sequence[str], None] = '9bd9009ad81e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='character_history'"))
    if result.scalar():
        op.drop_table('character_history')

    op.create_table('character_history',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('character_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('ref_code', sa.String(length=100), nullable=False),
    sa.Column('design_image', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('created_at', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['character_id'], ['characters.uuid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_history_character', 'character_history', ['character_id', 'created_at'], unique=False)
    op.create_index('idx_character_history_project', 'character_history', ['project_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_character_history_project', table_name='character_history')
    op.drop_index('idx_history_character', table_name='character_history')
    op.drop_table('character_history')

    op.create_table('character_history',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('character_id', sa.String(length=36), nullable=False),
    sa.Column('snapshot', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['character_id'], ['characters.uuid'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_history_character', 'character_history', ['character_id', 'created_at'], unique=False)
