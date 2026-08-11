"""rename generate_task fields: provider_file_url->remote_url, save_path->local_path

Revision ID: b21bc58ed015
Revises: 77958a0c0f8d
Create Date: 2026-08-11 15:12:24.948622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b21bc58ed015'
down_revision: Union[str, Sequence[str], None] = '77958a0c0f8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加新列（允许为空）
    with op.batch_alter_table('generate_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('remote_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('local_path', sa.String(length=500), nullable=True))

    # 数据迁移：复制旧列到新列，同时转换 local_path 为相对路径
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE generate_tasks
        SET remote_url = provider_file_url,
            local_path = CASE
                WHEN save_path LIKE '%\\ai-video-gui\\%' THEN
                    SUBSTR(save_path, INSTR(save_path, '\\ai-video-gui\\') + 14)
                ELSE
                    save_path
            END
    """))

    # 设置新列为 NOT NULL
    with op.batch_alter_table('generate_tasks', schema=None) as batch_op:
        batch_op.alter_column('remote_url', nullable=False, server_default='')
        batch_op.alter_column('local_path', nullable=False, server_default='')
        batch_op.drop_column('save_path')
        batch_op.drop_column('provider_file_url')


def downgrade() -> None:
    """Downgrade schema."""
    # 添加旧列
    with op.batch_alter_table('generate_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('provider_file_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('save_path', sa.String(length=500), nullable=True))

    # 数据迁移：复制新列到旧列
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE generate_tasks
        SET provider_file_url = remote_url,
            save_path = local_path
    """))

    # 设置旧列为 NOT NULL
    with op.batch_alter_table('generate_tasks', schema=None) as batch_op:
        batch_op.alter_column('provider_file_url', nullable=False, server_default='')
        batch_op.alter_column('save_path', nullable=False, server_default='')
        batch_op.drop_column('local_path')
        batch_op.drop_column('remote_url')
