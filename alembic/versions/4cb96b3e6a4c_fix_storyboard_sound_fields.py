"""fix storyboard sound fields

Revision ID: 4cb96b3e6a4c
Revises: f1a2b3c4d5e6
Create Date: 2026-08-06 11:35:03.164636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cb96b3e6a4c'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite 不支持 ALTER COLUMN，需要使用批量模式重建表
    with op.batch_alter_table('storyboard', schema=None) as batch_op:
        batch_op.alter_column('sound_effect',
                   existing_type=sa.VARCHAR(length=255),
                   type_=sa.Text(),
                   existing_nullable=False)
        batch_op.drop_column('dialogue')

    with op.batch_alter_table('storyboard_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ambient_sound', sa.Text(), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('background_music', sa.Text(), nullable=False, server_default=''))
        batch_op.alter_column('sound_effect',
                   existing_type=sa.VARCHAR(length=255),
                   type_=sa.Text(),
                   existing_nullable=False)
        batch_op.drop_column('dialogue')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('storyboard_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dialogue', sa.TEXT(), nullable=False, server_default=''))
        batch_op.alter_column('sound_effect',
                   existing_type=sa.Text(),
                   type_=sa.VARCHAR(length=255),
                   existing_nullable=False)
        batch_op.drop_column('background_music')
        batch_op.drop_column('ambient_sound')

    with op.batch_alter_table('storyboard', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dialogue', sa.TEXT(), nullable=False, server_default=''))
        batch_op.alter_column('sound_effect',
                   existing_type=sa.Text(),
                   type_=sa.VARCHAR(length=255),
                   existing_nullable=False)
