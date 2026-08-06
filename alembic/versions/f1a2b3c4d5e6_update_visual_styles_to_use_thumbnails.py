"""update visual styles to use thumbnails

Revision ID: f1a2b3c4d5e6
Revises: 00580e5e675a
Create Date: 2026-08-06 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '00580e5e675a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """更新预设视觉风格的图片路径为缩略图版本"""
    connection = op.get_bind()

    # 定义需要更新的路径映射（旧路径 -> 新路径）
    path_updates = [
        ("resources/styles/felt.png", "resources/styles/felt_thumb.png"),
        ("resources/styles/3d_cartoon.png", "resources/styles/3d_cartoon_thumb.png"),
        ("resources/styles/pixel_art.png", "resources/styles/pixel_art_thumb.png"),
        ("resources/styles/puppet_animation.png", "resources/styles/puppet_animation_thumb.png"),
        ("resources/styles/claymation.png", "resources/styles/claymation_thumb.png"),
        ("resources/styles/black_and_white_animation.png", "resources/styles/black_and_white_animation_thumb.png"),
        ("resources/styles/watercolor_illustration.png", "resources/styles/watercolor_illustration_thumb.png"),
        ("resources/styles/japanese_animation.png", "resources/styles/japanese_animation_thumb.png"),
        ("resources/styles/cyberpunk.png", "resources/styles/cyberpunk_thumb.png"),
        ("resources/styles/paper_cut.png", "resources/styles/paper_cut_thumb.png"),
        ("resources/styles/oil_painting.png", "resources/styles/oil_painting_thumb.png"),
        ("resources/styles/low_poly.png", "resources/styles/low_poly_thumb.png"),
        ("resources/styles/cinematic.png", "resources/styles/cinematic_thumb.png"),
        ("resources/styles/realistic.png", "resources/styles/realistic_thumb.png"),
    ]

    # 批量更新路径
    for old_path, new_path in path_updates:
        connection.execute(
            text(
                "UPDATE visual_styles SET sample_image_path = :new_path "
                "WHERE sample_image_path = :old_path"
            ),
            {"old_path": old_path, "new_path": new_path}
        )


def downgrade() -> None:
    """回退到原始图片路径"""
    connection = op.get_bind()

    # 定义需要回退的路径映射（新路径 -> 旧路径）
    path_updates = [
        ("resources/styles/felt_thumb.png", "resources/styles/felt.png"),
        ("resources/styles/3d_cartoon_thumb.png", "resources/styles/3d_cartoon.png"),
        ("resources/styles/pixel_art_thumb.png", "resources/styles/pixel_art.png"),
        ("resources/styles/puppet_animation_thumb.png", "resources/styles/puppet_animation.png"),
        ("resources/styles/claymation_thumb.png", "resources/styles/claymation.png"),
        ("resources/styles/black_and_white_animation_thumb.png", "resources/styles/black_and_white_animation.png"),
        ("resources/styles/watercolor_illustration_thumb.png", "resources/styles/watercolor_illustration.png"),
        ("resources/styles/japanese_animation_thumb.png", "resources/styles/japanese_animation.png"),
        ("resources/styles/cyberpunk_thumb.png", "resources/styles/cyberpunk.png"),
        ("resources/styles/paper_cut_thumb.png", "resources/styles/paper_cut.png"),
        ("resources/styles/oil_painting_thumb.png", "resources/styles/oil_painting.png"),
        ("resources/styles/low_poly_thumb.png", "resources/styles/low_poly.png"),
        ("resources/styles/cinematic_thumb.png", "resources/styles/cinematic.png"),
        ("resources/styles/realistic_thumb.png", "resources/styles/realistic.png"),
    ]

    # 批量回退路径
    for new_path, old_path in path_updates:
        connection.execute(
            text(
                "UPDATE visual_styles SET sample_image_path = :old_path "
                "WHERE sample_image_path = :new_path"
            ),
            {"old_path": old_path, "new_path": new_path}
        )
