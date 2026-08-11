"""remove_unused_visual_styles

Revision ID: 24332896a659
Revises: da5ede4ea6a3
Create Date: 2026-08-11 13:51:17.347526

"""
from typing import Sequence, Union
import os
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '24332896a659'
down_revision: Union[str, Sequence[str], None] = 'da5ede4ea6a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """删除不需要的视觉风格数据和对应的图片文件"""
    connection = op.get_bind()

    # 保留的风格名称
    kept_styles = [
        "毛毡风格",
        "3D卡通",
        "像素风格",
        "木偶动画",
        "黏土风格",  # 数据库中存储的是"黏土"
        "黑白动画",
    ]

    # 要删除的风格及其对应的文件
    removed_styles = [
        ("水彩插画", "watercolor_illustration"),
        ("日本动画", "japanese_animation"),
        ("赛博朋克", "cyberpunk"),
        ("剪纸风格", "paper_cut"),
        ("油画风格", "oil_painting"),
        ("低多边形", "low_poly"),
        ("电影风格", "cinematic"),
        ("写实风格", "realistic"),
    ]

    # 删除数据库记录
    for style_name, _ in removed_styles:
        connection.execute(
            text("DELETE FROM visual_styles WHERE name = :name"),
            {"name": style_name}
        )

    # 删除对应的图片文件
    project_root = Path(__file__).parent.parent.parent
    resources_styles_dir = project_root / "resources" / "styles"

    # 获取工作目录中的资源文件路径
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if localappdata:
        workspace_styles_dir = Path(localappdata) / "ai-video-gui" / "resources" / "styles"
    else:
        workspace_styles_dir = None

    for _, file_prefix in removed_styles:
        # 删除项目目录中的文件
        for file_path in resources_styles_dir.glob(f"{file_prefix}*"):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    print(f"已删除项目文件: {file_path}")
                except Exception as e:
                    print(f"删除项目文件失败 {file_path}: {e}")

        # 删除工作目录中的文件（如果存在）
        if workspace_styles_dir and workspace_styles_dir.exists():
            for file_path in workspace_styles_dir.glob(f"{file_prefix}*"):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        print(f"已删除工作目录文件: {file_path}")
                    except Exception as e:
                        print(f"删除工作目录文件失败 {file_path}: {e}")


def downgrade() -> None:
    """恢复被删除的视觉风格数据（注意：无法恢复已删除的图片文件）"""
    connection = op.get_bind()

    # 重新插入被删除的风格数据
    removed_styles = [
        ("水彩插画", "resources/styles/watercolor_illustration.png"),
        ("日本动画", "resources/styles/japanese_animation.png"),
        ("赛博朋克", "resources/styles/cyberpunk.png"),
        ("剪纸风格", "resources/styles/paper_cut.png"),
        ("油画风格", "resources/styles/oil_painting.png"),
        ("低多边形", "resources/styles/low_poly.png"),
        ("电影风格", "resources/styles/cinematic.png"),
        ("写实风格", "resources/styles/realistic.png"),
    ]

    for name, image_path in removed_styles:
        # 检查记录是否已存在（避免重复插入）
        result = connection.execute(
            text("SELECT COUNT(*) FROM visual_styles WHERE name = :name"),
            {"name": name}
        ).scalar()

        if result == 0:
            connection.execute(
                text(
                    "INSERT INTO visual_styles (name, is_default, sample_image_path, created_at, updated_at) "
                    "VALUES (:name, 1, :image_path, strftime('%s', 'now') * 1000, strftime('%s', 'now') * 1000)"
                ),
                {"name": name, "image_path": image_path}
            )
