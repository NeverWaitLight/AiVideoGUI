"""rename_visual_content_to_content

Revision ID: 538fc50dfbdb
Revises: 4cb96b3e6a4c
Create Date: 2026-08-06 13:59:12.585491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '538fc50dfbdb'
down_revision: Union[str, Sequence[str], None] = '4cb96b3e6a4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite 不支持 RENAME COLUMN，需要手动迁移数据

    # 1. 为 storyboard 表添加新列
    op.add_column('storyboard', sa.Column('content', sa.Text(), nullable=False, server_default=''))

    # 2. 复制数据从 visual_content 到 content
    op.execute('UPDATE storyboard SET content = visual_content')

    # 3. 删除旧列
    op.drop_column('storyboard', 'visual_content')

    # 4. 为 storyboard_history 表添加新列
    op.add_column('storyboard_history', sa.Column('content', sa.Text(), nullable=False, server_default=''))

    # 5. 复制数据从 visual_content 到 content
    op.execute('UPDATE storyboard_history SET content = visual_content')

    # 6. 删除旧列
    op.drop_column('storyboard_history', 'visual_content')


def downgrade() -> None:
    """Downgrade schema."""
    # 回滚操作：content -> visual_content

    # 1. 为 storyboard 表添加旧列
    op.add_column('storyboard', sa.Column('visual_content', sa.TEXT(), nullable=False, server_default=''))

    # 2. 复制数据从 content 到 visual_content
    op.execute('UPDATE storyboard SET visual_content = content')

    # 3. 删除新列
    op.drop_column('storyboard', 'content')

    # 4. 为 storyboard_history 表添加旧列
    op.add_column('storyboard_history', sa.Column('visual_content', sa.TEXT(), nullable=False, server_default=''))

    # 5. 复制数据从 content 到 visual_content
    op.execute('UPDATE storyboard_history SET visual_content = content')

    # 6. 删除新列
    op.drop_column('storyboard_history', 'content')
