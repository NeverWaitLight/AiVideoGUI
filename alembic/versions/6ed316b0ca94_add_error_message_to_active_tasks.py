"""add error_message to active_tasks

Revision ID: 6ed316b0ca94
Revises: b2bd28c1ce35
Create Date: 2026-07-24 09:47:10.211272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ed316b0ca94'
down_revision: Union[str, Sequence[str], None] = 'b2bd28c1ce35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'active_tasks' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('active_tasks')]
        if 'error_message' not in columns:
            op.add_column('active_tasks', sa.Column('error_message', sa.Text(), nullable=False, server_default=''))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'active_tasks' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('active_tasks')]
        if 'error_message' in columns:
            op.drop_column('active_tasks', 'error_message')
