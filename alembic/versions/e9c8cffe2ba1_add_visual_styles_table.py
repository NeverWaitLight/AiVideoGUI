"""add_visual_styles_table

Revision ID: e9c8cffe2ba1
Revises: 
Create Date: 2026-08-05 15:56:59.116732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9c8cffe2ba1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 visual_styles 表并插入预设数据"""
    # 创建表
    op.create_table(
        'visual_styles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('sample_image_path', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 创建索引
    op.create_index('idx_visual_styles_created_at', 'visual_styles', ['created_at'])
    op.create_index('idx_visual_styles_name', 'visual_styles', ['name'])

    # 插入预设风格数据
    from sqlalchemy import text
    connection = op.get_bind()

    preset_styles = [
        ("毛毡风格", 1, "resources/styles/felt.png"),
        ("3D卡通", 1, "resources/styles/3d_cartoon.png"),
        ("像素风格", 1, "resources/styles/pixel_art.png"),
        ("木偶动画", 1, "resources/styles/puppet_animation.png"),
        ("黏土风格", 1, "resources/styles/claymation.png"),
        ("黑白动画", 1, "resources/styles/black_and_white_animation.png"),
        ("水彩插画", 1, "resources/styles/watercolor_illustration.png"),
        ("日本动画", 1, "resources/styles/japanese_animation.png"),
        ("赛博朋克", 1, "resources/styles/cyberpunk.png"),
        ("剪纸风格", 1, "resources/styles/paper_cut.png"),
        ("油画风格", 1, "resources/styles/oil_painting.png"),
        ("低多边形", 1, "resources/styles/low_poly.png"),
        ("电影风格", 1, "resources/styles/cinematic.png"),
        ("写实风格", 1, "resources/styles/realistic.png"),
    ]

    for name, is_default, image_path in preset_styles:
        connection.execute(
            text(
                "INSERT INTO visual_styles (name, is_default, sample_image_path, created_at, updated_at) "
                "VALUES (:name, :is_default, :image_path, strftime('%s', 'now') * 1000, strftime('%s', 'now') * 1000)"
            ),
            {"name": name, "is_default": is_default, "image_path": image_path}
        )


def downgrade() -> None:
    """删除 visual_styles 表"""
    op.drop_index('idx_visual_styles_name', table_name='visual_styles')
    op.drop_index('idx_visual_styles_created_at', table_name='visual_styles')
    op.drop_table('visual_styles')
