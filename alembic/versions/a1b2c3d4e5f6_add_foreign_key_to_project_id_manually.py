"""add foreign key to project_id manually

Revision ID: a1b2c3d4e5f6
Revises: f28dbf5d457b
Create Date: 2026-08-12 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f28dbf5d457b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Recreate generate_tasks table with foreign key constraint."""
    with op.batch_alter_table('generate_tasks', schema=None, recreate='always') as batch_op:
        batch_op.create_foreign_key(
            'fk_generate_tasks_project_id',
            'projects',
            ['project_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    """Remove foreign key constraint."""
    with op.batch_alter_table('generate_tasks', schema=None, recreate='always') as batch_op:
        batch_op.drop_constraint('fk_generate_tasks_project_id', type_='foreignkey')
